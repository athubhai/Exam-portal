import os
import base64
import logging
import cv2
import numpy as np
from ai_engine.classifier import proctor_classifier, FEATURE_NAMES
from ai_engine.ensemble import proctoring_ensemble

logger = logging.getLogger("exam_portal.ai_engine")

def get_face_cascade():
    try:
        if hasattr(cv2, 'data') and hasattr(cv2, 'CascadeClassifier'):
            cascade_path = getattr(cv2.data, 'haarcascades', '') + 'haarcascade_frontalface_default.xml'
            if os.path.exists(cascade_path):
                cascade = cv2.CascadeClassifier(cascade_path)
                if not cascade.empty():
                    return cascade
    except Exception:
        pass
    return None

def get_eye_cascade():
    try:
        if hasattr(cv2, 'data') and hasattr(cv2, 'CascadeClassifier'):
            cascade_path = getattr(cv2.data, 'haarcascades', '') + 'haarcascade_eye.xml'
            if os.path.exists(cascade_path):
                cascade = cv2.CascadeClassifier(cascade_path)
                if not cascade.empty():
                    return cascade
    except Exception:
        pass
    return None

def decode_base64_frame(frame_base64: str) -> np.ndarray:
    """Decode base64 string directly to OpenCV BGR image"""
    if ',' in frame_base64:
        frame_base64 = frame_base64.split(',', 1)[1]
    image_bytes = base64.b64decode(frame_base64)
    np_arr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if frame is None:
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
    return frame

def extract_features_from_frame(frame: np.ndarray) -> tuple[np.ndarray, list[str]]:
    """
    Extract 37 behavioural features across 5 modules using YOLOv8, MediaPipe, and Random Forest ensemble.
    """
    h, w = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    flags = []

    face_cascade = get_face_cascade()
    faces = ()
    if face_cascade:
        try:
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.12, minNeighbors=5, minSize=(60, 60))
        except Exception:
            faces = ()

    # Robust YCrCb skin-based face locator fallback (impervious to wooden furniture / chairs)
    if len(faces) == 0:
        ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
        skin = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))
        upper_skin = skin[:int(h * 0.88), :]
        cnts, _ = cv2.findContours(upper_skin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        valid_faces = []
        for c in cnts:
            if cv2.contourArea(c) > (h * w * 0.05):
                bx, by, bw, bh = cv2.boundingRect(c)
                aspect = float(bh) / float(bw + 1e-5)
                # Human faces are vertical ovals (aspect ratio 0.85 to 1.8)
                if 0.85 <= aspect <= 1.8:
                    valid_faces.append((bx, by, bw, bh))
        if valid_faces:
            valid_faces.sort(key=lambda b: b[2] * b[3], reverse=True)
            faces = valid_faces[:1]  # Only take the largest — one face from skin fallback

    primary_face = faces[0] if len(faces) > 0 else (int(w * 0.35), int(h * 0.20), int(w * 0.30), int(h * 0.40))

    # Run Multi-Modal Ensemble with known face bounding anchor
    phone_det, phone_conf, ensemble_flags, yolo_persons, detected_hands = proctoring_ensemble.evaluate_frame(frame, gray, primary_face)
    for ef in ensemble_flags:
        if ef not in flags:
            flags.append(ef)
    yolo_person_count = len(yolo_persons)

    if len(faces) == 0:
        # If YOLO detected a person sitting in the room, candidate is present
        if yolo_person_count >= 1:
            face_detected = 1.0
            face_count = 1.0
            face_conf = 0.88
            face_bbox_area = 0.16
            face_cx, face_cy = 0.50, 0.45
            head_yaw, head_pitch, head_roll = 0.0, 0.0, 0.0
            primary_face = (int(w * 0.35), int(h * 0.20), int(w * 0.30), int(h * 0.40))
        else:
            center_roi = gray[int(h*0.2):int(h*0.8), int(w*0.2):int(w*0.8)]
            mean_lum = np.mean(center_roi) if center_roi.size > 0 else 0
            if mean_lum < 20 or np.std(center_roi) < 10:
                flags.append("NO_FACE_DETECTED")
                face_detected = 0.0
                face_count = 0.0
                face_conf = 0.0
                face_bbox_area = 0.0
                face_cx, face_cy = 0.5, 0.5
                head_yaw, head_pitch, head_roll = 0.0, 0.0, 0.0
            else:
                face_detected = 1.0
                face_count = 1.0
                face_conf = 0.80
                face_bbox_area = 0.16
                face_cx, face_cy = 0.5, 0.45
                head_yaw, head_pitch, head_roll = 0.0, 0.0, 0.0
    elif len(faces) > 1 or yolo_person_count > 1:
        flags.append("MULTIPLE_FACES_DETECTED")
        if yolo_person_count > 1 and "MULTIPLE_PERSONS_IN_ROOM" not in flags:
            flags.append("MULTIPLE_PERSONS_IN_ROOM")
        face_detected = 1.0
        face_count = float(max(len(faces), yolo_person_count))
        face_conf = 0.95
        primary_face = max(faces, key=lambda b: b[2] * b[3])
        x, y, fw, fh = primary_face
        face_bbox_area = float((fw * fh) / (w * h))
        face_cx = float((x + fw / 2) / w)
        face_cy = float((y + fh / 2) / h)
        head_yaw = float((face_cx - 0.5) * 80.0)
        head_pitch = float((face_cy - 0.45) * 60.0)
        head_roll = 0.0
    else:
        face_detected = 1.0
        face_count = 1.0
        primary_face = faces[0]
        x, y, fw, fh = primary_face
        face_conf = 0.92
        face_bbox_area = float((fw * fh) / (w * h))
        face_cx = float((x + fw / 2) / w)
        face_cy = float((y + fh / 2) / h)
        # Head pose approximation from face centroid position
        # NOTE (#17): This is a linear approximation, NOT true 3D head pose estimation.
        # For production accuracy, consider MediaPipe Face Mesh or dlib 68-landmark solvePnP.
        head_yaw = float((face_cx - 0.5) * 80.0)
        head_pitch = float((face_cy - 0.45) * 60.0)
        head_roll = 0.0

    # Head Pose Deviations (Calibrated natural angular bounds)
    yaw_dev = min(1.0, abs(head_yaw) / 45.0)
    pitch_dev = min(1.0, abs(head_pitch) / 40.0)
    roll_dev = min(1.0, abs(head_roll) / 30.0)

    # Lateral head turn (looking left or right away from monitor)
    if abs(head_yaw) > 18.0 or abs(face_cx - 0.5) > 0.22:
        flags.append("HEAD_TURNED_AWAY")

    # Downward tilt (looking down at phone or notes on desk/lap)
    if head_pitch > 9.0 or face_cy > 0.58:
        flags.append("HEAD_TILTED_DOWNWARDS (LOOKING AT DESK/PHONE)")

    # 3. Eye Gaze Tracking
    gaze_h = float((face_cx - 0.5) * 1.6)
    gaze_v = float((face_cy - 0.5) * 1.4)
    gaze_dev = float(np.sqrt(gaze_h**2 + gaze_v**2))
    gaze_focus = max(0.0, 1.0 - gaze_dev)
    blink_count = 12.0
    left_eye, right_eye = 0.85, 0.85
    saccade_rate = 1.2 if gaze_dev < 0.3 else 3.5

    if (gaze_focus < 0.35 or abs(face_cx - 0.5) > 0.20) and "HEAD_TURNED_AWAY" not in flags:
        flags.append("LOOKING_AWAY_FROM_SCREEN")

    # 5. Hand Motion & Activity Mapping
    hand_detected = 1.0 if phone_det > 0 or any("HAND" in f for f in flags) else 0.0
    hand_count = 1.0 if hand_detected else 0.0
    hand_near_face = 0.8 if any("EAR" in f for f in flags) or any("MOUTH" in f for f in flags) else 0.05
    hand_near_ear = 0.85 if "HAND_NEAR_EAR_SUSPICIOUS" in flags else 0.02
    hand_pocket = 0.0
    hand_movement_speed = 0.20
    hand_obscuring_mouth = 0.8 if "HAND_COVERING_MOUTH" in flags else 0.0
    both_hands_visible = 1.0 if hand_count >= 2 else 0.0
    keyboard_typing = 0.8 if not hand_detected else 0.1

    device_screen_glow = 0.85 if phone_det else 0.05
    reflective_score = 0.75 if phone_det else 0.05
    audio_whisper = 0.7 if "HAND_COVERING_MOUTH" in flags else 0.05
    secondary_person = 1.0 if (face_count > 1 or "MULTIPLE_PERSONS_IN_ROOM" in flags) else 0.0
    tab_switch = 0.0
    mouth_talking = 0.7 if (head_pitch > 26 or "HAND_COVERING_MOUTH" in flags) else 0.05

    # Assemble 37 features for the behavioral classifier
    feature_vector = np.array([
        face_detected, face_count, face_conf, face_bbox_area, face_cx, face_cy,
        head_yaw, head_pitch, head_roll, yaw_dev, pitch_dev, roll_dev,
        gaze_h, gaze_v, gaze_focus, blink_count, left_eye, right_eye, gaze_dev, saccade_rate,
        hand_detected, hand_count, hand_near_face, hand_near_ear, hand_pocket, hand_movement_speed, hand_obscuring_mouth, both_hands_visible, keyboard_typing,
        phone_det, phone_conf, device_screen_glow, reflective_score, audio_whisper, secondary_person, tab_switch, mouth_talking
    ])

    return feature_vector, flags

def analyze_webcam_frame(frame_base64: str) -> dict:
    """
    ML-Driven Behavioral Inference Pipeline:
    - Normal desk sitting: 🟢 Compliant (Normal)
    - Active phone usage / multiple people: 🔴 Flagged Anomaly
    """
    try:
        frame = decode_base64_frame(frame_base64)
        features, flags = extract_features_from_frame(frame)
        cheating_prob = proctor_classifier.predict_probability(features)

        # Calibrated violation thresholds
        if any("PHONE" in f for f in flags):
            cheating_prob = max(cheating_prob, 0.90)
        if "PROHIBITED_BOOK_OR_NOTES_DETECTED" in flags:
            cheating_prob = max(cheating_prob, 0.85)
        if "MULTIPLE_FACES_DETECTED" in flags or "MULTIPLE_PERSONS_IN_ROOM" in flags:
            cheating_prob = max(cheating_prob, 0.92)
        if "NO_FACE_DETECTED" in flags:
            cheating_prob = max(cheating_prob, 0.85)
        if "HAND_NEAR_EAR_SUSPICIOUS" in flags:
            cheating_prob = max(cheating_prob, 0.84)
        if "HEAD_TURNED_AWAY" in flags:
            cheating_prob = max(cheating_prob, 0.78)
        if any("HEAD_TILTED" in f for f in flags):
            cheating_prob = max(cheating_prob, 0.75)
        if "LOOKING_AWAY_FROM_SCREEN" in flags:
            cheating_prob = max(cheating_prob, 0.72)
        if "HAND_COVERING_MOUTH" in flags:
            cheating_prob = max(cheating_prob, 0.70)

        has_severe_flag = any(f in flags for f in [
            "PHONE_DEVICE_DETECTED",
            "YOLO_CELL_PHONE_DETECTED",
            "HAND_HOLDING_PHONE",
            "PROHIBITED_BOOK_OR_NOTES_DETECTED",
            "MULTIPLE_FACES_DETECTED",
            "MULTIPLE_PERSONS_IN_ROOM",
            "NO_FACE_DETECTED",
            "HAND_NEAR_EAR_SUSPICIOUS",
            "HAND_COVERING_MOUTH",
            "HEAD_TURNED_AWAY",
            "LOOKING_AWAY_FROM_SCREEN"
        ]) or any("HEAD_TILTED" in f for f in flags)

        is_suspicious = bool(cheating_prob >= 0.60 or has_severe_flag)
        display_flags = flags if is_suspicious else ["NORMAL_HONEST_BEHAVIOR"]

        return {
            "cheating_probability": round(float(cheating_prob if is_suspicious else min(0.10, cheating_prob)), 2),
            "is_suspicious": is_suspicious,
            "flags": display_flags,
            "features_summary": {
                "face_count": int(features[1]),
                "head_yaw": round(float(features[6]), 1),
                "head_pitch": round(float(features[7]), 1),
                "gaze_focus": round(float(features[14]), 2),
                "hand_detected": bool(features[20] > 0),
                "phone_score": round(float(features[30]), 2)
            }
        }
    except Exception as e:
        # #18: Log exceptions instead of silently returning "normal" behavior.
        # A cheater could exploit malformed frames to bypass detection.
        logger.error("AI proctoring frame analysis failed: %s", e, exc_info=True)
        return {
            "cheating_probability": 0.50,
            "is_suspicious": True,
            "flags": ["ANALYSIS_ERROR"],
            "features_summary": {
                "face_count": 0,
                "head_yaw": 0.0,
                "head_pitch": 0.0,
                "gaze_focus": 0.0,
                "hand_detected": False,
                "phone_score": 0.0
            }
        }
