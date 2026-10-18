"""
Shared utilities for the Secure Exam Portal backend.
Centralizes audit logging, risk level computation, and structured logging.
"""

import logging
import sys
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import Request

from models import AuditLog


# ================= STRUCTURED LOGGING (#30) =================
def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Configure structured logging with timestamps and module context.
    Replaces ad-hoc print() statements across the codebase.
    """
    logger = logging.getLogger("exam_portal")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s.%(funcName)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger


logger = setup_logging()


# ================= SHARED AUDIT LOGGING (#7) =================
def log_audit_action(
    db: Session,
    user_id: int | None,
    action: str,
    resource: str,
    ip: str | None = None,
    request: Request | None = None,
) -> None:
    """
    Centralized audit log writer. Extracted from duplicated implementations
    in routers/auth.py, routers/exams.py, and routers/submissions.py.
    """
    try:
        resolved_ip = ip
        if resolved_ip is None and request is not None:
            resolved_ip = request.client.host if request.client else "127.0.0.1"
        elif resolved_ip is None:
            resolved_ip = "127.0.0.1"

        log = AuditLog(
            user_id=user_id,
            action=action,
            target_resource=resource,
            timestamp=datetime.now(timezone.utc),
            ip_address=resolved_ip,
        )
        db.add(log)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Failed to write audit log: %s", e)


# ================= CONSISTENT RISK LEVEL (#9) =================
def compute_risk_level(flagged_events_count: int) -> str:
    """
    Compute cheating risk level from the number of proctoring flag events.
    Consistent thresholds used across all endpoints:
      - 0 flags      → LOW
      - 1-2 flags    → MEDIUM
      - 3+ flags     → HIGH
    """
    if flagged_events_count >= 3:
        return "HIGH"
    elif flagged_events_count >= 1:
        return "MEDIUM"
    return "LOW"
