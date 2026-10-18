import os
import io
import base64
import numpy as np
import soundfile as sf
import scipy.signal
import torch

try:
    from resemblyzer import VoiceEncoder, preprocess_wav
except ImportError:
    VoiceEncoder = None

class AudioProctoringEngine:
    """
    Audio Proctoring & Voice Biometrics Engine:
    - Enrolls student voice profile during calibration using Resemblyzer.
    - Evaluates rolling audio chunks for speech presence (Silero VAD).
    - Detects unauthorized secondary speakers via cosine similarity.
    - Detects sustained whispering and filters out transient noises.
    """
    def __init__(self):
        self.encoder = None
        self.vad_model = None
        self.get_speech_timestamps = None
        self._init_models()

    def _init_models(self):
        # 1. Initialize Resemblyzer VoiceEncoder
        if VoiceEncoder is not None:
            try:
                self.encoder = VoiceEncoder("cpu")
            except Exception as e:
                print(f"[AudioEngine] VoiceEncoder init error: {e}")
                self.encoder = None

        # 2. Initialize Silero VAD
        try:
            model, utils = torch.hub.load(
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                trust_repo=True
            )
            self.vad_model = model
            self.get_speech_timestamps = utils[0]
        except Exception as e:
            print(f"[AudioEngine] Silero VAD init error: {e}")
            self.vad_model = None
            self.get_speech_timestamps = None

    def decode_audio_payload(self, audio_payload) -> tuple[np.ndarray, int]:
        """
        Decode audio from base64 string, bytes, or numpy array.
        Returns: (1D float32 normalized audio array, sample_rate)
        """
        if isinstance(audio_payload, np.ndarray):
            audio = audio_payload.astype(np.float32)
            if audio.ndim > 1:
                audio = np.mean(audio, axis=1)
            return audio, 16000

        # If base64 string
        if isinstance(audio_payload, str):
            if "," in audio_payload:
                audio_payload = audio_payload.split(",", 1)[1]
            raw_bytes = base64.b64decode(audio_payload)
        elif isinstance(audio_payload, bytes):
            raw_bytes = audio_payload
        else:
            return np.zeros(16000, dtype=np.float32), 16000

        try:
            # Attempt to decode container format (WAV, OGG, WebM) via soundfile
            data, sr = sf.read(io.BytesIO(raw_bytes), dtype="float32")
            if data.ndim > 1:
                data = np.mean(data, axis=1)
            # Resample to 16kHz if needed
            if sr != 16000 and len(data) > 0:
                num_samples = int(len(data) * 16000 / sr)
                data = scipy.signal.resample(data, num_samples).astype(np.float32)
                sr = 16000
            return data, sr
        except Exception:
            # Fallback: assume raw 16-bit PCM mono audio
            try:
                pcm16 = np.frombuffer(raw_bytes, dtype=np.int16)
                data = (pcm16.astype(np.float32) / 32768.0)
                return data, 16000
            except Exception:
                return np.zeros(16000, dtype=np.float32), 16000

    def enroll_voice_profile(self, audio_payload) -> dict:
        """
        Extract 256-d voice embedding from student's verification phrase audio.
        Returns: {"success": bool, "embedding": list[float], "duration_sec": float, "error": str | None}
        """
        audio, sr = self.decode_audio_payload(audio_payload)
        duration = len(audio) / float(sr)

        # Require at least 1.0 second of audio
        if duration < 1.0 or np.max(np.abs(audio)) < 0.01:
            return {
                "success": False,
                "embedding": None,
                "duration_sec": round(duration, 2),
                "error": "Audio signal too short or silent for enrollment."
            }

        if self.encoder is None:
            # Fallback: compute 256-d spectral centroid/energy fingerprint
            fft_mag = np.abs(np.fft.rfft(audio))
            fingerprint = fft_mag[:256]
            norm = np.linalg.norm(fingerprint) + 1e-6
            embedding = (fingerprint / norm).tolist()
            return {
                "success": True,
                "embedding": embedding,
                "duration_sec": round(duration, 2),
                "error": None
            }

        try:
            # Preprocess and embed utterance
            wav = preprocess_wav(audio, sr)
            if len(wav) < 1600:
                wav = audio
            emb = self.encoder.embed_utterance(wav)
            # Ensure unit norm
            emb = emb / (np.linalg.norm(emb) + 1e-8)
            return {
                "success": True,
                "embedding": emb.tolist(),
                "duration_sec": round(duration, 2),
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "embedding": None,
                "duration_sec": round(duration, 2),
                "error": f"Voice embedding failed: {str(e)}"
            }

    def detect_speech_activity(self, audio: np.ndarray, sr: int = 16000) -> tuple[bool, float, list[dict]]:
        """
        Run Silero VAD on audio chunk.
        Returns: (has_speech, speech_duration_sec, speech_intervals)
        """
        if len(audio) == 0:
            return False, 0.0, []

        duration = len(audio) / float(sr)

        # If Silero VAD is available
        if self.vad_model is not None and self.get_speech_timestamps is not None:
            try:
                tensor_audio = torch.from_numpy(audio.copy())
                timestamps = self.get_speech_timestamps(tensor_audio, self.vad_model, sampling_rate=sr)
                total_speech_samples = sum((ts["end"] - ts["start"]) for ts in timestamps)
                speech_sec = total_speech_samples / float(sr)
                
                # Transient rejection: Ignore brief clicks / chair squeaks < 0.4s
                if speech_sec >= 0.40:
                    return True, round(speech_sec, 2), timestamps
            except Exception:
                pass

        # Energy & Zero-Crossing fallback VAD
        frame_size = int(sr * 0.03)  # 30ms frames
        hop_size = int(sr * 0.01)    # 10ms hop
        energies = []
        for i in range(0, len(audio) - frame_size, hop_size):
            frame = audio[i:i + frame_size]
            energies.append(np.sum(frame ** 2))

        if not energies:
            return False, 0.0, []

        energies = np.array(energies)
        speech_frames = np.sum(energies > 0.005)
        speech_sec = float(speech_frames * 0.01)
        has_speech = bool(speech_sec >= 0.40)
        return has_speech, round(speech_sec, 2), []

    def evaluate_audio_chunk(
        self,
        audio_payload,
        enrolled_embedding: list[float] | None = None,
        whisper_history_sec: float = 0.0,
        second_voice_threshold: float = 0.75
    ) -> dict:
        """
        Evaluate ongoing audio chunk:
        - Detects speech presence via VAD.
        - Compares speaker embedding against enrolled profile.
        - Identifies SECOND_VOICE_DETECTED or SUSTAINED_WHISPERING.
        """
        audio, sr = self.decode_audio_payload(audio_payload)
        duration = len(audio) / float(sr)
        flags = []
        similarity = 1.0

        if duration < 0.5:
            return {
                "has_speech": False,
                "speech_duration_sec": 0.0,
                "similarity": 1.0,
                "flags": [],
                "whisper_duration_sec": 0.0
            }

        # 1. Voice Activity Detection
        has_speech, speech_duration, _ = self.detect_speech_activity(audio, sr)
        rms = float(np.sqrt(np.mean(audio ** 2)))

        # 2. Whisper Detection
        # Low energy but active speech signals
        is_whispering_chunk = bool(has_speech and (0.008 <= rms <= 0.075))
        updated_whisper_sec = (whisper_history_sec + speech_duration) if is_whispering_chunk else max(0.0, whisper_history_sec - 1.0)
        if updated_whisper_sec >= 3.0:
            flags.append("SUSTAINED_WHISPERING")

        # 3. Speaker Verification (if enrolled profile is provided and speech is present)
        if has_speech and enrolled_embedding is not None and len(enrolled_embedding) > 0:
            try:
                enrolled_vec = np.array(enrolled_embedding, dtype=np.float32)
                enrolled_norm = np.linalg.norm(enrolled_vec)
                if enrolled_norm > 0:
                    enrolled_vec = enrolled_vec / enrolled_norm

                if self.encoder is not None:
                    wav = preprocess_wav(audio, sr)
                    if len(wav) < 1600:
                        wav = audio
                    chunk_emb = self.encoder.embed_utterance(wav)
                    chunk_norm = np.linalg.norm(chunk_emb)
                    if chunk_norm > 0:
                        chunk_emb = chunk_emb / chunk_norm
                    similarity = float(np.dot(chunk_emb, enrolled_vec))
                else:
                    # Fallback spectral cosine similarity
                    fft_mag = np.abs(np.fft.rfft(audio))[:len(enrolled_vec)]
                    norm = np.linalg.norm(fft_mag)
                    if norm > 0:
                        chunk_emb = fft_mag / norm
                        similarity = float(np.dot(chunk_emb, enrolled_vec))

                similarity = round(float(np.clip(similarity, 0.0, 1.0)), 3)

                # Check if voice does not match enrolled student
                if similarity < second_voice_threshold:
                    flags.append("SECOND_VOICE_DETECTED")
            except Exception as e:
                print(f"[AudioEngine] Speaker verification error: {e}")

        return {
            "has_speech": has_speech,
            "speech_duration_sec": speech_duration,
            "rms_amplitude": round(rms, 4),
            "similarity": similarity,
            "flags": flags,
            "whisper_duration_sec": round(updated_whisper_sec, 2)
        }

audio_engine = AudioProctoringEngine()
