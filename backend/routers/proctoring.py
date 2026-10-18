import json
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import Submission, ProctoringEvent, User, UserRole
from schemas import (
    FrameAnalysisRequest, FrameAnalysisResponse, ProctoringEventOut,
    VerificationPhraseResponse, VideoCalibrationRequest, VideoCalibrationResponse,
    AudioCalibrationRequest, AudioCalibrationResponse,
    MultimodalAnalysisRequest, MultimodalAnalysisResponse
)
from auth import get_current_user, require_role
from ai_engine.extractor import analyze_webcam_frame, extract_features_from_frame, decode_base64_frame
from ai_engine.calibration_engine import calibration_manager
from ai_engine.audio_engine import audio_engine

router = APIRouter(prefix="/proctoring", tags=["AI Proctoring & Real-Time Alert Engine"])

# ================= WEBSOCKET CONNECTION MANAGER =================
class ProctoringConnectionManager:
    def __init__(self):
        # Maps exam_id -> list of active WebSocket connections (e.g. faculty dashboards)
        self.active_faculty_connections: Dict[int, List[WebSocket]] = {}

    async def connect_faculty(self, exam_id: int, websocket: WebSocket):
        await websocket.accept()
        if exam_id not in self.active_faculty_connections:
            self.active_faculty_connections[exam_id] = []
        self.active_faculty_connections[exam_id].append(websocket)

    def disconnect_faculty(self, exam_id: int, websocket: WebSocket):
        if exam_id in self.active_faculty_connections:
            if websocket in self.active_faculty_connections[exam_id]:
                self.active_faculty_connections[exam_id].remove(websocket)

    async def broadcast_proctoring_alert(self, exam_id: int, alert_data: dict):
        """Push real-time alert to all faculty watching this exam"""
        if exam_id in self.active_faculty_connections:
            dead_sockets = []
            for connection in self.active_faculty_connections[exam_id]:
                try:
                    await connection.send_text(json.dumps(alert_data))
                except Exception:
                    dead_sockets.append(connection)
            for dead in dead_sockets:
                self.disconnect_faculty(exam_id, dead)

proctor_manager = ProctoringConnectionManager()

# ================= PROCTORING ENDPOINTS =================
@router.post("/analyze-frame", response_model=FrameAnalysisResponse)
async def analyze_frame(
    body: FrameAnalysisRequest,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db)
):
    submission = db.query(Submission).filter(
        Submission.id == body.submission_id,
        Submission.student_id == current_user.id
    ).first()

    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found.")

    # Execute AI proctoring pipeline on the frame
    analysis_result = analyze_webcam_frame(body.frame_base64)
    cheating_prob = analysis_result["cheating_probability"]
    is_suspicious = analysis_result["is_suspicious"]
    flags = analysis_result["flags"]

    # Record ProctoringEvent in database if suspicious
    if is_suspicious:
        event_description = " | ".join(flags)
        event = ProctoringEvent(
            submission_id=submission.id,
            timestamp=datetime.utcnow(),
            event_type=event_description,
            confidence_score=cheating_prob,
            frame_reference=body.frame_base64[:60] + "..."  # Short snapshot reference
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        # Broadcast live alert to faculty dashboard via WebSocket
        alert_payload = {
            "type": "PROCTORING_FLAG_ALERT",
            "submission_id": submission.id,
            "exam_id": submission.exam_id,
            "student_name": current_user.name,
            "student_email": current_user.email,
            "cheating_probability": cheating_prob,
            "flags": flags,
            "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
            "snapshot": body.frame_base64
        }
        await proctor_manager.broadcast_proctoring_alert(submission.exam_id, alert_payload)

    return FrameAnalysisResponse(
        cheating_probability=cheating_prob,
        is_suspicious=is_suspicious,
        flags=flags,
        features_summary=analysis_result["features_summary"]
    )

# ================= PERSONALIZED CALIBRATION & MULTIMODAL ENDPOINTS =================
@router.get("/verification-phrase", response_model=VerificationPhraseResponse)
def get_verification_phrase(current_user: User = Depends(require_role(UserRole.STUDENT))):
    """Retrieve a randomized academic honesty phrase for voice enrollment."""
    phrase = calibration_manager.get_random_phrase()
    return VerificationPhraseResponse(phrase=phrase)

@router.post("/calibrate-video", response_model=VideoCalibrationResponse)
def calibrate_video_frame(
    body: VideoCalibrationRequest,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db)
):
    """Collect frame biometrics during the 30-60s pre-exam calibration phase."""
    submission = db.query(Submission).filter(
        Submission.id == body.submission_id,
        Submission.student_id == current_user.id
    ).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found.")

    frame = decode_base64_frame(body.frame_base64)
    features, _ = extract_features_from_frame(frame)
    # Features: [cx:4, cy:5, yaw:6, pitch:7, blink:15]
    cx, cy = float(features[4]), float(features[5])
    yaw, pitch = float(features[6]), float(features[7])
    blink_rate = float(features[15])

    session = calibration_manager.get_or_create_session(str(body.submission_id), current_user.id)
    session.add_calibration_sample(yaw, pitch, blink_rate, cx, cy)

    samples_count = len(session.calibration_samples)
    calibrated = session.video_calibrated
    summary = None

    # Automatically finalize once 30 samples are reached (or on demand)
    if samples_count >= 30 and not calibrated:
        summary = session.finalize_video_calibration()
        calibrated = session.video_calibrated

    return VideoCalibrationResponse(
        success=True,
        samples_count=samples_count,
        calibrated=calibrated,
        summary=summary
    )

@router.post("/calibrate-audio", response_model=AudioCalibrationResponse)
def calibrate_audio_utterance(
    body: AudioCalibrationRequest,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db)
):
    """Enroll student's voice embedding from the spoken verification phrase."""
    submission = db.query(Submission).filter(
        Submission.id == body.submission_id,
        Submission.student_id == current_user.id
    ).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found.")

    session = calibration_manager.get_or_create_session(str(body.submission_id), current_user.id)
    res = session.enroll_audio_phrase(body.audio_base64, body.phrase_text)

    return AudioCalibrationResponse(
        success=res.get("success", False),
        duration_sec=res.get("duration_sec", 0.0),
        embedding_enrolled=session.audio_enrolled,
        error=res.get("error")
    )

@router.post("/analyze-multimodal", response_model=MultimodalAnalysisResponse)
async def analyze_multimodal(
    body: MultimodalAnalysisRequest,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db)
):
    """
    Unified Multi-Modal Proctoring Inference Pipeline:
    - Fuses Video Baseline (Z-score, Isolation Forest, EWMA Drift) + Audio Voice Biometrics (Resemblyzer + Silero VAD)
    - Produces real-time parallel 3-way outcomes (Variant A: Legacy, Variant B: Personalized Video, Variant C: Full Fused)
    """
    submission = db.query(Submission).filter(
        Submission.id == body.submission_id,
        Submission.student_id == current_user.id
    ).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found.")

    session = calibration_manager.get_or_create_session(str(body.submission_id), current_user.id)
    mode = body.mode or "fused"

    # 1. Evaluate Video Frame (if provided and mode is not audio_only)
    features = [0.0] * 37
    legacy_flags = ["NORMAL_HONEST_BEHAVIOR"]
    legacy_prob = 0.05
    legacy_suspicious = False
    video_eval = None

    if body.frame_base64 and mode != "audio_only":
        frame = decode_base64_frame(body.frame_base64)
        features, raw_flags = extract_features_from_frame(frame)
        legacy_res = analyze_webcam_frame(body.frame_base64)
        legacy_prob = legacy_res["cheating_probability"]
        legacy_suspicious = legacy_res["is_suspicious"]
        legacy_flags = legacy_res["flags"]

        # Evaluate against personalized video baseline
        cx, cy = float(features[4]), float(features[5])
        yaw, pitch = float(features[6]), float(features[7])
        blink_rate = float(features[15])
        video_eval = session.score_video_frame(yaw, pitch, blink_rate, cx, cy)

    # 2. Evaluate Audio Chunk (if provided and mode is not video_only)
    audio_eval = None
    if body.audio_base64 and mode != "video_only":
        audio_eval = session.score_audio_chunk(body.audio_base64)

    # 3. Construct Parallel Outcomes
    # Variant A: Legacy static global thresholds
    variant_a = {
        "cheating_probability": round(legacy_prob, 2),
        "is_suspicious": legacy_suspicious,
        "flags": legacy_flags
    }

    # Variant B: Personalized Video Baseline (Z-Score + Isolation Forest + Baseline Drift)
    variant_b_flags = []
    # Retain non-pose severe flags from vision (phone, books, multiple persons)
    severe_vision = [f for f in legacy_flags if any(k in f for k in ["PHONE", "BOOK", "MULTIPLE_PERSONS", "NO_FACE"])]
    variant_b_flags.extend(severe_vision)
    if video_eval and video_eval.get("calibrated", False):
        variant_b_flags.extend(video_eval.get("flags", []))
    elif legacy_suspicious:
        # Fallback to legacy pose flags if calibration not active
        variant_b_flags.extend([f for f in legacy_flags if "HEAD" in f or "LOOKING" in f])

    b_suspicious = bool(len(variant_b_flags) > 0 and variant_b_flags != ["NORMAL_HONEST_BEHAVIOR"])
    b_prob = max([0.90 if any("PHONE" in f for f in variant_b_flags) else 0.75 for f in variant_b_flags], default=0.08)
    variant_b = {
        "cheating_probability": round(float(b_prob if b_suspicious else 0.06), 2),
        "is_suspicious": b_suspicious,
        "flags": variant_b_flags if b_suspicious else ["NORMAL_HONEST_BEHAVIOR"]
    }

    # Variant C: Full Fused Multi-Modal (Personalized Video + Resemblyzer Voice Biometrics)
    fused_flags = list(variant_b_flags) if b_suspicious else []
    fused_prob = float(b_prob if b_suspicious else 0.05)

    if audio_eval and audio_eval.get("flags"):
        for af in audio_eval["flags"]:
            if af not in fused_flags:
                fused_flags.append(af)
            if af == "SECOND_VOICE_DETECTED":
                fused_prob = max(fused_prob, 0.96)
            elif af == "SUSTAINED_WHISPERING":
                fused_prob = max(fused_prob, 0.88)

    c_suspicious = bool(len(fused_flags) > 0)
    variant_c = {
        "cheating_probability": round(float(fused_prob if c_suspicious else 0.05), 2),
        "is_suspicious": c_suspicious,
        "flags": fused_flags if c_suspicious else ["NORMAL_HONEST_BEHAVIOR"]
    }

    # Record and Broadcast if suspicious in the fused pipeline
    if c_suspicious:
        event_description = " | ".join(fused_flags)
        event = ProctoringEvent(
            submission_id=submission.id,
            timestamp=datetime.utcnow(),
            event_type=event_description,
            confidence_score=variant_c["cheating_probability"],
            frame_reference=(body.frame_base64[:60] + "...") if body.frame_base64 else "audio_chunk"
        )
        db.add(event)
        db.commit()

        # Broadcast live alert to faculty dashboard via WebSocket
        alert_payload = {
            "type": "PROCTORING_FLAG_ALERT",
            "submission_id": submission.id,
            "exam_id": submission.exam_id,
            "student_name": current_user.name,
            "student_email": current_user.email,
            "cheating_probability": variant_c["cheating_probability"],
            "flags": fused_flags,
            "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
            "snapshot": body.frame_base64,
            "detection_method": "ZScore+IsolationForest+Resemblyzer"
        }
        await proctor_manager.broadcast_proctoring_alert(submission.exam_id, alert_payload)

    features_summary = {
        "face_count": int(features[1]),
        "head_yaw": round(float(features[6]), 1),
        "head_pitch": round(float(features[7]), 1),
        "gaze_focus": round(float(features[14]), 2),
        "hand_detected": bool(features[20] > 0),
        "phone_score": round(float(features[30]), 2)
    }

    return MultimodalAnalysisResponse(
        cheating_probability=variant_c["cheating_probability"],
        is_suspicious=variant_c["is_suspicious"],
        flags=variant_c["flags"],
        features_summary=features_summary,
        audio_summary=audio_eval,
        video_baseline_summary=video_eval,
        parallel_comparison={
            "variant_a_legacy": variant_a,
            "variant_b_personalized_video": variant_b,
            "variant_c_full_fused": variant_c
        }
    )

@router.get("/events/{submission_id}", response_model=List[ProctoringEventOut])
def get_submission_proctoring_events(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found.")

    if current_user.role == UserRole.STUDENT and submission.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden.")

    return submission.proctoring_events

# ================= WEBSOCKET ROUTE FOR FACULTY LIVE MONITOR =================
@router.websocket("/ws/{exam_id}")
async def websocket_proctor_monitor(websocket: WebSocket, exam_id: int):
    """
    WebSocket endpoint for Faculty / Admin to receive real-time proctoring alerts.
    Requires JWT token via query parameter: ws://host/api/proctoring/ws/{exam_id}?token=<jwt>
    """
    # Authenticate WebSocket connection via JWT token in query params
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Authentication required. Provide ?token=<jwt>")
        return

    try:
        from auth import decode_token
        payload = decode_token(token)
        if payload.get("token_type") != "access":
            await websocket.close(code=1008, reason="Invalid token type.")
            return
        user_role = payload.get("role", "")
        if user_role not in ("Admin", "Faculty"):
            await websocket.close(code=1008, reason="Forbidden: Faculty or Admin role required.")
            return
    except Exception:
        await websocket.close(code=1008, reason="Invalid or expired token.")
        return

    await proctor_manager.connect_faculty(exam_id, websocket)
    try:
        while True:
            # Keep connection alive; faculty client can send heartbeat pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "PONG", "timestamp": datetime.utcnow().isoformat()}))
    except WebSocketDisconnect:
        proctor_manager.disconnect_faculty(exam_id, websocket)
    except Exception:
        proctor_manager.disconnect_faculty(exam_id, websocket)
