import os
import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

MODEL_PATH = os.path.join(os.path.dirname(__file__), "proctoring_model.pkl")

# 37 feature column names corresponding to Mendeley Dataset modules
FEATURE_NAMES = [
    # Module 1: Face Detection (6 features)
    "face_detected", "face_count", "face_confidence", "face_bbox_area", "face_center_x", "face_center_y",
    # Module 2: Head Pose (6 features)
    "head_yaw", "head_pitch", "head_roll", "yaw_deviation", "pitch_deviation", "roll_deviation",
    # Module 3: Eye Gaze Tracking (8 features)
    "gaze_horizontal", "gaze_vertical", "gaze_screen_focus", "blink_count", 
    "left_eye_openness", "right_eye_openness", "gaze_deviation", "saccade_rate",
    # Module 4: Hand Tracking (9 features)
    "hand_detected", "hand_count", "hand_near_face", "hand_near_ear", "hand_near_pocket", 
    "hand_movement_speed", "hand_obscuring_mouth", "both_hands_visible", "keyboard_typing_heuristic",
    # Module 5: Mobile Phone & Device Detection (8 features)
    "phone_detected", "phone_confidence", "device_screen_glow", "reflective_surface_score",
    "audio_whisper_score", "secondary_person_presence", "tab_switch_flag", "mouth_movement_talking"
]

class ProctoringClassifier:
    def __init__(self):
        self.model = None
        self.feature_names = FEATURE_NAMES
        self.load_or_train_model()

    def generate_synthetic_mendeley_dataset(self, n_samples=5500, random_state=42):
        """
        Generates a synthetic 5,500 sample dataset with 37 features that simulates
        the distribution and structure of the Mendeley Exam Proctoring Suspicious
        Behaviours Dataset (DOI: 10.17632/39xs8th543.1).
        
        NOTE: This is a SYNTHETIC SIMULATION, not trained on the actual Mendeley data.
        The feature distributions are modeled to approximate real exam proctoring
        scenarios with a roughly balanced class split (52% normal, 48% suspicious).
        For production deployment, replace with actual dataset loading.
        """
        np.random.seed(random_state)
        # Roughly balanced 52% normal (0), 48% suspicious (1)
        labels = np.random.choice([0, 1], size=n_samples, p=[0.52, 0.48])
        X = np.zeros((n_samples, len(self.feature_names)))

        for i, label in enumerate(labels):
            if label == 0:  # Normal honest behavior
                # Face
                face_detected = 1.0 if np.random.rand() > 0.015 else 0.0 # 1.5% momentary occlusion/lighting flicker
                face_count = 1.0 if face_detected else 0.0
                face_confidence = np.random.uniform(0.82, 0.98) if face_detected else 0.0
                face_bbox_area = np.random.uniform(0.10, 0.26) if face_detected else 0.0
                face_center_x = np.random.normal(0.50, 0.035)
                face_center_y = np.random.normal(0.46, 0.040)
                # Head pose (angles in degrees, near 0 with natural posture drift)
                head_yaw = np.random.normal(0, 8.5)
                head_pitch = np.random.normal(-5, 7.5) # Natural downward tilt toward keyboard/screen
                head_roll = np.random.normal(0, 3.5)
                yaw_dev = abs(head_yaw) / 90.0
                pitch_dev = abs(head_pitch) / 90.0
                roll_dev = abs(head_roll) / 90.0
                # Gaze (normal reading saccades and screen scan)
                gaze_h = np.random.normal(0, 0.16)
                gaze_v = np.random.normal(-0.06, 0.14)
                gaze_focus = np.clip(1.0 - np.sqrt(gaze_h**2 + gaze_v**2) + np.random.normal(0, 0.05), 0.55, 0.99)
                blink_count = np.random.uniform(10, 24)
                left_eye = np.random.uniform(0.65, 0.95)
                right_eye = np.random.uniform(0.65, 0.95)
                gaze_dev = np.sqrt(gaze_h**2 + gaze_v**2)
                saccade = np.random.uniform(0.8, 3.6)
                # Hands: normal benign gestures (scratching nose, adjusting glasses, chin rest 8% of the time)
                hand_det = np.random.choice([0, 1], p=[0.60, 0.40])
                hand_cnt = 1.0 if hand_det else 0.0
                is_adjusting_glasses = (hand_det and np.random.rand() < 0.15)
                hand_face = np.random.uniform(0.20, 0.65) if is_adjusting_glasses else np.random.uniform(0.0, 0.20)
                hand_ear = np.random.uniform(0.10, 0.35) if is_adjusting_glasses else np.random.uniform(0.0, 0.10)
                hand_pocket = np.random.uniform(0.0, 0.06)
                hand_speed = np.random.uniform(0.02, 0.40)
                hand_mouth = np.random.uniform(0.15, 0.45) if is_adjusting_glasses else np.random.uniform(0.0, 0.12)
                both_hands = np.random.choice([0, 1], p=[0.70, 0.30])
                typing = np.random.uniform(0.10, 0.88)
                # Phone / Device (clean desk, rare background edge reflection)
                phone_det = 1.0 if np.random.rand() < 0.025 else 0.0 # 2.5% false contour on dark clutter/reflection
                phone_conf = np.random.uniform(0.18, 0.45) if phone_det else np.random.uniform(0.0, 0.15)
                screen_glow = np.random.uniform(0.0, 0.28)
                reflect_score = np.random.uniform(0.0, 0.25)
                whisper = np.random.uniform(0.0, 0.28)
                secondary_person = 1.0 if np.random.rand() < 0.015 else 0.0 # 1.5% false face detector trigger on background
                tab_switch = 1.0 if np.random.rand() < 0.02 else 0.0
                mouth_talking = np.random.uniform(0.0, 0.30)
            else:  # Suspicious / Cheating behavior
                anomaly_type = np.random.choice(["phone", "gaze_away", "head_turn", "multiple_people", "mouth_talk"], p=[0.30, 0.25, 0.20, 0.10, 0.15])
                face_detected = np.random.choice([1.0, 0.0], p=[0.92, 0.08])
                face_count = np.random.choice([0.0, 1.0, 2.0], p=[0.05, 0.45, 0.50]) if anomaly_type == "multiple_people" else (1.0 if face_detected else 0.0)
                face_confidence = np.random.uniform(0.50, 0.95) if face_detected else 0.0
                face_bbox_area = np.random.uniform(0.08, 0.32) if face_detected else 0.0
                face_center_x = np.random.uniform(0.20, 0.80)
                face_center_y = np.random.uniform(0.25, 0.72)
                # Head pose with varying degrees of subtlety
                if anomaly_type == "head_turn":
                    head_yaw = np.random.choice([-1, 1]) * np.random.uniform(18.0, 50.0)
                else:
                    head_yaw = np.random.normal(0, 12.0)
                head_pitch = np.random.uniform(-28, 18) if anomaly_type in ("phone", "gaze_away") else np.random.normal(-5, 9)
                head_roll = np.random.normal(0, 7.0)
                yaw_dev = abs(head_yaw) / 90.0
                pitch_dev = abs(head_pitch) / 90.0
                roll_dev = abs(head_roll) / 90.0
                # Gaze
                if anomaly_type == "gaze_away":
                    gaze_h = np.random.choice([-1, 1]) * np.random.uniform(0.25, 0.70)
                    gaze_v = np.random.uniform(0.20, 0.60)
                else:
                    gaze_h = np.random.normal(0, 0.20)
                    gaze_v = np.random.normal(0, 0.18)
                gaze_focus = np.clip(1.0 - np.sqrt(gaze_h**2 + gaze_v**2) + np.random.normal(0, 0.08), 0.05, 0.75)
                blink_count = np.random.uniform(4, 36)
                left_eye = np.random.uniform(0.60, 0.95)
                right_eye = np.random.uniform(0.60, 0.95)
                gaze_dev = np.sqrt(gaze_h**2 + gaze_v**2)
                saccade = np.random.uniform(1.2, 4.0) if anomaly_type == "gaze_away" else np.random.uniform(0.8, 3.2)
                # Hands: normal baseline hands unless anomaly involves hands/phone
                has_active_hand = anomaly_type in ("phone", "mouth_talk") or (np.random.rand() < 0.35)
                hand_det = 1.0 if has_active_hand else (1.0 if np.random.rand() < 0.40 else 0.0)
                hand_cnt = np.random.choice([1.0, 2.0], p=[0.55, 0.45]) if hand_det else 0.0
                hand_face = np.random.uniform(0.35, 0.85) if anomaly_type in ("phone", "mouth_talk") else np.random.uniform(0.0, 0.25)
                hand_ear = np.random.uniform(0.40, 0.90) if (anomaly_type == "phone" and np.random.rand() > 0.35) else np.random.uniform(0.0, 0.12)
                hand_pocket = np.random.uniform(0.0, 0.08)
                hand_speed = np.random.uniform(0.20, 0.75) if has_active_hand else np.random.uniform(0.02, 0.40)
                hand_mouth = np.random.uniform(0.40, 0.90) if anomaly_type == "mouth_talk" else np.random.uniform(0.0, 0.15)
                both_hands = 1.0 if hand_cnt >= 2 else 0.0
                typing = np.random.uniform(0.10, 0.85)
                # Phone / Device
                is_phone_cheat = (anomaly_type == "phone")
                phone_det = 1.0 if (is_phone_cheat and np.random.rand() > 0.12) else (1.0 if np.random.rand() < 0.03 else 0.0)
                phone_conf = np.random.uniform(0.55, 0.94) if phone_det else np.random.uniform(0.0, 0.20)
                screen_glow = np.random.uniform(0.35, 0.85) if phone_det else np.random.uniform(0.0, 0.25)
                reflect_score = np.random.uniform(0.30, 0.80) if phone_det else np.random.uniform(0.0, 0.22)
                whisper = np.random.uniform(0.40, 0.88) if anomaly_type == "mouth_talk" else np.random.uniform(0.0, 0.25)
                secondary_person = 1.0 if anomaly_type == "multiple_people" else (1.0 if np.random.rand() < 0.015 else 0.0)
                tab_switch = np.random.choice([0.0, 1.0], p=[0.75, 0.25])
                mouth_talking = np.random.uniform(0.50, 0.92) if anomaly_type == "mouth_talk" else np.random.uniform(0.0, 0.25)

            X[i] = [
                face_detected, face_count, face_confidence, face_bbox_area, face_center_x, face_center_y,
                head_yaw, head_pitch, head_roll, yaw_dev, pitch_dev, roll_dev,
                gaze_h, gaze_v, gaze_focus, blink_count, left_eye, right_eye, gaze_dev, saccade,
                hand_det, hand_cnt, hand_face, hand_ear, hand_pocket, hand_speed, hand_mouth, both_hands, typing,
                phone_det, phone_conf, screen_glow, reflect_score, whisper, secondary_person, tab_switch, mouth_talking
            ]

        return X, labels

    def train_and_save(self, save_path=MODEL_PATH):
        """Train Random Forest model using Stratified 5-Fold Cross-Validation and save to disk"""
        X, y = self.generate_synthetic_mendeley_dataset(n_samples=5500)
        
        # 1. Perform Stratified 5-Fold Cross-Validation
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_folds = []
        for fold, (train_idx, val_idx) in enumerate(skf.split(X, y), 1):
            fold_clf = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42 + fold, n_jobs=-1)
            fold_clf.fit(X[train_idx], y[train_idx])
            val_pred = fold_clf.predict(X[val_idx])
            cv_folds.append({
                "fold": fold,
                "accuracy": float(accuracy_score(y[val_idx], val_pred)),
                "precision": float(precision_score(y[val_idx], val_pred, zero_division=0)),
                "recall": float(recall_score(y[val_idx], val_pred, zero_division=0)),
                "f1_score": float(f1_score(y[val_idx], val_pred, zero_division=0))
            })

        acc_vals = [f["accuracy"] for f in cv_folds]
        prec_vals = [f["precision"] for f in cv_folds]
        rec_vals = [f["recall"] for f in cv_folds]
        f1_vals = [f["f1_score"] for f in cv_folds]

        # 2. Fit final production model on full dataset
        clf = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
        clf.fit(X, y)

        metrics = {
            "accuracy": float(np.mean(acc_vals)),
            "precision": float(np.mean(prec_vals)),
            "recall": float(np.mean(rec_vals)),
            "f1_score": float(np.mean(f1_vals)),
            "cv_accuracy_mean": float(np.mean(acc_vals)),
            "cv_accuracy_std": float(np.std(acc_vals)),
            "cv_precision_mean": float(np.mean(prec_vals)),
            "cv_precision_std": float(np.std(prec_vals)),
            "cv_recall_mean": float(np.mean(rec_vals)),
            "cv_recall_std": float(np.std(rec_vals)),
            "cv_f1_mean": float(np.mean(f1_vals)),
            "cv_f1_std": float(np.std(f1_vals)),
            "cv_folds": cv_folds,
            "n_samples": len(X),
            "n_features": len(self.feature_names)
        }

        with open(save_path, "wb") as f:
            pickle.dump({"model": clf, "metrics": metrics, "features": self.feature_names}, f)

        self.model = clf
        self.metrics = metrics
        return metrics

    def load_or_train_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, "rb") as f:
                    data = pickle.load(f)
                    self.model = data["model"]
                    self.metrics = data.get("metrics", {})
                    return
            except Exception:
                pass
        self.train_and_save()

    def predict_probability(self, feature_vector: np.ndarray) -> float:
        """Predict cheating probability score (0.0 to 1.0)"""
        if self.model is None:
            self.load_or_train_model()
        
        vec = np.array(feature_vector).reshape(1, -1)
        # Class 1 probability (suspicious)
        prob = self.model.predict_proba(vec)[0][1]
        return float(round(prob, 4))

proctor_classifier = ProctoringClassifier()
