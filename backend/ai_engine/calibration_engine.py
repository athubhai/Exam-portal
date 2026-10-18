import time
import numpy as np
from sklearn.ensemble import IsolationForest
from ai_engine.audio_engine import audio_engine

# Randomized verification phrases for audio voice enrollment
VERIFICATION_PHRASES = [
    "I verify that I am sitting at my desk taking this examination independently and honestly in a quiet room.",
    "Academic integrity is essential, and I confirm my identity and compliance for this proctored evaluation.",
    "I agree to adhere to all university examination rules and maintain full concentration on my monitor.",
    "My workspace is clear of unauthorized devices, notes, or secondary assistance for the duration of this exam."
]

class StudentSessionBaseline:
    """
    Per-student baseline profile:
    - Video: Pose & facial biometrics calibrated per candidate
    - Audio: Resemblyzer voice embedding locked for duration of session
    """
    def __init__(self, session_id: str, user_id: int | None = None):
        self.session_id = session_id
        self.user_id = user_id
        self.created_at = time.time()

        # Calibration state
        self.video_calibrated = False
        self.audio_enrolled = False
        self.calibration_samples = []  # List of [yaw, pitch, blink_rate, cx, cy]

        # Video Baseline Parameters
        self.mean_vector = None         # Current EWMA mean
        self.initial_mean_vector = None # Preserved anchor to detect gradual cheating drift
        self.std_vector = None
        # Floor std values to prevent division-by-near-zero for very still students
        # [yaw: 2.5 deg, pitch: 2.0 deg, blink: 1.2, cx: 0.025, cy: 0.025]
        self.floor_std = np.array([2.5, 2.0, 1.2, 0.025, 0.025], dtype=np.float32)
        self.isolation_forest = None

        # Continuous drift tracking
        self.last_drift_check_time = time.time()
        self.baseline_history = []
        self.max_drift_per_min = 5.0  # Max 5 degrees or 0.04 centroid drift per minute

        # Audio Baseline Parameters
        self.voice_embedding = None
        self.verification_phrase = None
        self.whisper_history_sec = 0.0

    def add_calibration_sample(self, yaw: float, pitch: float, blink_rate: float, cx: float, cy: float):
        """Add a frame's geometric signals during the 30-60s calibration window."""
        vec = [float(yaw), float(pitch), float(blink_rate), float(cx), float(cy)]
        self.calibration_samples.append(vec)

    def finalize_video_calibration(self) -> dict:
        """
        Compute initial statistical baseline and fit candidate's Isolation Forest.
        Returns calibration summary.
        """
        if len(self.calibration_samples) < 15:
            # Fallback if too few samples
            return {
                "success": False,
                "samples_count": len(self.calibration_samples),
                "error": "Insufficient video samples. Fallback to global thresholds active."
            }

        data = np.array(self.calibration_samples, dtype=np.float32)
        self.mean_vector = np.mean(data, axis=0)
        self.initial_mean_vector = np.copy(self.mean_vector)
        self.std_vector = np.std(data, axis=0)

        # Train personalized Isolation Forest on candidate's calibration distribution
        try:
            iso = IsolationForest(n_estimators=60, contamination=0.05, random_state=42)
            iso.fit(data)
            self.isolation_forest = iso
        except Exception as e:
            self.isolation_forest = None
            print(f"[Calibration] Isolation Forest train error: {e}")

        self.video_calibrated = True
        self.last_drift_check_time = time.time()

        return {
            "success": True,
            "samples_count": len(data),
            "mean_yaw": round(float(self.mean_vector[0]), 2),
            "mean_pitch": round(float(self.mean_vector[1]), 2),
            "mean_cx": round(float(self.mean_vector[3]), 3),
            "mean_cy": round(float(self.mean_vector[4]), 3),
            "std_yaw": round(float(self.std_vector[0]), 2),
            "std_pitch": round(float(self.std_vector[1]), 2),
            "isolation_forest_trained": bool(self.isolation_forest is not None)
        }

    def enroll_audio_phrase(self, audio_payload, phrase_text: str | None = None) -> dict:
        """Enroll student's voice embedding during calibration."""
        res = audio_engine.enroll_voice_profile(audio_payload)
        if res.get("success", False) and res.get("embedding"):
            self.voice_embedding = res["embedding"]
            self.verification_phrase = phrase_text
            self.audio_enrolled = True
            return {
                "success": True,
                "duration_sec": res.get("duration_sec", 0.0),
                "embedding_dim": len(self.voice_embedding)
            }
        return {
            "success": False,
            "error": res.get("error", "Audio enrollment failed.")
        }

    def score_video_frame(
        self,
        yaw: float,
        pitch: float,
        blink_rate: float,
        cx: float,
        cy: float,
        z_threshold: float = 2.8
    ) -> dict:
        """
        Evaluate frame against candidate's personalized baseline:
        - Computes z-score deviation per feature
        - Evaluates candidate's Isolation Forest anomaly score
        - Slowly updates EWMA baseline
        - Detects cumulative baseline drift velocity
        """
        current_vec = np.array([yaw, pitch, blink_rate, cx, cy], dtype=np.float32)

        # If not calibrated, return fallback uncalibrated status
        if not self.video_calibrated or self.mean_vector is None:
            return {
                "calibrated": False,
                "z_scores": [0.0] * 5,
                "max_z": 0.0,
                "z_anomaly": False,
                "if_anomaly": False,
                "drift_anomaly": False,
                "flags": []
            }

        # 1. Z-score deviation with variance floor
        effective_std = np.maximum(self.std_vector, self.floor_std)
        z_scores = (current_vec - self.mean_vector) / effective_std
        max_z = float(np.max(np.abs(z_scores)))
        z_anomaly = bool(max_z >= z_threshold)

        flags = []
        if z_anomaly:
            flags.append("PERSONALIZED_POSE_DEVIATION_ZSCORE")
            if abs(z_scores[0]) >= z_threshold:
                flags.append("HEAD_YAW_ANOMALY_FROM_BASELINE")
            if abs(z_scores[1]) >= z_threshold:
                flags.append("HEAD_PITCH_ANOMALY_FROM_BASELINE")

        # 2. Isolation Forest score
        if_anomaly = False
        if_score = 0.0
        if self.isolation_forest is not None:
            try:
                # -1 for outlier, 1 for inlier
                pred = self.isolation_forest.predict(current_vec.reshape(1, -1))[0]
                if_score = float(self.isolation_forest.decision_function(current_vec.reshape(1, -1))[0])
                if pred == -1:
                    if_anomaly = True
                    flags.append("ISOLATION_FOREST_BEHAVIORAL_OUTLIER")
            except Exception:
                pass

        # 3. Continuous Baseline Update (EWMA: 0.95 old + 0.05 new)
        # Updates slowly only when candidate is not in extreme anomaly
        now = time.time()
        if not z_anomaly:
            self.mean_vector = (0.95 * self.mean_vector) + (0.05 * current_vec)

        # 4. Drift Cap Detection (detects creeping gradual turns over minutes)
        drift_anomaly = False
        elapsed_min = max(0.1, (now - self.last_drift_check_time) / 60.0)
        yaw_drift = abs(self.mean_vector[0] - self.initial_mean_vector[0])
        pitch_drift = abs(self.mean_vector[1] - self.initial_mean_vector[1])
        centroid_drift = np.sqrt(
            (self.mean_vector[3] - self.initial_mean_vector[3]) ** 2 +
            (self.mean_vector[4] - self.initial_mean_vector[4]) ** 2
        )

        # If baseline itself shifts faster than 5 deg/min or 0.04 centroid/min
        drift_rate_deg = max(yaw_drift, pitch_drift) / elapsed_min
        if drift_rate_deg > self.max_drift_per_min or (centroid_drift / elapsed_min) > 0.05:
            drift_anomaly = True
            flags.append("BASELINE_DRIFT_ANOMALY")

        return {
            "calibrated": True,
            "z_scores": [round(float(z), 2) for z in z_scores],
            "max_z": round(max_z, 2),
            "z_anomaly": z_anomaly,
            "if_score": round(if_score, 3),
            "if_anomaly": if_anomaly,
            "drift_anomaly": drift_anomaly,
            "drift_rate_deg_per_min": round(float(drift_rate_deg), 2),
            "current_baseline_mean": [round(float(v), 2) for v in self.mean_vector],
            "flags": flags
        }

    def score_audio_chunk(self, audio_payload) -> dict:
        """Evaluate incoming audio chunk against enrolled voice embedding."""
        if not self.audio_enrolled or self.voice_embedding is None:
            return {
                "enrolled": False,
                "has_speech": False,
                "similarity": 1.0,
                "flags": []
            }

        res = audio_engine.evaluate_audio_chunk(
            audio_payload=audio_payload,
            enrolled_embedding=self.voice_embedding,
            whisper_history_sec=self.whisper_history_sec
        )
        self.whisper_history_sec = res.get("whisper_duration_sec", 0.0)
        res["enrolled"] = True
        return res


class ProctoringCalibrationManager:
    """Singleton session registry managing baselines across active exams."""
    def __init__(self):
        self._sessions: dict[str, StudentSessionBaseline] = {}

    def get_or_create_session(self, session_id: str, user_id: int | None = None) -> StudentSessionBaseline:
        if session_id not in self._sessions:
            self._sessions[session_id] = StudentSessionBaseline(session_id, user_id)
        return self._sessions[session_id]

    def get_session(self, session_id: str) -> StudentSessionBaseline | None:
        return self._sessions.get(session_id)

    def get_random_phrase(self) -> str:
        return np.random.choice(VERIFICATION_PHRASES)

calibration_manager = ProctoringCalibrationManager()
