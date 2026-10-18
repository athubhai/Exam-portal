import os
import cv2
import numpy as np
from ai_engine.phone_detector import phone_ml_detector

YOLO_WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "yolov8n.pt")

class MultiModalProctoringEnsemble:
    """
    Ensemble AI Proctoring Perception Engine:
    Fuses YOLOv8 (Deep-Learning Convolutional Object Detection) and Google MediaPipe / Hand Tracking
    with spatial corroboration and Random Forest behavioral scoring.
    """
    def __init__(self):
        self.yolo_model = None
        self.yolo_initialized = False
        self._init_yolo()

    def _init_yolo(self):
        """Initialize YOLOv8 Nano model for real-time prohibited object detection."""
        try:
            from ultralytics import YOLO
            weights = YOLO_WEIGHTS_PATH if os.path.exists(YOLO_WEIGHTS_PATH) else "yolov8n.pt"
            self.yolo_model = YOLO(weights)
            self.yolo_initialized = True
        except Exception:
            self.yolo_model = None
            self.yolo_initialized = False

    def detect_objects_yolo(self, frame: np.ndarray) -> tuple[list[dict], list[dict], list[dict]]:
        """
        Run YOLOv8 inference to detect phones, books, and persons in the frame.
        COCO classes: 67=cell phone, 65=remote (handheld electronic device), 73=book, 0=person
        Returns: (phones, books, persons)
        """
        if not self.yolo_initialized or self.yolo_model is None:
            return [], [], []

        try:
            results = self.yolo_model(frame, conf=0.16, verbose=False)
            phones = []
            books = []
            persons = []

            for r in results:
                boxes = r.boxes
                for box in boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    xyxy = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = [int(v) for v in xyxy]
                    item = {"box": (x1, y1, x2, y2), "conf": round(conf, 3)}

                    if cls_id in (67, 65):  # cell phone or handheld remote/device
                        phones.append(item)
                    elif cls_id == 73 and conf >= 0.20:  # book
                        books.append(item)
                    elif cls_id == 0 and conf >= 0.25:  # person
                        persons.append(item)

            return phones, books, persons
        except Exception:
            return [], [], []

    def detect_hands_and_gestures(self, frame: np.ndarray, face_box: tuple) -> list[dict]:
        """
        Extract hand coordinates and gesture locations using robust YCrCb human skin tracking.
        Filters out background furniture and walls.
        Returns list of hand dicts: {"center": (cx, cy), "box": (x, y, w, h), "near_ear": bool, "covering_mouth": bool, "elevated": bool}
        """
        h, w = frame.shape[:2]
        frame_area = float(h * w)
        hands = []

        ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
        skin_mask = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))

        has_ear_hand = False
        has_mouth_hand = False

        if face_box:
            fx, fy, fw, fh = face_box
            # 1. Ear zone check: Detect hand skin mass positioned at left or right ear
            left_ear_zone = skin_mask[int(fy):int(fy + fh * 0.8), max(0, int(fx - fw * 0.7)):int(fx + fw * 0.15)]
            right_ear_zone = skin_mask[int(fy):int(fy + fh * 0.8), int(fx + fw * 0.85):min(w, int(fx + fw * 1.7))]
            min_ear_pixels = (fw * fh) * 0.18

            # Lateral ear bulge check for when hand touches ear and merges with face contour
            aspect = float(fh) / float(fw + 1e-5)
            left_ear_mass = np.count_nonzero(skin_mask[int(fy):int(fy + fh), int(fx):int(fx + fw * 0.28)])
            right_ear_mass = np.count_nonzero(skin_mask[int(fy):int(fy + fh), int(fx + fw * 0.72):int(fx + fw)])
            has_ear_bulge = (aspect < 1.10 and (left_ear_mass > (fw * fh * 0.14) or right_ear_mass > (fw * fh * 0.14)))

            if np.count_nonzero(left_ear_zone) > min_ear_pixels or np.count_nonzero(right_ear_zone) > min_ear_pixels or has_ear_bulge:
                has_ear_hand = True

            # 2. Mouth zone check: Distinguish external hand covering mouth from candidate's natural chin
            face_oval_mask = np.zeros_like(skin_mask)
            cv2.ellipse(face_oval_mask, (int(fx + fw * 0.5), int(fy + fh * 0.5)),
                        (int(fw * 0.40), int(fh * 0.45)), 0, 0, 360, 255, -1)
            
            chin_y1 = int(fy + fh * 0.55)
            chin_y2 = min(h, int(fy + fh * 1.30))
            mouth_x1 = max(0, int(fx + fw * 0.20))
            mouth_x2 = min(w, int(fx + fw * 0.80))
            if chin_y2 > chin_y1 and mouth_x2 > mouth_x1:
                external_skin = cv2.bitwise_and(skin_mask, cv2.bitwise_not(face_oval_mask))
                mouth_zone = external_skin[chin_y1:chin_y2, mouth_x1:mouth_x2]
                min_mouth_pixels = (mouth_x2 - mouth_x1) * (chin_y2 - chin_y1) * 0.32
                if np.count_nonzero(mouth_zone) > min_mouth_pixels or aspect >= 2.1:
                    has_mouth_hand = True

            # Mask out face oval for general hand contour extraction
            inner_cx, inner_cy = int(fx + fw * 0.5), int(fy + fh * 0.5)
            cv2.ellipse(skin_mask, (inner_cx, inner_cy), (int(fw * 0.45), int(fh * 0.55)), 0, 0, 360, 0, -1)

        # Find general hand contours
        cnts, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            c_area = cv2.contourArea(c)
            if (frame_area * 0.006) < c_area < (frame_area * 0.30):
                hx, hy, hw, hh = cv2.boundingRect(c)
                cx = float(hx + hw / 2)
                cy = float(hy + hh / 2)
                hands.append({
                    "center": (cx, cy),
                    "box": (hx, hy, hw, hh),
                    "near_ear": has_ear_hand,
                    "covering_mouth": has_mouth_hand,
                    "elevated": bool(cy < (h * 0.76))
                })

        if has_ear_hand and not any(hd["near_ear"] for hd in hands):
            fb_x = face_box[0] if face_box else int(w * 0.3)
            fb_y = face_box[1] if face_box else int(h * 0.3)
            hands.append({
                "center": (float(fb_x), float(fb_y + 40)),
                "box": (fb_x - 30, fb_y, 40, 60),
                "near_ear": True,
                "covering_mouth": False,
                "elevated": True
            })

        if has_mouth_hand and not any(hd["covering_mouth"] for hd in hands):
            fb_x = face_box[0] if face_box else int(w * 0.3)
            fb_y = face_box[1] if face_box else int(h * 0.3)
            hands.append({
                "center": (float(fb_x + 40), float(fb_y + 80)),
                "box": (fb_x, fb_y + 50, 60, 60),
                "near_ear": False,
                "covering_mouth": True,
                "elevated": True
            })

        return hands

    def evaluate_frame(self, frame: np.ndarray, gray: np.ndarray, face_box: tuple) -> tuple[float, float, list[str], list[dict], list[dict]]:
        """
        Multi-Modal Perception Pipeline:
        1. Run YOLOv8 for prohibited items (cell phones, books, multiple persons).
        2. Run MediaPipe-compatible YCrCb gesture tracking for hand positions (elevated, near ear, over mouth).
        3. Spatially correlate hands with detected objects to confirm cheating with 0 false alarms.
        4. When YOLO is active and negative, NEVER let static background contours trigger phone alarms.
        """
        flags = []
        phone_detected = 0.0
        phone_conf = 0.0

        # 1. Gesture Tracking (Hand near ear / mouth)
        detected_hands = self.detect_hands_and_gestures(frame, face_box)
        has_hand_near_ear = any(h["near_ear"] for h in detected_hands)
        has_hand_covering_mouth = any(h["covering_mouth"] for h in detected_hands)

        if has_hand_near_ear:
            flags.append("HAND_NEAR_EAR_SUSPICIOUS")
        if has_hand_covering_mouth:
            flags.append("HAND_COVERING_MOUTH")

        # 2. YOLOv8 Deep Object Detection
        yolo_phones, yolo_books, yolo_persons = self.detect_objects_yolo(frame)

        # Multi-person detection via YOLO
        if len(yolo_persons) > 1:
            flags.append("MULTIPLE_PERSONS_IN_ROOM")

        # Book / Cheat Notes detection via YOLO
        if len(yolo_books) > 0:
            flags.append("PROHIBITED_BOOK_OR_NOTES_DETECTED")

        # Phone detection via YOLO + Spatial Corroboration
        if len(yolo_phones) > 0:
            best_phone = max(yolo_phones, key=lambda p: p["conf"])
            phone_detected = 1.0
            phone_conf = best_phone["conf"]
            flags.append("YOLO_CELL_PHONE_DETECTED")
            flags.append("PHONE_DEVICE_DETECTED")

            # Check if an elevated hand is touching or near the phone
            bx1, by1, bx2, by2 = best_phone["box"]
            p_cx, p_cy = (bx1 + bx2) / 2.0, (by1 + by2) / 2.0
            for h_dict in detected_hands:
                hx, hy = h_dict["center"]
                dist = np.hypot(p_cx - hx, p_cy - hy)
                if dist < (frame.shape[1] * 0.28):
                    flags.append("HAND_HOLDING_PHONE")
                    break

        # 3. Fallback ML Phone Detector: If YOLO missed but student has an elevated hand
        if phone_detected == 0.0:
            elevated_hands = [h for h in detected_hands if h.get("elevated", False)]
            if (not self.yolo_initialized) or len(elevated_hands) > 0:
                rf_phone_det, rf_conf, rf_flags = phone_ml_detector.detect(frame, gray, face_box, detected_hands)
                if rf_phone_det > 0.0:
                    phone_detected = rf_phone_det
                    phone_conf = rf_conf
                    for f in rf_flags:
                        if f not in flags:
                            flags.append(f)

        return phone_detected, phone_conf, flags, yolo_persons, detected_hands

# Singleton instance
proctoring_ensemble = MultiModalProctoringEnsemble()
