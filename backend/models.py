import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Float, Text, JSON, ForeignKey, Enum, Index
)
from sqlalchemy.orm import relationship
from database import Base

class UserRole(str, enum.Enum):
    ADMIN = "Admin"
    FACULTY = "Faculty"
    STUDENT = "Student"

class ExamStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"

class SubmissionStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    EVALUATED = "EVALUATED"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.STUDENT)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(64), nullable=True)

    # Relationships
    created_exams = relationship("Exam", back_populates="creator", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="student", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    status = Column(Enum(ExamStatus), nullable=False, default=ExamStatus.DRAFT)

    # Relationships
    creator = relationship("User", back_populates="created_exams")
    questions = relationship("Question", back_populates="exam", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="exam", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text_encrypted = Column(Text, nullable=False)
    options = Column(JSON, nullable=True)  # List of option strings e.g. ["A", "B", "C", "D"]
    correct_answer_encrypted = Column(Text, nullable=False)
    marks = Column(Integer, nullable=False, default=1)

    # Relationships
    exam = relationship("Exam", back_populates="questions")

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    answers_encrypted = Column(Text, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    auto_score = Column(Float, nullable=True)
    status = Column(Enum(SubmissionStatus), nullable=False, default=SubmissionStatus.IN_PROGRESS)

    # Relationships
    exam = relationship("Exam", back_populates="submissions")
    student = relationship("User", back_populates="submissions")
    proctoring_events = relationship("ProctoringEvent", back_populates="submission", cascade="all, delete-orphan")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    target_resource = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

class ProctoringEvent(Base):
    __tablename__ = "proctoring_events"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    confidence_score = Column(Float, nullable=False)
    frame_reference = Column(String(255), nullable=True)

    # Relationships
    submission = relationship("Submission", back_populates="proctoring_events")
