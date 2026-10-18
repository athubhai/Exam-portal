"""
User Profile Management Router (#26, #27)
Provides password change and profile update endpoints for authenticated users.
"""

import re
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator

from database import get_db
from models import User
from auth import get_current_user, hash_password, verify_password
from utils import log_audit_action


router = APIRouter(prefix="/profile", tags=["User Profile Management"])


# ================= SCHEMAS =================

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters long.')
        if not re.search(r'[A-Z]', v):
            raise ValueError('New password must contain at least one uppercase letter.')
        if not re.search(r'[a-z]', v):
            raise ValueError('New password must contain at least one lowercase letter.')
        if not re.search(r'\d', v):
            raise ValueError('New password must contain at least one digit.')
        return v


class ProfileUpdateRequest(BaseModel):
    name: str | None = None
    email: str | None = None

    @field_validator('name')
    @classmethod
    def sanitize_name(cls, v):
        if v is not None:
            # Strip HTML tags for XSS prevention (#29)
            v = re.sub(r'<[^>]+>', '', v).strip()
            if len(v) < 2 or len(v) > 100:
                raise ValueError('Name must be between 2 and 100 characters.')
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v is not None:
            v = v.strip().lower()
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
                raise ValueError('Invalid email address format.')
        return v


# ================= ENDPOINTS =================

@router.get("/me")
def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile details."""
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role.value,
        "mfa_enabled": current_user.mfa_enabled,
        "created_at": current_user.created_at,
    }


@router.put("/update")
def update_profile(
    body: ProfileUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user name and/or email (#27)."""
    changes = []

    if body.name is not None and body.name != current_user.name:
        current_user.name = body.name
        changes.append(f"name→{body.name}")

    if body.email is not None and body.email != current_user.email:
        # Check email uniqueness
        existing = db.query(User).filter(User.email == body.email).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="An account with this email already exists."
            )
        current_user.email = body.email
        changes.append(f"email→{body.email}")

    if not changes:
        return {"status": "no_change", "message": "No profile changes detected."}

    db.commit()
    db.refresh(current_user)

    ip = request.client.host if request.client else "127.0.0.1"
    log_audit_action(
        db, current_user.id, "PROFILE_UPDATED",
        f"User updated profile: {', '.join(changes)}",
        ip=ip
    )

    return {
        "status": "success",
        "message": "Profile updated successfully.",
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role.value,
        }
    }


@router.post("/change-password")
def change_password(
    body: PasswordChangeRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user's password (#26). Requires current password verification."""
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect."
        )

    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400,
            detail="New password must be different from current password."
        )

    current_user.hashed_password = hash_password(body.new_password)
    db.commit()

    ip = request.client.host if request.client else "127.0.0.1"
    log_audit_action(
        db, current_user.id, "PASSWORD_CHANGED",
        f"Password changed for {current_user.email}",
        ip=ip
    )

    return {
        "status": "success",
        "message": "Password changed successfully. Please log in again with your new password."
    }
