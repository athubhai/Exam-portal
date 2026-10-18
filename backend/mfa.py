import io
import base64
import pyotp
import qrcode

def generate_mfa_secret() -> str:
    """Generate a random 32-character base32 secret for TOTP"""
    return pyotp.random_base32()

def generate_mfa_uri(email: str, secret: str, issuer_name: str = "SecureExamPortal") -> str:
    """Generate the otpauth:// URI for authenticator apps"""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer_name)

def generate_qr_code_base64(provisioning_uri: str) -> str:
    """Generate a base64 encoded PNG QR code image of the provisioning URI"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=8,
        border=3,
    )
    qr.add_data(provisioning_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    b64_img = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{b64_img}"

def verify_mfa_code(secret: str, code: str) -> bool:
    """Verify a 6-digit TOTP code against the user's secret with 1-step tolerance"""
    if not secret or not code:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code.strip(), valid_window=1)
