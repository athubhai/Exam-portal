import sys
import os
import bcrypt
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, Base, engine
from models import User, UserRole, Exam, Question, ExamStatus, AuditLog
from crypto import encrypt_text

def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

def seed_database():
    print("Syncing database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Seed Test Users
        test_users = [
            {
                "name": "System Administrator",
                "email": "admin@examportal.com",
                "password": "AdminPass123!",
                "role": UserRole.ADMIN,
                "mfa_enabled": False
            },
            {
                "name": "Dr. Sarah Jenkins (Examiner)",
                "email": "faculty@examportal.com",
                "password": "FacultyPass123!",
                "role": UserRole.FACULTY,
                "mfa_enabled": False
            },
            {
                "name": "Alex Smith (Candidate)",
                "email": "student@examportal.com",
                "password": "StudentPass123!",
                "role": UserRole.STUDENT,
                "mfa_enabled": False
            }
        ]

        user_map = {}
        for user_data in test_users:
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            if not existing:
                hashed_pw = hash_password(user_data["password"])
                user = User(
                    name=user_data["name"],
                    email=user_data["email"],
                    hashed_password=hashed_pw,
                    role=user_data["role"],
                    mfa_enabled=user_data["mfa_enabled"]
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                user_map[user_data["email"]] = user
                print(f"Seeded User: {user.name} ({user.role.value}) -> {user.email}")
            else:
                user_map[user_data["email"]] = existing
                print(f"User already exists: {existing.email}")

        faculty_user = user_map.get("faculty@examportal.com")
        admin_user = user_map.get("admin@examportal.com")

        # 2. Seed Sample Published Examination
        existing_exam = db.query(Exam).filter(Exam.title.like("%CS801%")).first()
        if not existing_exam and faculty_user:
            exam = Exam(
                title="CS801: Advanced Network & Cyber Security Examination",
                created_by=faculty_user.id,
                start_time=datetime.now(timezone.utc) - timedelta(minutes=5),
                end_time=datetime.now(timezone.utc) + timedelta(days=7),
                duration_minutes=30,
                status=ExamStatus.PUBLISHED
            )
            db.add(exam)
            db.commit()
            db.refresh(exam)
            print(f"Seeded Published Exam: '{exam.title}' (ID: #{exam.id})")

            # 3. Seed Questions with AES-256 Encryption
            questions_data = [
                {
                    "text": "Which cryptographic algorithm is employed for encrypting question papers at rest in this secure exam portal?",
                    "options": ["AES-256 / Fernet", "DES 56-bit", "MD5 Hash", "Plaintext Base64"],
                    "correct": "AES-256 / Fernet",
                    "marks": 2
                },
                {
                    "text": "What is the primary mechanism used to prevent privilege escalation at the API layer in FastAPI?",
                    "options": ["Server-side RBAC dependency injection (require_role)", "Hiding HTML buttons with CSS", "Client-side localStorage checks", "URL query parameter hashing"],
                    "correct": "Server-side RBAC dependency injection (require_role)",
                    "marks": 2
                },
                {
                    "text": "How does the AI proctoring service detect suspicious behaviour during live examination sessions?",
                    "options": ["Analyzing facial landmarks, head pose, eye gaze vectors, and hand movement with a trained classifier", "Audio keyword recording only", "IP address geolocation pinging", "Random screenshots with no ML analysis"],
                    "correct": "Analyzing facial landmarks, head pose, eye gaze vectors, and hand movement with a trained classifier",
                    "marks": 2
                },
                {
                    "text": "Which TOTP standard is utilized for Multi-Factor Authentication (MFA) in the portal?",
                    "options": ["RFC 6238 Time-Based One-Time Password", "Static SMS 4-digit PIN", "Email Magic Link", "HTTP Basic Auth"],
                    "correct": "RFC 6238 Time-Based One-Time Password",
                    "marks": 2
                }
            ]

            for q in questions_data:
                enc_text = encrypt_text(q["text"])
                enc_ans = encrypt_text(q["correct"])
                question = Question(
                    exam_id=exam.id,
                    question_text_encrypted=enc_text,
                    options=q["options"],
                    correct_answer_encrypted=enc_ans,
                    marks=q["marks"]
                )
                db.add(question)
            db.commit()
            print(f"Seeded {len(questions_data)} AES-256 encrypted exam questions.")

        # 4. Seed Initial Audit Logs
        if admin_user:
            initial_logs = [
                ("SYSTEM_INITIALIZED", "Exam Portal Database & Security Engine Initialized"),
                ("RBAC_POLICY_APPLIED", "Role-Based Access Control matrix verified: Admin, Faculty, Student"),
                ("CRYPTO_ENGINE_READY", "AES-256 symmetric cipher initialized for question papers & results")
            ]
            for action, target in initial_logs:
                log = AuditLog(
                    user_id=admin_user.id,
                    action=action,
                    target_resource=target,
                    timestamp=datetime.now(timezone.utc),
                    ip_address="127.0.0.1"
                )
                db.add(log)
            db.commit()

        print("\nDatabase seeding completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
