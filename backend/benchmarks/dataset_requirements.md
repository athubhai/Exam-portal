# Dataset Collection & Annotation Requirements for Empirical Proctoring Verification

This document specifies the rigorous data collection protocol required to empirically benchmark the multi-modal personalized proctoring system for peer-reviewed conference publication (IEEE TALE / EDUCON / ACM SAC).

---

## 1. Participant Cohort Specifications
To achieve statistical significance and satisfy reviewer scrutiny on demographic diversity:
- **Sample Size ($N$)**: Minimum $25\text{--}30$ human participants.
- **Session Duration**: $12\text{--}15$ minutes per mock exam session.
- **Demographic Balance**:
  - **Gender / Voice Pitch**: $\approx 50\%$ male, $50\%$ female (ensuring Resemblyzer voice embedding encoder generalizes across fundamental frequency ranges $F_0 \in [85\text{--}255\text{ Hz}]$).
  - **Skin Tone Diversity**: Representation across Fitzpatrick skin phototypes I through VI (evaluating lighting and facial landmark sensitivity).
  - **Vision Correction**: $\ge 30\%$ wearing eyeglasses (to test reflection and gaze/blink robustness).

---

## 2. Hardware & Environment Protocols
Participants should record under varying consumer-grade hardware to prove deployment viability:
- **Webcam Specifications**:
  - Resolution: Native $720\text{p}$ or $1080\text{p}$ downsampled to $640 \times 480$ at $15\text{--}30\text{ FPS}$.
  - Camera Placement: Standard laptop integrated webcams ($0^\circ\text{--}15^\circ$ elevation angle) and external USB webcams.
- **Audio / Microphone Specifications**:
  - Sample Rate: Native $44.1\text{ kHz}$ or $48\text{ kHz}$ downsampled to $16\text{ kHz}$ mono PCM WAV.
  - Hardware Variants: Integrated laptop microphone, wired headset, and wireless Bluetooth earbuds.
- **Acoustic Environment**:
  - Quiet indoor room ($< 35\text{ dB}$ ambient noise).
  - Background noise test trials (keyboard typing, computer fan noise, distant door closures).

---

## 3. Session Protocol & Staged Behavioral Scenarios
Each participant completes two sessions:

### Session 1: Completely Compliant (Negative Ground Truth, $Y=0$)
- Participant answers legitimate multiple-choice questions for 10 minutes.
- Allowed normal behaviors:
  - Reading questions silently with natural eye saccades
  - Momentarily resting chin on hand or adjusting eyeglasses
  - Shifting posture naturally in office chair
  - Thinking aloud / muttering to self in enrolled voice

### Session 2: Structured Violation Scenarios (Positive Ground Truth, $Y=1$)
Participants execute scripted violations with logged timestamp markers:
1. **Verbal Collaboration / Second Speaker**: An accomplice outside the webcam frame reads an answer aloud (staged at specific minute marks).
2. **Sustained Whispering**: Candidate whispers question numbers and options under their breath for $\ge 4$ seconds.
3. **Lateral Off-Screen Peeking**: Turning head $> 25^\circ$ left/right toward secondary monitor or notes.
4. **Downward Desk / Lap Phone Glances**: Looking down at a concealed smartphone beneath camera view.
5. **Elevated Hand Smartphone Usage**: Holding smartphone beside head or ear.
6. **Gradual Baseline Drift**: Slowly turning torso and head $\approx 1^\circ\text{--}2^\circ$ per minute away from the display.

---

## 4. Ground-Truth Annotation Schema (`annotations.json`)
Every recorded video and audio stream must be annotated with millisecond-accurate interval labels:

```json
{
  "session_id": "STUDENT_014_SESSION_B",
  "subject_metadata": {
    "gender": "Female",
    "glasses": true,
    "mic_type": "Integrated_Laptop",
    "fitzpatrick_scale": "IV"
  },
  "calibration": {
    "video_start_sec": 0.0,
    "video_end_sec": 30.0,
    "audio_phrase_enrolled": true,
    "phrase_audio_file": "audio/sub_014_enroll.wav"
  },
  "ground_truth_events": [
    {
      "start_sec": 74.5,
      "end_sec": 82.0,
      "violation_class": "SECOND_VOICE_DETECTED",
      "actor": "External_Collaborator",
      "description": "Second person speaks from behind door asking question 4"
    },
    {
      "start_sec": 142.0,
      "end_sec": 149.2,
      "violation_class": "HEAD_TURNED_AWAY",
      "actor": "Candidate",
      "description": "Head turned 32 degrees left reading notes on wall"
    },
    {
      "start_sec": 210.0,
      "end_sec": 216.5,
      "violation_class": "SUSTAINED_WHISPERING",
      "actor": "Candidate",
      "description": "Low-volume whispering reading answer choices"
    },
    {
      "start_sec": 300.0,
      "end_sec": 420.0,
      "violation_class": "BASELINE_DRIFT_ANOMALY",
      "actor": "Candidate",
      "description": "Gradual posture shift from 0 deg to 18 deg over 2 minutes"
    }
  ]
}
```

---

## 5. Metrics to Report in Paper
With this labeled corpus collected, execute `backend/benchmarks/benchmark_personalized_fused.py` against the real recordings to report:
1. **Three-Way Ablation Table**:
   - Variant A (Legacy Static Global Thresholds)
   - Variant B (Personalized Video Baseline)
   - Variant C (Full Fused Multi-Modal: Personalized Video + Voice Biometrics)
2. **False Positive Rate (FPR) on Compliant Sessions**: Proving personalized calibration drops benign false alarms (adjusting glasses, resting chin) toward zero.
3. **Statistical Method Comparison**: $F_1$-score of Z-score thresholding vs. per-student Isolation Forest.
4. **Resemblyzer Cosine Separation**: Distribution histogram of same-speaker vs. second-speaker cosine similarities.
