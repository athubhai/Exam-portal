from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone

from database import get_db
from models import Exam, Question, User, UserRole, ExamStatus
from schemas import (
    ExamCreate, ExamUpdate, ExamOut, QuestionCreate, QuestionOut, QuestionStudentOut
)
from auth import get_current_user, require_role
from crypto import encrypt_text, decrypt_text
from utils import log_audit_action

router = APIRouter(prefix="/exams", tags=["Exam & Question Management"])


@router.get("", response_model=List[ExamOut])
def list_exams(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List exams with pagination (#12) and eager loading (#13):
    - Students see only PUBLISHED exams.
    - Faculty see exams created by them.
    - Admin sees all exams.
    """
    base_query = db.query(Exam).options(
        joinedload(Exam.questions),
        joinedload(Exam.creator)
    )

    if current_user.role == UserRole.STUDENT:
        exams = base_query.filter(Exam.status == ExamStatus.PUBLISHED).order_by(Exam.start_time.desc()).offset(skip).limit(limit).all()
    elif current_user.role == UserRole.FACULTY:
        exams = base_query.filter(Exam.created_by == current_user.id).order_by(Exam.start_time.desc()).offset(skip).limit(limit).all()
    else:  # Admin
        exams = base_query.order_by(Exam.start_time.desc()).offset(skip).limit(limit).all()

    # Deduplicate results from joinedload (SQLAlchemy may return duplicates)
    seen_ids = set()
    unique_exams = []
    for ex in exams:
        if ex.id not in seen_ids:
            seen_ids.add(ex.id)
            unique_exams.append(ex)

    result = []
    for ex in unique_exams:
        q_count = len(ex.questions)
        t_marks = sum(q.marks for q in ex.questions)
        creator_name = ex.creator.name if ex.creator else "Unknown"
        result.append(ExamOut(
            id=ex.id,
            title=ex.title,
            created_by=ex.created_by,
            creator_name=creator_name,
            start_time=ex.start_time,
            end_time=ex.end_time,
            duration_minutes=ex.duration_minutes,
            status=ex.status,
            total_questions=q_count,
            total_marks=t_marks
        ))
    return result

@router.post("", response_model=ExamOut, status_code=status.HTTP_201_CREATED)
def create_exam(
    exam_in: ExamCreate,
    request: Request,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.FACULTY)),
    db: Session = Depends(get_db)
):
    if exam_in.end_time <= exam_in.start_time:
        raise HTTPException(status_code=400, detail="Exam end time must be after start time.")

    exam = Exam(
        title=exam_in.title,
        created_by=current_user.id,
        start_time=exam_in.start_time,
        end_time=exam_in.end_time,
        duration_minutes=exam_in.duration_minutes,
        status=ExamStatus.DRAFT
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)

    log_audit_action(db, current_user.id, "EXAM_CREATED", f"Exam #{exam.id} '{exam.title}' created", request=request)

    return ExamOut(
        id=exam.id,
        title=exam.title,
        created_by=exam.created_by,
        creator_name=current_user.name,
        start_time=exam.start_time,
        end_time=exam.end_time,
        duration_minutes=exam.duration_minutes,
        status=exam.status,
        total_questions=0,
        total_marks=0
    )

@router.get("/{exam_id}", response_model=ExamOut)
def get_exam(exam_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found.")

    if current_user.role == UserRole.STUDENT and exam.status != ExamStatus.PUBLISHED:
        raise HTTPException(status_code=403, detail="Exam is not published.")

    return ExamOut(
        id=exam.id,
        title=exam.title,
        created_by=exam.created_by,
        creator_name=exam.creator.name if exam.creator else "Unknown",
        start_time=exam.start_time,
        end_time=exam.end_time,
        duration_minutes=exam.duration_minutes,
        status=exam.status,
        total_questions=len(exam.questions),
        total_marks=sum(q.marks for q in exam.questions)
    )

@router.put("/{exam_id}", response_model=ExamOut)
def update_exam(
    exam_id: int,
    exam_in: ExamUpdate,
    request: Request,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.FACULTY)),
    db: Session = Depends(get_db)
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found.")

    if current_user.role == UserRole.FACULTY and exam.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You can only edit your own exams.")

    if exam_in.title is not None:
        exam.title = exam_in.title
    if exam_in.start_time is not None:
        exam.start_time = exam_in.start_time
    if exam_in.end_time is not None:
        exam.end_time = exam_in.end_time
    if exam_in.duration_minutes is not None:
        exam.duration_minutes = exam_in.duration_minutes
    if exam_in.status is not None:
        exam.status = exam_in.status

    db.commit()
    db.refresh(exam)

    log_audit_action(db, current_user.id, "EXAM_UPDATED", f"Exam #{exam.id} updated", request=request)

    return ExamOut(
        id=exam.id,
        title=exam.title,
        created_by=exam.created_by,
        creator_name=exam.creator.name if exam.creator else "Unknown",
        start_time=exam.start_time,
        end_time=exam.end_time,
        duration_minutes=exam.duration_minutes,
        status=exam.status,
        total_questions=len(exam.questions),
        total_marks=sum(q.marks for q in exam.questions)
    )

@router.post("/{exam_id}/publish", response_model=ExamOut)
def toggle_publish_exam(
    exam_id: int,
    request: Request,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.FACULTY)),
    db: Session = Depends(get_db)
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found.")

    if current_user.role == UserRole.FACULTY and exam.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You can only publish your own exams.")

    if len(exam.questions) == 0:
        raise HTTPException(status_code=400, detail="Cannot publish an exam with zero questions.")

    exam.status = ExamStatus.PUBLISHED if exam.status == ExamStatus.DRAFT else ExamStatus.DRAFT
    db.commit()
    db.refresh(exam)

    log_audit_action(db, current_user.id, "EXAM_STATUS_CHANGE", f"Exam #{exam.id} status changed to {exam.status.value}", request=request)

    return ExamOut(
        id=exam.id,
        title=exam.title,
        created_by=exam.created_by,
        creator_name=exam.creator.name if exam.creator else "Unknown",
        start_time=exam.start_time,
        end_time=exam.end_time,
        duration_minutes=exam.duration_minutes,
        status=exam.status,
        total_questions=len(exam.questions),
        total_marks=sum(q.marks for q in exam.questions)
    )

@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exam(
    exam_id: int,
    request: Request,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.FACULTY)),
    db: Session = Depends(get_db)
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found.")

    if current_user.role == UserRole.FACULTY and exam.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You can only delete your own exams.")

    db.delete(exam)
    db.commit()
    log_audit_action(db, current_user.id, "EXAM_DELETED", f"Exam #{exam_id} deleted", request=request)
    return None

# ================= QUESTIONS CRUD (WITH AES-256 ENCRYPTION) =================
@router.post("/{exam_id}/questions", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
def add_question(
    exam_id: int,
    q_in: QuestionCreate,
    request: Request,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.FACULTY)),
    db: Session = Depends(get_db)
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found.")

    if current_user.role == UserRole.FACULTY and exam.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You can only edit questions for your own exams.")

    # AES-256 Encryption of question text and correct answer before DB write
    encrypted_question_text = encrypt_text(q_in.question_text)
    encrypted_correct_answer = encrypt_text(q_in.correct_answer)

    question = Question(
        exam_id=exam_id,
        question_text_encrypted=encrypted_question_text,
        options=q_in.options,
        correct_answer_encrypted=encrypted_correct_answer,
        marks=q_in.marks
    )
    db.add(question)
    db.commit()
    db.refresh(question)

    log_audit_action(db, current_user.id, "QUESTION_ADDED", f"Question added to Exam #{exam_id} with Fernet encryption", request=request)

    return QuestionOut(
        id=question.id,
        exam_id=question.exam_id,
        question_text=q_in.question_text,
        options=question.options,
        correct_answer=q_in.correct_answer,
        marks=question.marks
    )

@router.get("/{exam_id}/questions")
def get_exam_questions(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns decrypted questions:
    - Faculty/Admin: receives question_text, options, marks, AND correct_answer.
    - Students: receives question_text, options, marks (NEVER returns correct_answer).
    """
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found.")

    if current_user.role == UserRole.STUDENT:
        if exam.status != ExamStatus.PUBLISHED:
            raise HTTPException(status_code=403, detail="Exam questions not accessible.")

        student_questions = []
        for q in exam.questions:
            decrypted_q_text = decrypt_text(q.question_text_encrypted)
            student_questions.append({
                "id": q.id,
                "exam_id": q.exam_id,
                "question_text": decrypted_q_text,
                "options": q.options,
                "marks": q.marks
            })
        return student_questions

    # Faculty / Admin view with decrypted correct answer
    admin_questions = []
    for q in exam.questions:
        decrypted_q_text = decrypt_text(q.question_text_encrypted)
        decrypted_ans = decrypt_text(q.correct_answer_encrypted)
        admin_questions.append({
            "id": q.id,
            "exam_id": q.exam_id,
            "question_text": decrypted_q_text,
            "options": q.options,
            "correct_answer": decrypted_ans,
            "marks": q.marks
        })
    return admin_questions

@router.delete("/{exam_id}/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    exam_id: int,
    question_id: int,
    request: Request,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.FACULTY)),
    db: Session = Depends(get_db)
):
    question = db.query(Question).filter(Question.id == question_id, Question.exam_id == exam_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found.")

    db.delete(question)
    db.commit()
    log_audit_action(db, current_user.id, "QUESTION_DELETED", f"Question #{question_id} deleted from Exam #{exam_id}", request=request)
    return None
