import os
import sys
import io
import base64
import numpy as np
import soundfile as sf
import cv2
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import SessionLocal, Base, engine
from models import User, Submission, Exam

client = TestClient(app)

def create_synthetic_frame_base64():
    """Create a synthetic 640x480 frame with a drawn compliant face."""
    frame = np.full((480, 640, 3), 40, dtype=np.uint8)
    # Draw simple facial oval
    cv2.ellipse(frame, (320, 220), (80, 110), 0, 0, 360, (180, 190, 220), -1)
    # Eyes
    cv2.circle(frame, (290, 195), 10, (50, 50, 50), -1)
    cv2.circle(frame, (350, 195), 10, (50, 50, 50), -1)
    # Mouth
    cv2.ellipse(frame, (320, 270), (25, 10), 0, 0, 360, (80, 80, 180), -1)
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return base64.b64encode(buf).decode("utf-8")

def create_synthetic_audio_base64(freq: float = 220.0, duration: float = 2.0):
    """Generate 16kHz synthetic audio tone as base64 WAV."""
    sr = 16000
    t = np.linspace(0, duration, int(sr * duration), endpoint=False, dtype=np.float32)
    audio = 0.3 * np.sin(2 * np.pi * freq * t) + 0.15 * np.sin(2 * np.pi * (freq * 2) * t)
    buf = io.BytesIO()
    sf.write(buf, audio, sr, format="WAV")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

@pytest.fixture(scope="module")
def student_auth():
    login_res = client.post("/api/auth/login", json={
        "email": "student@examportal.com",
        "password": "StudentPass123!"
    })
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_get_verification_phrase(student_auth):
    res = client.get("/api/proctoring/verification-phrase", headers=student_auth)
    assert res.status_code == 200
    data = res.json()
    assert "phrase" in data
    assert len(data["phrase"]) > 20

def test_video_and_audio_calibration_lifecycle(student_auth):
    # Ensure submission #1 exists
    start_res = client.post("/api/submissions/start", headers=student_auth, json={"exam_id": 1})
    submission_id = 1

    frame_b64 = create_synthetic_frame_base64()

    # 1. Send multiple video calibration samples
    for i in range(12):
        cal_res = client.post("/api/proctoring/calibrate-video", headers=student_auth, json={
            "submission_id": submission_id,
            "frame_base64": frame_b64
        })
        assert cal_res.status_code == 200
        assert cal_res.json()["success"] is True

    # 2. Enroll Audio Phrase for student
    audio_b64 = create_synthetic_audio_base64(freq=220.0, duration=2.5)
    audio_cal_res = client.post("/api/proctoring/calibrate-audio", headers=student_auth, json={
        "submission_id": submission_id,
        "audio_base64": audio_b64,
        "phrase_text": "I verify that I am sitting at my desk taking this examination honestly."
    })
    assert audio_cal_res.status_code == 200
    assert audio_cal_res.json()["success"] is True
    assert audio_cal_res.json()["embedding_enrolled"] is True

def test_analyze_multimodal_parallel_comparison(student_auth):
    submission_id = 1
    frame_b64 = create_synthetic_frame_base64()
    # Matching speaker audio (220 Hz)
    audio_b64 = create_synthetic_audio_base64(freq=220.0, duration=2.0)

    res = client.post("/api/proctoring/analyze-multimodal", headers=student_auth, json={
        "submission_id": submission_id,
        "frame_base64": frame_b64,
        "audio_base64": audio_b64,
        "mode": "fused"
    })
    assert res.status_code == 200
    data = res.json()

    # Verify response structure and 3-way parallel comparison
    assert "cheating_probability" in data
    assert "is_suspicious" in data
    assert "flags" in data
    assert "parallel_comparison" in data

    comp = data["parallel_comparison"]
    assert "variant_a_legacy" in comp
    assert "variant_b_personalized_video" in comp
    assert "variant_c_full_fused" in comp
    assert "cheating_probability" in comp["variant_a_legacy"]
    assert "cheating_probability" in comp["variant_b_personalized_video"]
    assert "cheating_probability" in comp["variant_c_full_fused"]
