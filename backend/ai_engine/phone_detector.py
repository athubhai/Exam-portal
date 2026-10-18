import os
import joblib
import cv2
import numpy as np
from sklearn.ensemble import RandomForestClassifier

MODEL_PATH = os.path.join(os.path.dirname(__file__), "phone_model.pkl")

class PhoneAndHandMLDetector:
    def __init__(self):
        self.model = self._load_or_train_model()

    def _train_dataset(self):
        """Train a specialized Random Forest model on geometric & visual smartphone properties."""
        np.random.seed(42)
        X = []
        y = []

        # Class 0: Non-phone objects (3,000 samples)
        # Background objects, curved shirts, curtains, shoulders, round items, desk clutter
        for _ in range(3000):
            ar = np.random.uniform(0.6, 4.5)
            sol = np.random.uniform(0.25, 0.70) # Low solidity (irregular curves)
            ext = np.random.uniform(0.15, 0.58) # Low rectangular extent
            area = np.random.uniform(0.003, 0.35)
            elev = np.random.uniform(0.70, 0.99) # Resting down on desk
            unif = np.random.uniform(0.10, 0.55)
            X.append([ar, sol, ext, area, elev, unif])
            y.append(0)

        # Class 1: Active Smartphone in hand (2,500 samples)
        # Phones held in hand with fingers occluding bezel: aspect ratio ~1.35 to 2.8, solidity ~0.65 to 0.98
        for _ in range(2500):
            ar = np.random.normal(1.90, 0.28)    # Smartphone aspect ratio ~1.35 to 2.8
            sol = np.random.uniform(0.66, 0.98)   # Solid boundary with slight finger cutouts
            ext = np.random.uniform(0.55, 0.96)   # Fills bounding box like a rectangle
            area = np.random.uniform(0.006, 0.24) # Occupies 0.6% to 24% of webcam frame
            elev = np.random.uniform(0.15, 0.82)  # Raised in front of webcam/chest/ear
            unif = np.random.uniform(0.52, 0.98)  # Flat uniform glass/metal surface
            X.append([ar, sol, ext, area, elev, unif])
            y.append(1)

        X = np.array(X)
        y = np.array(y)

        clf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=12)
        clf.fit(X, y)
        return clf

    def _load_or_train_model(self):
        clf = self._train_dataset()
        try:
            joblib.dump(clf, MODEL_PATH)
        except Exception:
            pass
        return clf

    def detect(self, frame: np.ndarray, gray: np.ndarray, face_box: tuple, detected_hands: list = None) -> tuple[float, float, list[str]]:
        """
        Runs ML inference to detect handheld smartphones.
        Requires candidate objects to be physically correlated with an active, elevated hand.
        Furniture, chair edges, and background walls are completely filtered out.
        Returns: (phone_detected_0_or_1, phone_confidence, list_of_flags)
        """
        h, w = frame.shape[:2]
        frame_area = float(h * w)
        flags = []
        max_phone_prob = 0.0

        # If no detected hands are passed, detect hands using YCrCb skin segmentation
        if not detected_hands:
            ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
            skin_mask = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))
            if face_box:
                fx, fy, fw, fh = face_box
                x1, y1 = max(0, fx - 15), max(0, fy - 15)
                x2, y2 = min(w, fx + fw + 15), min(h, fy + fh + int(fh * 0.4))
                skin_mask[y1:y2, x1:x2] = 0

            detected_hands = []
            cnts, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for sc in cnts:
                if cv2.contourArea(sc) > (frame_area * 0.008):
                    hx, hy, hw, hh = cv2.boundingRect(sc)
                    detected_hands.append({
                        "center": (float(hx + hw / 2), float(hy + hh / 2)),
                        "box": (hx, hy, hw, hh),
                        "elevated": bool((hy + hh / 2) < (h * 0.76))
                    })

        elevated_hands = [hd for hd in detected_hands if hd.get("elevated", False)]
        if not elevated_hands:
            # Candidate hands are resting on desk/keyboard: zero phone risk
            return 0.0, 0.0, []

        # 2. Extract contours in proximity to elevated hands
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 35, 135)

        for eh in elevated_hands:
            hx, hy = eh["center"]
            # Search window around the elevated hand (includes hand grip and device)
            search_r = int(w * 0.26)
            sx1 = max(0, int(hx - search_r))
            sy1 = max(int(h * 0.12), int(hy - search_r))
            sx2 = min(w, int(hx + search_r))
            sy2 = min(h, int(hy + search_r))

            hand_roi = edges[sy1:sy2, sx1:sx2]
            if hand_roi.size == 0:
                continue

            obj_cnts, _ = cv2.findContours(hand_roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in obj_cnts:
                area = cv2.contourArea(cnt)
                # Sensitive range: from 0.6% to 25% of frame (detects phones near or far)
                if (frame_area * 0.006) < area < (frame_area * 0.25):
                    xr_rel, yr_rel, wr, hr = cv2.boundingRect(cnt)
                    xr = xr_rel + sx1
                    yr = yr_rel + sy1

                    if face_box:
                        fx, fy, fw, fh = face_box
                        if (xr < fx + fw and xr + wr > fx and yr < fy + fh and yr + hr > fy):
                            continue

                    aspect_ratio = max(wr, hr) / float(min(wr, hr) + 1e-5)
                    # Covers all smartphone proportions (vertical, horizontal, tilted)
                    if 1.30 <= aspect_ratio <= 3.4:
                        hull = cv2.convexHull(cnt)
                        solidity = min(1.0, float(area / (cv2.contourArea(hull) + 1e-5)))
                        extent = min(1.0, float(area / (wr * hr + 1e-5)))

                        # Tolerant to fingers gripping phone bezel
                        if solidity > 0.64 and extent > 0.54:
                            rel_area = float(area / frame_area)
                            elevation = float(yr / float(h))
                            roi_patch = gray[yr:yr+hr, xr:xr+wr]
                            unif = 0.70
                            if roi_patch.size > 0:
                                std_dev = float(np.std(roi_patch))
                                unif = max(0.0, min(1.0, 1.0 - (std_dev / 140.0)))

                            feat_vec = np.array([[
                                aspect_ratio, solidity, extent, rel_area, elevation, unif
                            ]])
                            prob = float(self.model.predict_proba(feat_vec)[0][1])
                            if prob > max_phone_prob:
                                max_phone_prob = prob

        phone_detected = 1.0 if max_phone_prob >= 0.58 else 0.0
        if phone_detected:
            flags.append("PHONE_DEVICE_DETECTED")
            flags.append("HAND_HOLDING_PHONE")

        return phone_detected, round(max_phone_prob, 3), flags

phone_ml_detector = PhoneAndHandMLDetector()
