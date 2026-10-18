from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from database import get_db
from models import Exam, Question, Submission, ProctoringEvent, User, UserRole, ExamStatus, SubmissionStatus
from schemas import (
    SubmissionStartRequest, AutosaveRequest, SubmitExamRequest, SubmissionOut
)
from auth import get_current_user, require_role
from crypto import encrypt_json, decrypt_json, decrypt_text
from utils import log_audit_action, compute_risk_level

router = APIRouter(prefix="/submissions", tags=["Student Exam Submissions & Auto-Grading"])


@router.post("/start")
def start_or_resume_submission(
    body: SubmissionStartRequest,
    request: Request,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db)
):
    exam = db.query(Exam).filter(Exam.id == body.exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found.")
    if exam.status != ExamStatus.PUBLISHED:
        raise HTTPException(status_code=400, detail="This exam is not active or published.")

    # #25: Enforce exam time window — reject if exam has ended
    now = datetime.now(timezone.utc)
    if exam.end_time and now > exam.end_time.replace(tzinfo=timezone.utc if exam.end_time.tzinfo is None else exam.end_time.tzinfo):
        raise HTTPException(status_code=400, detail="This exam's submission window has closed.")

    # Check for existing submission
    submission = db.query(Submission).filter(
        Submission.exam_id == body.exam_id,
        Submission.student_id == current_user.id
    ).first()

    if not submission:
        submission = Submission(
            exam_id=body.exam_id,
            student_id=current_user.id,
            answers_encrypted=encrypt_json({}),
            status=SubmissionStatus.IN_PROGRESS
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
        log_audit_action(db, current_user.id, "EXAM_SESSION_STARTED", f"Student started Exam #{exam.id}", request=request)
    elif submission.status == SubmissionStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail="You have already submitted this examination.")

    # Decrypt draft answers if any
    saved_answers = decrypt_json(submission.answers_encrypted) if submission.answers_encrypted else {}

    # Return questions stripped of correct answers
    questions = []
    for q in exam.questions:
        questions.append({
            "id": q.id,
            "question_text": decrypt_text(q.question_text_encrypted),
            "options": q.options,
            "marks": q.marks
        })

    return {
        "submission_id": submission.id,
        "exam_id": exam.id,
        "exam_title": exam.title,
        "duration_minutes": exam.duration_minutes,
        "status": submission.status.value,
        "saved_answers": saved_answers,
        "questions": questions,
        "total_questions": len(questions),
        "total_marks": sum(q.marks for q in exam.questions)
    }

@router.post("/autosave")
def autosave_answers(
    body: AutosaveRequest,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db)
):
    submission = db.query(Submission).filter(
        Submission.id == body.submission_id,
        Submission.student_id == current_user.id
    ).first()

    if not submission:
        raise HTTPException(status_code=404, detail="Submission session not found.")
    if submission.status != SubmissionStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Cannot autosave on a finalized submission.")

    # Encrypt answers at rest using AES-256
    submission.answers_encrypted = encrypt_json(body.answers)
    db.commit()

    return {"status": "saved", "timestamp": datetime.now(timezone.utc)}

@router.post("/submit", response_model=SubmissionOut)
def submit_exam(
    body: SubmitExamRequest,
    request: Request,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db)
):
    submission = db.query(Submission).filter(
        Submission.id == body.submission_id,
        Submission.student_id == current_user.id
    ).first()

    if not submission:
        raise HTTPException(status_code=404, detail="Submission session not found.")
    if submission.status == SubmissionStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail="Exam has already been submitted.")

    exam = submission.exam

    # #25: Enforce exam time window on final submission
    now = datetime.now(timezone.utc)
    if exam.end_time and now > exam.end_time.replace(tzinfo=timezone.utc if exam.end_time.tzinfo is None else exam.end_time.tzinfo):
        raise HTTPException(status_code=400, detail="Exam submission window has closed. Your draft answers have been saved.")

    submitted_answers = body.answers  # { "q_id": "selected_option" }

    # AES-256 Encrypt final answer payload before persistence
    submission.answers_encrypted = encrypt_json(submitted_answers)
    submission.submitted_at = datetime.now(timezone.utc)
    submission.status = SubmissionStatus.SUBMITTED

    # ================= AUTOMATED GRADING =================
    total_score = 0.0
    for q in exam.questions:
        q_id_str = str(q.id)
        if q_id_str in submitted_answers:
            student_choice = submitted_answers[q_id_str].strip()
            decrypted_correct = decrypt_text(q.correct_answer_encrypted).strip()
            if student_choice.lower() == decrypted_correct.lower():
                total_score += float(q.marks)

    submission.auto_score = total_score
    db.commit()
    db.refresh(submission)

    log_audit_action(db, current_user.id, "EXAM_SUBMITTED", f"Exam #{exam.id} submitted. Auto-grade: {total_score} pts", request=request)

    # Compute Flagged Events and Risk Level using shared utility
    flag_count = len(submission.proctoring_events)
    risk = compute_risk_level(flag_count)

    return SubmissionOut(
        id=submission.id,
        exam_id=submission.exam_id,
        exam_title=exam.title,
        student_id=current_user.id,
        student_name=current_user.name,
        student_email=current_user.email,
        submitted_at=submission.submitted_at,
        auto_score=submission.auto_score,
        total_marks=sum(q.marks for q in exam.questions),
        status=submission.status,
        flagged_events_count=flag_count,
        cheating_risk_level=risk
    )

@router.get("/my", response_model=List[SubmissionOut])
def get_my_submissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db)
):
    submissions = db.query(Submission).filter(Submission.student_id == current_user.id).order_by(Submission.id.desc()).offset(skip).limit(limit).all()
    results = []
    for sub in submissions:
        flag_cnt = len(sub.proctoring_events)
        risk = compute_risk_level(flag_cnt)
        results.append(SubmissionOut(
            id=sub.id,
            exam_id=sub.exam_id,
            exam_title=sub.exam.title if sub.exam else "Unknown",
            student_id=sub.student_id,
            student_name=current_user.name,
            student_email=current_user.email,
            submitted_at=sub.submitted_at,
            auto_score=sub.auto_score,
            total_marks=sum(q.marks for q in sub.exam.questions) if sub.exam else 0,
            status=sub.status,
            flagged_events_count=flag_cnt,
            cheating_risk_level=risk
        ))
    return results

@router.get("/exam/{exam_id}", response_model=List[SubmissionOut])
def get_exam_submissions(
    exam_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.FACULTY)),
    db: Session = Depends(get_db)
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found.")

    if current_user.role == UserRole.FACULTY and exam.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You can only view submissions for your own exams.")

    results = []
    for sub in exam.submissions:
        flag_cnt = len(sub.proctoring_events)
        risk = compute_risk_level(flag_cnt)
        results.append(SubmissionOut(
            id=sub.id,
            exam_id=sub.exam_id,
            exam_title=exam.title,
            student_id=sub.student_id,
            student_name=sub.student.name if sub.student else "Unknown",
            student_email=sub.student.email if sub.student else "Unknown",
            submitted_at=sub.submitted_at,
            auto_score=sub.auto_score,
            total_marks=sum(q.marks for q in exam.questions),
            status=sub.status,
            flagged_events_count=flag_cnt,
            cheating_risk_level=risk
        ))
    return results

@router.get("/{submission_id}")
def get_submission_detail(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found.")

    # Permissions check
    if current_user.role == UserRole.STUDENT and submission.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot view other students' submissions.")
    if current_user.role == UserRole.FACULTY and submission.exam.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot view submissions for other faculty members' exams.")

    # Decrypt submitted answers
    answers = decrypt_json(submission.answers_encrypted) if submission.answers_encrypted else {}

    # Detailed questions breakdown
    questions_data = []
    for q in submission.exam.questions:
        q_id_str = str(q.id)
        student_ans = answers.get(q_id_str, "Not Answered")
        decrypted_q_text = decrypt_text(q.question_text_encrypted)
        decrypted_correct = decrypt_text(q.correct_answer_encrypted)
        is_correct = (student_ans.strip().lower() == decrypted_correct.strip().lower())

        item = {
            "id": q.id,
            "question_text": decrypted_q_text,
            "options": q.options,
            "student_answer": student_ans,
            "is_correct": is_correct,
            "marks_awarded": q.marks if is_correct else 0,
            "max_marks": q.marks
        }
        # Only show correct answer to student if exam is submitted
        if current_user.role != UserRole.STUDENT or submission.status == SubmissionStatus.SUBMITTED:
            item["correct_answer"] = decrypted_correct

        questions_data.append(item)

    # Proctoring logs
    proctoring_events = []
    for ev in submission.proctoring_events:
        proctoring_events.append({
            "id": ev.id,
            "timestamp": ev.timestamp,
            "event_type": ev.event_type,
            "confidence_score": ev.confidence_score,
            "frame_reference": ev.frame_reference
        })

    return {
        "id": submission.id,
        "exam_id": submission.exam_id,
        "exam_title": submission.exam.title,
        "student_name": submission.student.name,
        "student_email": submission.student.email,
        "status": submission.status.value,
        "submitted_at": submission.submitted_at,
        "auto_score": submission.auto_score,
        "total_marks": sum(q.marks for q in submission.exam.questions),
        "questions_breakdown": questions_data,
        "proctoring_events": proctoring_events
    }
