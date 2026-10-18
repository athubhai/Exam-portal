import time
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from database import get_db
from models import User, UserRole
from schemas import (
    UserRegister, UserLogin, UserOut, TokenResponse, RefreshTokenRequest
)
from auth import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    decode_token, get_current_user, require_role
)
from mfa import verify_mfa_code
from crypto import decrypt_text
from utils import log_audit_action

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])

# In-memory Rate Limiter: IP -> list of attempt timestamps in the last 60 seconds
# Note (#14): This is suitable for single-process dev. For production with multiple
# workers, use Redis-based rate limiting (e.g., slowapi or fastapi-limiter).
LOGIN_ATTEMPTS: Dict[str, list] = {}
RATE_LIMIT_MAX_ATTEMPTS = 8
RATE_LIMIT_WINDOW_SECONDS = 60

def check_rate_limit(ip: str):
    now = time.time()
    if ip not in LOGIN_ATTEMPTS:
        LOGIN_ATTEMPTS[ip] = []
    # Filter out attempts older than window
    LOGIN_ATTEMPTS[ip] = [t for t in LOGIN_ATTEMPTS[ip] if now - t < RATE_LIMIT_WINDOW_SECONDS]
    if len(LOGIN_ATTEMPTS[ip]) >= RATE_LIMIT_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please wait 1 minute before trying again."
        )
    LOGIN_ATTEMPTS[ip].append(now)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "127.0.0.1"
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )
        
    hashed_pw = hash_password(user_in.password)
    # Security: Always force Student role on self-registration.
    # Only admins can assign elevated roles via PUT /admin/users/{id}/role.
    new_user = User(
        name=user_in.name,
        email=user_in.email,
        hashed_password=hashed_pw,
        role=UserRole.STUDENT,
        mfa_enabled=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    log_audit_action(
        db, new_user.id, "USER_REGISTERED", f"User {new_user.email} registered with role {new_user.role.value}",
        ip
    )
    
    return new_user

@router.post("/login")
def login(login_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "127.0.0.1"
    check_rate_limit(ip)

    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        log_audit_action(
            db, None, "LOGIN_FAILED", f"Failed login attempt for email {login_data.email}", ip
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check MFA requirement if enabled on user account
    if user.mfa_enabled:
        if not login_data.mfa_code:
            return {
                "mfa_required": True,
                "message": "MFA is enabled on this account. Please provide your 6-digit TOTP code.",
                "email": user.email
            }
        # MFA secrets are stored encrypted at rest; decrypt before verification
        decrypted_mfa_secret = decrypt_text(user.mfa_secret) if user.mfa_secret else None
        is_mfa_valid = verify_mfa_code(decrypted_mfa_secret, login_data.mfa_code)
        if not is_mfa_valid:
            log_audit_action(
                db, user.id, "MFA_VERIFICATION_FAILED", f"Invalid MFA code provided for {user.email}", ip
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 6-digit MFA authentication code."
            )
        
    token_payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value if isinstance(user.role, UserRole) else str(user.role),
        "name": user.name
    }
    
    access_token = create_access_token(data=token_payload)
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    log_audit_action(
        db, user.id, "USER_LOGIN_SUCCESS", f"User logged in as {user.role.value}", ip
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.value,
            "mfa_enabled": user.mfa_enabled,
            "created_at": user.created_at
        }
    }

@router.post("/refresh")
def refresh_token(body: RefreshTokenRequest, db: Session = Depends(get_db)):
    payload = decode_token(body.refresh_token)
    if payload.get("token_type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type for token refresh."
        )
        
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload."
        )
        
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token no longer exists."
        )
        
    new_payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value if isinstance(user.role, UserRole) else str(user.role),
        "name": user.name
    }
    
    new_access_token = create_access_token(data=new_payload)
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/admin-demo")
def admin_only_endpoint(current_user: User = Depends(require_role(UserRole.ADMIN))):
    return {
        "status": "success",
        "message": f"Welcome Admin {current_user.name}! You have accessed an Admin-restricted resource.",
        "user_id": current_user.id,
        "role": current_user.role.value,
        "timestamp": datetime.now(timezone.utc)
    }

@router.get("/faculty-demo")
def faculty_or_admin_endpoint(current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.FACULTY))):
    return {
        "status": "success",
        "message": f"Welcome {current_user.name}! You have accessed a Faculty/Examiner resource.",
        "user_id": current_user.id,
        "role": current_user.role.value,
        "timestamp": datetime.now(timezone.utc)
    }
