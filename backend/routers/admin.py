from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from database import get_db
from models import User, Exam, Submission, ProctoringEvent, AuditLog, UserRole
from schemas import (
    UserOut, UserCreateAdmin, UserRoleUpdate, AuditLogOut, SystemStatsOut
)
from auth import require_role, hash_password
from ai_engine.classifier import proctor_classifier
from utils import log_audit_action

router = APIRouter(prefix="/admin", tags=["Admin Portal & System Management"])

@router.get("/users", response_model=List[UserOut])
def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    return db.query(User).order_by(User.id.asc()).offset(skip).limit(limit).all()

@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user_by_admin(
    user_in: UserCreateAdmin,
    request: Request,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    new_user = User(
        name=user_in.name,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        role=user_in.role,
        mfa_enabled=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    ip = request.client.host if request.client else "127.0.0.1"
    log_audit_action(
        db, current_user.id, "ADMIN_CREATE_USER",
        f"Created User #{new_user.id} ({new_user.email}) as {new_user.role.value}",
        ip=ip
    )

    return new_user

@router.put("/users/{user_id}/role", response_model=UserOut)
def update_user_role(
    user_id: int,
    role_in: UserRoleUpdate,
    request: Request,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    old_role = user.role.value
    user.role = role_in.role
    db.commit()
    db.refresh(user)

    ip = request.client.host if request.client else "127.0.0.1"
    log_audit_action(
        db, current_user.id, "ADMIN_ROLE_CHANGE",
        f"Changed User #{user.id} ({user.email}) role from {old_role} to {user.role.value}",
        ip=ip
    )

    return user

@router.get("/audit-logs", response_model=List[AuditLogOut])
def get_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).offset(skip).limit(limit).all()
    results = []
    for log in logs:
        results.append(AuditLogOut(
            id=log.id,
            user_id=log.user_id,
            user_email=log.user.email if log.user else "System/Anonymous",
            action=log.action,
            target_resource=log.target_resource,
            timestamp=log.timestamp,
            ip_address=log.ip_address
        ))
    return results

@router.get("/stats", response_model=SystemStatsOut)
def get_system_stats(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    total_users = db.query(User).count()
    total_exams = db.query(Exam).count()
    total_submissions = db.query(Submission).count()
    total_proctoring_alerts = db.query(ProctoringEvent).count()
    active_exams_count = db.query(Exam).filter(Exam.status == "PUBLISHED").count()
    model_accuracy = proctor_classifier.metrics.get("accuracy", 0.945)

    return SystemStatsOut(
        total_users=total_users,
        total_exams=total_exams,
        total_submissions=total_submissions,
        total_proctoring_alerts=total_proctoring_alerts,
        active_exams_count=active_exams_count,
        model_accuracy=float(round(model_accuracy * 100, 2))
    )
