from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, EmailStr, Field
from models import UserRole, ExamStatus, SubmissionStatus

# ================= AUTH & USER SCHEMAS =================
class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, example="John Doe")
    email: EmailStr = Field(..., example="user@examportal.com")
    password: str = Field(..., min_length=6, max_length=100, example="SecurePassword123!")
    role: Optional[UserRole] = Field(default=UserRole.STUDENT)

class UserLogin(BaseModel):
    email: EmailStr = Field(..., example="admin@examportal.com")
    password: str = Field(..., example="AdminPass123!")
    mfa_code: Optional[str] = None

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole
    mfa_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserCreateAdmin(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole

class UserRoleUpdate(BaseModel):
    role: UserRole

# ================= EXAM & QUESTION SCHEMAS =================
class QuestionCreate(BaseModel):
    question_text: str = Field(..., min_length=3, example="What does RBAC stand for?")
    options: List[str] = Field(..., min_items=2, example=["Role-Based Access Control", "Random Block Cipher", "Rule Based Auth Check", "Remote Backend API Call"])
    correct_answer: str = Field(..., example="Role-Based Access Control")
    marks: int = Field(default=1, ge=1)

class QuestionOut(BaseModel):
    id: int
    exam_id: int
    question_text: str
    options: List[str]
    correct_answer: str  # Decrypted only for Faculty / Admin
    marks: int

    class Config:
        from_attributes = True

class QuestionStudentOut(BaseModel):
    id: int
    exam_id: int
    question_text: str
    options: List[str]
    marks: int

class ExamCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, example="Computer Systems & Security Midterm")
    start_time: datetime
    end_time: datetime
    duration_minutes: int = Field(..., ge=5, le=360, example=60)

class ExamUpdate(BaseModel):
    title: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    status: Optional[ExamStatus] = None

class ExamOut(BaseModel):
    id: int
    title: str
    created_by: int
    creator_name: Optional[str] = None
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    status: ExamStatus
    total_questions: int = 0
    total_marks: int = 0

    class Config:
        from_attributes = True

# ================= SUBMISSION SCHEMAS =================
class SubmissionStartRequest(BaseModel):
    exam_id: int

class AutosaveRequest(BaseModel):
    submission_id: int
    answers: Dict[str, str]  # { "question_id": "selected_option" }

class SubmitExamRequest(BaseModel):
    submission_id: int
    answers: Dict[str, str]

class SubmissionOut(BaseModel):
    id: int
    exam_id: int
    exam_title: Optional[str] = None
    student_id: int
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    submitted_at: Optional[datetime] = None
    auto_score: Optional[float] = None
    total_marks: Optional[int] = None
    status: SubmissionStatus
    flagged_events_count: int = 0
    cheating_risk_level: str = "LOW"

    class Config:
        from_attributes = True

# ================= PROCTORING SCHEMAS =================
class FrameAnalysisRequest(BaseModel):
    submission_id: int
    frame_base64: str  # JPEG/PNG base64 string

class FrameAnalysisResponse(BaseModel):
    cheating_probability: float
    is_suspicious: bool
    flags: List[str]
    features_summary: Dict[str, Any]

class VerificationPhraseResponse(BaseModel):
    phrase: str

class VideoCalibrationRequest(BaseModel):
    submission_id: int
    frame_base64: str

class VideoCalibrationResponse(BaseModel):
    success: bool
    samples_count: int
    calibrated: bool
    summary: Optional[Dict[str, Any]] = None

class AudioCalibrationRequest(BaseModel):
    submission_id: int
    audio_base64: str
    phrase_text: Optional[str] = None

class AudioCalibrationResponse(BaseModel):
    success: bool
    duration_sec: float
    embedding_enrolled: bool
    error: Optional[str] = None

class MultimodalAnalysisRequest(BaseModel):
    submission_id: int
    frame_base64: Optional[str] = None
    audio_base64: Optional[str] = None
    mode: Optional[str] = "fused"  # "fused", "video_only", "audio_only"

class MultimodalAnalysisResponse(BaseModel):
    cheating_probability: float
    is_suspicious: bool
    flags: List[str]
    features_summary: Dict[str, Any]
    audio_summary: Optional[Dict[str, Any]] = None
    video_baseline_summary: Optional[Dict[str, Any]] = None
    parallel_comparison: Dict[str, Any]

class ProctoringEventOut(BaseModel):
    id: int
    submission_id: int
    timestamp: datetime
    event_type: str
    confidence_score: float
    frame_reference: Optional[str] = None

    class Config:
        from_attributes = True

# ================= ADMIN & AUDIT SCHEMAS =================
class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    action: str
    target_resource: Optional[str] = None
    timestamp: datetime
    ip_address: Optional[str] = None

    class Config:
        from_attributes = True

class SystemStatsOut(BaseModel):
    total_users: int
    total_exams: int
    total_submissions: int
    total_proctoring_alerts: int
    active_exams_count: int
    model_accuracy: float

# ================= MFA SCHEMAS =================
class MFASetupResponse(BaseModel):
    secret: str
    qr_code_image: str
    provisioning_uri: str

class MFAVerifyRequest(BaseModel):
    code: str
    secret: Optional[str] = None
