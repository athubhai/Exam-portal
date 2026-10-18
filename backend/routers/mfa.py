from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from database import get_db
from models import User
from schemas import MFASetupResponse, MFAVerifyRequest
from auth import get_current_user
from mfa import generate_mfa_secret, generate_mfa_uri, generate_qr_code_base64, verify_mfa_code
from crypto import encrypt_text, decrypt_text
from utils import log_audit_action

router = APIRouter(prefix="/mfa", tags=["Multi-Factor Authentication (MFA)"])

@router.get("/setup", response_model=MFASetupResponse)
def setup_mfa(current_user: User = Depends(get_current_user)):
    """Generate a new TOTP secret and QR code image for authenticator apps"""
    secret = generate_mfa_secret()
    uri = generate_mfa_uri(current_user.email, secret)
    qr_code_b64 = generate_qr_code_base64(uri)

    return MFASetupResponse(
        secret=secret,
        qr_code_image=qr_code_b64,
        provisioning_uri=uri
    )

@router.post("/enable")
def enable_mfa(
    body: MFAVerifyRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify 6-digit OTP and enable MFA on the user account"""
    if not body.secret:
        raise HTTPException(status_code=400, detail="MFA setup secret is required.")

    is_valid = verify_mfa_code(body.secret, body.code)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid 6-digit OTP authentication code.")

    current_user.mfa_enabled = True
    # Encrypt MFA secret at rest to protect against database compromise
    current_user.mfa_secret = encrypt_text(body.secret)
    db.commit()

    ip = request.client.host if request.client else "127.0.0.1"
    log_audit_action(db, current_user.id, "MFA_ENABLED", f"MFA enabled for {current_user.email}", ip=ip)

    return {"status": "success", "message": "Multi-Factor Authentication successfully enabled.", "mfa_enabled": True}

@router.post("/disable")
def disable_mfa(
    body: MFAVerifyRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable MFA after verifying current OTP"""
    if not current_user.mfa_enabled or not current_user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA is not enabled on this account.")

    # Decrypt stored MFA secret before verification
    decrypted_secret = decrypt_text(current_user.mfa_secret)
    is_valid = verify_mfa_code(decrypted_secret, body.code)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid 6-digit OTP code to disable MFA.")

    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    db.commit()

    ip = request.client.host if request.client else "127.0.0.1"
    log_audit_action(db, current_user.id, "MFA_DISABLED", f"MFA disabled for {current_user.email}", ip=ip)

    return {"status": "success", "message": "Multi-Factor Authentication disabled.", "mfa_enabled": False}
