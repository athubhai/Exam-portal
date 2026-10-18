import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app
from database import SessionLocal, Base, engine
from models import User, UserRole, Exam, Question, Submission, ExamStatus
from crypto import encrypt_text, decrypt_text, encrypt_json, decrypt_json
from auth import create_access_token, verify_password
from mfa import generate_mfa_secret, verify_mfa_code
from ai_engine.classifier import proctor_classifier
import pyotp

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()

# ================= 1. CRYPTO & ENCRYPTION TESTS =================
def test_aes256_text_encryption():
    secret_text = "What is the primary function of a symmetric block cipher?"
    ciphertext = encrypt_text(secret_text)
    assert ciphertext != secret_text
    assert len(ciphertext) > len(secret_text)

    decrypted = decrypt_text(ciphertext)
    assert decrypted == secret_text

def test_aes256_json_encryption():
    payload = {"q1": "Option A", "q2": "Option C", "score": 98.5}
    ciphertext = encrypt_json(payload)
    assert isinstance(ciphertext, str)

    decrypted = decrypt_json(ciphertext)
    assert decrypted == payload

# ================= 2. AUTH & RBAC SECURITY TESTS =================
def test_login_and_token_generation():
    response = client.post("/api/auth/login", json={
        "email": "admin@examportal.com",
        "password": "AdminPass123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "Admin"

def test_invalid_login_rejected():
    response = client.post("/api/auth/login", json={
        "email": "admin@examportal.com",
        "password": "WrongPassword123!"
    })
    assert response.status_code == 401

def test_rbac_security_cross_role_access():
    # Login as Student
    student_res = client.post("/api/auth/login", json={
        "email": "student@examportal.com",
        "password": "StudentPass123!"
    })
    student_token = student_res.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # Attempt to access Admin-only endpoint as Student -> MUST BE 403 Forbidden
    admin_probe = client.get("/api/auth/admin-demo", headers=student_headers)
    assert admin_probe.status_code == 403
    assert "Access denied" in admin_probe.json()["detail"]

    # Attempt to access Faculty-only endpoint as Student -> MUST BE 403 Forbidden
    faculty_probe = client.get("/api/auth/faculty-demo", headers=student_headers)
    assert faculty_probe.status_code == 403

# ================= 3. EXAM CRUD & ENCRYPTION TESTS =================
def test_faculty_exam_crud_and_question_encryption():
    # Login as Faculty
    faculty_res = client.post("/api/auth/login", json={
        "email": "faculty@examportal.com",
        "password": "FacultyPass123!"
    })
    faculty_token = faculty_res.json()["access_token"]
    faculty_headers = {"Authorization": f"Bearer {faculty_token}"}

    # 1. Create Exam
    create_res = client.post("/api/exams", headers=faculty_headers, json={
        "title": "Automated Test Examination",
        "start_time": "2026-08-01T10:00:00",
        "end_time": "2026-08-30T10:00:00",
        "duration_minutes": 45
    })
    assert create_res.status_code == 201
    exam_id = create_res.json()["id"]

    # 2. Add Encrypted Question
    q_res = client.post(f"/api/exams/{exam_id}/questions", headers=faculty_headers, json={
        "question_text": "What is the AES block size in bits?",
        "options": ["64 bits", "128 bits", "256 bits", "512 bits"],
        "correct_answer": "128 bits",
        "marks": 5
    })
    assert q_res.status_code == 201

    # Verify directly in Database that raw content is encrypted
    db = SessionLocal()
    db_question = db.query(Question).filter(Question.exam_id == exam_id).first()
    assert db_question.question_text_encrypted != "What is the AES block size in bits?"
    assert db_question.correct_answer_encrypted != "128 bits"
    db.close()

    # 3. Publish Exam
    pub_res = client.post(f"/api/exams/{exam_id}/publish", headers=faculty_headers)
    assert pub_res.status_code == 200
    assert pub_res.json()["status"] == "PUBLISHED"

    # 4. Student View (Questions decrypted, but correct_answer stripped)
    student_res = client.post("/api/auth/login", json={"email": "student@examportal.com", "password": "StudentPass123!"})
    student_headers = {"Authorization": f"Bearer {student_res.json()['access_token']}"}

    student_q_res = client.get(f"/api/exams/{exam_id}/questions", headers=student_headers)
    assert student_q_res.status_code == 200
    student_questions = student_q_res.json()
    assert len(student_questions) == 1
    assert student_questions[0]["question_text"] == "What is the AES block size in bits?"
    assert "correct_answer" not in student_questions[0]  # Security check: never leak correct answer!

# ================= 4. STUDENT EXAM TAKING & AUTO-GRADING =================
def test_student_exam_taking_and_autograde():
    student_res = client.post("/api/auth/login", json={"email": "student@examportal.com", "password": "StudentPass123!"})
    student_token = student_res.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # Start seeded exam #1
    start_res = client.post("/api/submissions/start", headers=student_headers, json={"exam_id": 1})
    assert start_res.status_code in [200, 400]
    if start_res.status_code == 200:
        data = start_res.json()
        sub_id = data["submission_id"]
        questions = data["questions"]

        # Autosave answers
        answers_payload = {}
        for q in questions:
            # Pick first option
            answers_payload[str(q["id"])] = q["options"][0]

        save_res = client.post("/api/submissions/autosave", headers=student_headers, json={
            "submission_id": sub_id,
            "answers": answers_payload
        })
        assert save_res.status_code == 200

        # Submit
        submit_res = client.post("/api/submissions/submit", headers=student_headers, json={
            "submission_id": sub_id,
            "answers": answers_payload
        })
        assert submit_res.status_code == 200
        result = submit_res.json()
        assert result["auto_score"] is not None
        assert result["status"] == "SUBMITTED"

# ================= 5. MFA TOTP SECURITY TESTS =================
def test_totp_mfa_generation_and_validation():
    secret = generate_mfa_secret()
    assert len(secret) == 32
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()

    assert verify_mfa_code(secret, valid_code) is True
    assert verify_mfa_code(secret, "000000") is False

# ================= 6. AI PROCTORING CLASSIFIER EVALUATION =================
def test_ai_proctoring_classifier_metrics():
    metrics = proctor_classifier.metrics
    assert metrics["accuracy"] >= 0.85
    assert metrics["precision"] >= 0.80
    assert metrics["recall"] >= 0.80
    assert metrics["n_samples"] == 5500
    assert metrics["n_features"] == 37
