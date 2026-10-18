# REVIEW 1: PROBLEM AND DESIGN

---

**Project Title:**
**Design and Implementation of a Secure Online Examination System with Multimodal AI Proctoring, Cryptographic Data Protection, and Real-Time WebSocket Telemetry**

**Academic Level:** B.Tech Pre-Final / Final Year Capstone Project
**Domain:** Artificial Intelligence, Computer Vision, Cybersecurity, and Distributed Web Systems
**Date:** September 2026

---

## 1. Problem Statement

The rapid adoption of online education and remote assessment has introduced critical vulnerabilities in digital examination systems that compromise academic integrity, data confidentiality, and proctor efficiency. Current online examination platforms suffer from the following fundamental problems:

1. **Academic Dishonesty in Unsupervised Environments:** Students taking remote exams can collaborate with peers, consult unauthorized materials, use secondary devices (smartphones, tablets), glance at off-screen physical notes, or have unauthorized persons take the exam on their behalf. Conventional proctoring relies on post-exam manual video review, which is labor-intensive, expensive, and incapable of real-time intervention.

2. **Plaintext Data Exposure and Insider Threats:** Most Learning Management Systems (LMS) such as Moodle and Canvas store examination question papers, correct answer keys, and student submissions in plaintext within relational databases. A single SQL injection attack, misconfigured database backup, or unauthorized database administrator access can compromise the entire examination integrity, leaking questions before the exam or altering grades after submission.

3. **Heavy Client-Side Computational Burden:** Existing commercial AI proctoring solutions (e.g., Proctorio, Respondus LockDown Browser) mandate intrusive desktop agents or resource-heavy local deep learning inference that causes thermal throttling, crashes on low-specification student hardware, and raises privacy concerns due to continuous screen/webcam recording.

4. **Absence of Real-Time Alerting:** Most proctoring tools only record raw video for post-exam forensic review. Faculty/examiners cannot intervene during the examination to warn or disqualify suspicious candidates in real time.

5. **Weak Identity and Access Management:** Basic password-based authentication without multi-factor verification and without strict server-side role-based access control leaves the system vulnerable to credential stuffing, brute-force attacks, and privilege escalation.

**This project addresses the problem of designing and implementing a unified, enterprise-grade online examination platform that simultaneously provides real-time multimodal AI-driven behavioral proctoring, zero-plaintext cryptographic data protection at rest, and defense-in-depth identity assurance — all while maintaining minimal client-side computational overhead.**

---

## 2. Objectives

The primary objectives of this project are:

| # | Objective | Measurable Target |
|---|-----------|-------------------|
| O1 | Design a multimodal AI proctoring engine that analyzes webcam frames across five behavioral modules (Face Detection, Head Pose, Eye Gaze, Hand Movement, Device Detection) | 37-dimensional feature vector with ≥ 85% classification accuracy on held-out test data |
| O2 | Implement zero-plaintext cryptographic data protection at rest for question papers, answer keys, and student submissions | AES-256 Fernet envelope encryption; direct SQL inspection reveals zero readable content |
| O3 | Build real-time WebSocket telemetry for sub-second push notification of suspicious proctoring events to faculty dashboards | Sub-200ms alert delivery latency from anomaly detection to faculty dashboard |
| O4 | Enforce strict server-side Role-Based Access Control (RBAC) with three discrete roles: Admin, Faculty, Student | HTTP 403 Forbidden on all cross-role access attempts; validated via automated test suite |
| O5 | Integrate RFC 6238 TOTP Multi-Factor Authentication compatible with standard authenticator applications | Successful TOTP enrollment, QR generation, and 6-digit code validation |
| O6 | Implement resilient exam state management with periodic autosave | 10-second interval delta autosave to prevent data loss during network interruptions |
| O7 | Maintain lightweight client-edge sampling to support low-specification student hardware | Edge capture at 320×240 resolution @ 0.25 Hz; all AI inference offloaded to server |

---

## 3. Scope

### 3.1 In Scope

- Full-stack web application with React (Vite) frontend and FastAPI backend
- Role-tailored portals for Admin, Faculty/Examiner, and Student
- AI proctoring engine with 5 behavioral analysis modules and Random Forest ensemble classifier
- AES-256 Fernet authenticated encryption for questions, answers, and submissions at rest
- Bidirectional WebSocket channels for real-time proctoring alert broadcasting
- RFC 6238 TOTP MFA with QR code provisioning
- Server-side RBAC via FastAPI dependency injection
- Automated objective exam grading with encrypted answer comparison
- Comprehensive audit logging of all administrative actions
- In-memory sliding-window rate limiting for brute-force protection
- Docker multi-container deployment (PostgreSQL, FastAPI, React)

### 3.2 Out of Scope

- Biometric face-recognition-based identity verification (planned for future work)
- Subjective/essay-type answer evaluation using NLP
- Audio-based spatial triangulation for off-screen voice detection
- WebAssembly edge inference acceleration
- Dynamic question shuffling and parameterized question templates
- Mobile native application (iOS/Android)
- Integration with third-party LMS platforms (Moodle, Canvas)

---

## 4. Literature Survey

A comprehensive survey of 15 research papers was conducted across the domains of AI-based online proctoring, examination security, cryptographic data protection, and access control in e-assessment systems. The following comparison table summarizes each paper's method, dataset, key results, and identified gaps.

### 4.1 Comparison Table of 15 Surveyed Papers

| # | Authors & Year | Title | Method / Approach | Dataset | Key Results | Identified Gap |
|---|----------------|-------|-------------------|---------|-------------|----------------|
| 1 | Atoum et al. (2017) [1] | Automated Online Exam Proctoring | Dual-camera hardware setup using webcam + wearable sensor with SVM-based anomaly classification | Self-collected dataset (47 students, 2 cameras per student) | 87% detection accuracy for cheating incidents across multiple exam sessions | Requires high-friction multi-camera/wearable hardware impractical for mass-scale remote education; high deployment cost |
| 2 | Nigam et al. (2021) [2] | A Systematic Review on AI-Based Online Exam Proctoring Systems | Systematic taxonomy and comparative analysis of 50+ deep learning and CV approaches for exam monitoring | Meta-analysis of published datasets across 50+ papers | Identified that standalone single-task CNNs achieve 70–92% accuracy but produce 15–30% false positives | Highlights extreme client-side compute bloat and high false-positive rates when using isolated single-modality models |
| 3 | Li et al. (2021) [3] | A Multimodal AI Proctoring System for MOOCs | Multimodal video analytics combining face recognition, gaze tracking, and audio analysis for MOOC examinations | MOOC-Scale dataset (1,200 exam sessions, HD video streams) | 91% suspicious behavior detection rate at 720p continuous streaming | Bandwidth bottleneck caused by continuous HD video streaming to cloud servers; prohibitive for students with limited connectivity |
| 4 | Garg & Sharma (2022) [4] | RBAC and Cryptographic Security in Cloud E-Assessment | Cryptographic protocols (TLS, AES) and RBAC in cloud-based assessment platforms | Simulated cloud assessment environment with 500 concurrent users | Demonstrated secure data transit and role separation with <2% latency overhead | Addressed secure transit only; left persistent database storage vulnerable to plaintext inspection by insiders/admins |
| 5 | Hu et al. (2020) [5] | Real-Time Gaze and Head Pose Tracking for Cheating Detection | 3D head pose estimation (yaw/pitch/roll) combined with eye gaze vector tracking using MediaPipe landmarks | Self-collected dataset (60 participants, controlled lab conditions) | 84% accuracy for detecting off-screen gaze and suspicious head turns | Evaluated visual gaze in isolation without considering hand movements, unauthorized devices, or multi-person context |
| 6 | Prathish et al. (2016) [6] | An Intelligent System for Online Exam Monitoring | Rule-based face detection with Haar cascades for presence verification during online tests | Limited self-collected dataset (30 students, single exam session) | 78% face detection accuracy; basic presence/absence flagging | Simplistic rule-based approach with no probabilistic scoring; high false-negative rate under poor lighting conditions |
| 7 | Cote et al. (2016) [7] | Video Summarization for Remote Invigilation of Online Exams | Automated video summarization using temporal segmentation and keyframe extraction for post-exam review | 50 recorded exam sessions from a university pilot program | Reduced video review time by 65% compared to full-video manual review | Post-exam forensic analysis only; no real-time alerting capability; cannot prevent cheating during the exam |
| 8 | Hasan et al. (2021) [8] | CNN-Based Object Detection for Online Exam Proctoring | YOLOv3-based object detection for identifying mobile phones, books, and unauthorized persons during exams | Custom annotated dataset (3,000 images across 5 object categories) | 89% mAP for unauthorized object detection; 12 FPS inference on GPU | Requires dedicated GPU hardware; no integration with behavioral analysis modules (gaze, head pose); client-side inference only |
| 9 | Tiong & Lee (2021) [9] | E-Cheating Prevention Using Deep Learning | Multi-task CNN combining face verification and suspicious behavior classification | CelebA + custom exam behavior dataset (2,500 labeled samples) | 86% verification accuracy; 83% suspicious behavior detection rate | Heavy client-side model (~200MB); causes thermal throttling on low-spec laptops; no encryption of exam data at rest |
| 10 | Indi et al. (2021) [10] | AI-Based Proctoring for Virtual Assessments | Ensemble of face detection (MTCNN), head pose (PnP solver), and audio anomaly detection | Collected dataset during virtual exams (150 students, ~4 hours each) | 88% combined detection accuracy with audio-visual fusion | No cryptographic protection for stored exam data; RBAC implemented at frontend only (bypassable); no MFA |
| 11 | Kasliwal et al. (2021) [11] | Cheating Detection in Online Exams Using Computer Vision | OpenCV-based face and eye tracking with rule-based anomaly thresholds | Self-collected webcam dataset (80 students, scripted cheating scenarios) | 82% detection accuracy for predefined cheating behaviors | Rigid rule-based thresholds without machine learning generalization; no support for dynamic/unseen cheating patterns |
| 12 | Pandey et al. (2022) [12] | Secure Online Examination System with Blockchain | Blockchain-based tamper-proof exam record storage with smart contract grading | Ethereum testnet simulation with 200 exam records | Demonstrated tamper-proof grade storage with consensus verification | Extremely high computational overhead for blockchain consensus; impractical transaction latency for real-time exam workflows; no AI proctoring |
| 13 | Thomas & Raorane (2020) [13] | Biometric Authentication for E-Learning Exam Security | Fingerprint and face recognition for continuous identity verification during online exams | FERET face database + self-collected fingerprint samples (100 users) | 94% identity verification accuracy using multimodal biometrics | Requires specialized biometric hardware (fingerprint scanner); privacy concerns with biometric data storage; no behavioral analysis |
| 14 | Masud et al. (2022) [14] | Smart Anti-Cheating Exam System Using IoT and ML | IoT sensor fusion (ambient microphone, infrared proximity, webcam) with Random Forest classification | Custom IoT sensor dataset (500 exam sessions with labeled cheating events) | 90% cheating detection accuracy using multi-sensor IoT fusion | Requires deployment of physical IoT sensors in the examination room; not applicable to remote/home exam settings |
| 15 | Jia & He (2021) [15] | Facial Action Unit Analysis for Remote Exam Monitoring | Facial Action Coding System (FACS) analysis using AU detection with temporal LSTM networks | BP4D spontaneous facial expression dataset (41 participants) | 85% accuracy for detecting stress-related and deceptive facial micro-expressions | Computationally expensive temporal LSTM inference; limited to facial modality only; no consideration of hand/device/environmental cues |

### 4.2 Summary of Identified Gaps in Existing Literature

| Gap Category | Description | Papers Exhibiting This Gap |
|--------------|-------------|---------------------------|
| **Single-modality limitation** | Most systems analyze only 1–2 behavioral channels (face, gaze), missing comprehensive contextual cues | [1], [5], [6], [7], [11], [13], [15] |
| **Heavy client-side computation** | Deep learning models run locally, causing device overheating and poor performance on low-spec hardware | [2], [3], [8], [9], [15] |
| **No real-time alerting** | Analysis is post-exam only; examiners cannot intervene during the examination | [1], [6], [7], [9], [11] |
| **No cryptographic data protection** | Exam questions, answers, and submissions stored in plaintext in the database | [1], [2], [5], [6], [8], [9], [10], [11], [14], [15] |
| **Weak access control** | Missing or frontend-only RBAC; no MFA; vulnerable to privilege escalation | [6], [8], [10], [11], [14] |
| **Specialized hardware dependency** | Requires dedicated cameras, GPUs, IoT sensors, or biometric scanners | [1], [8], [12], [13], [14] |

---

## 5. Proposed Methodology

The proposed system employs a **5-Tier Zero-Trust Architecture** that integrates multimodal AI proctoring, cryptographic data protection, and real-time telemetry into a unified platform.

### 5.1 Overall Approach

The methodology follows a layered approach:

**Step 1 — Lightweight Edge Frame Acquisition:**
The student's browser captures webcam frames at low resolution (320×240 pixels) at 0.25 Hz (one frame every 4 seconds) using the HTML5 Canvas API and WebRTC MediaStream. This minimal sampling rate ensures negligible CPU/bandwidth usage on the student's device.

**Step 2 — Server-Side Multimodal Feature Extraction:**
Each captured frame is transmitted as a base64-encoded payload to the FastAPI backend, where a 5-module feature extractor processes the image to produce a 37-dimensional behavioral feature vector:

| Module | Features Extracted | Count |
|--------|--------------------|-------|
| Module 1: Face Detection & Spatial Geometry | Face detected, count, confidence, bounding box area, center (x, y) | 6 |
| Module 2: 3D Head Pose Estimation | Yaw, pitch, roll angles and their normalized deviations | 6 |
| Module 3: Eye Gaze Tracking & Screen Attention | Horizontal/vertical gaze, screen focus, blink count, eye openness, gaze deviation, saccade rate | 8 |
| Module 4: Hand Movement & Anatomical Proximity | Hand detected, count, near-face/ear/pocket distances, movement speed, mouth obstruction, both-hands visible, typing heuristic | 9 |
| Module 5: Device Detection & Environmental Anomaly | Phone detected, confidence, screen glow, reflective surface, whisper score, secondary person, tab switch, mouth talking | 8 |
| **Total** | | **37** |

**Step 3 — Ensemble Random Forest Classification:**
The 37-dimensional feature vector is fed into a trained Random Forest ensemble classifier (100 decision trees, max depth 12) that outputs a cheating probability score P(Cheating | X) ∈ [0.0, 1.0]:

```
P(Cheating | X) = (1/B) × Σ I(Tb(X) = 1),  where B = 100 trees
```

If P(Cheating | X) ≥ 0.50 (threshold τ), the system flags the frame as suspicious and generates descriptive alert flags.

**Step 4 — Real-Time WebSocket Broadcasting:**
Flagged events are immediately broadcast via bidirectional WebSocket channels to the faculty/examiner dashboard, delivering the alert with event tags, student identity, and a visual snapshot within sub-200ms latency.

**Step 5 — Cryptographic Data Protection:**
All sensitive data (question text, correct answers, student submissions) passes through a Fernet-based AES-256 authenticated encryption pipeline before database persistence:

```
K_fernet = URLSafeBase64(SHA-256(MASTER_SECRET_KEY))
Ciphertext = AES-128-CBC(Plaintext, IV) || HMAC-SHA-256(Ciphertext, K_hmac)
```

**Step 6 — Defense-in-Depth Identity Assurance:**
User authentication is layered with bcrypt password hashing, JWT tokens with embedded role claims, server-side RBAC enforcement via FastAPI dependency injection, RFC 6238 TOTP MFA, in-memory sliding-window rate limiting, and comprehensive audit logging.

### 5.2 Methodology Flowchart

```
┌─────────────────────────────────────────────────────────────┐
│                    STUDENT EXAM SESSION                       │
│                                                               │
│  ┌──────────────┐     ┌───────────────┐     ┌──────────────┐ │
│  │ Login + MFA  │────▶│ Load Encrypted│────▶│ Start Exam   │ │
│  │ (JWT + TOTP) │     │ Questions     │     │ + Webcam     │ │
│  └──────────────┘     └───────────────┘     └──────┬───────┘ │
│                                                     │         │
│                          ┌──────────────────────────┘         │
│                          ▼                                    │
│               ┌──────────────────────┐                        │
│               │ Capture Frame (4s)   │◀──── Every 4 seconds   │
│               │ 320×240 @ 0.25Hz     │                        │
│               └──────────┬───────────┘                        │
│                          │ base64 POST                        │
└──────────────────────────┼────────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                     FASTAPI BACKEND                           │
│                                                               │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │        MULTIMODAL AI PROCTORING ENGINE                    │ │
│  │                                                            │ │
│  │  ┌─────────┐ ┌─────────┐ ┌────────┐ ┌──────┐ ┌────────┐ │ │
│  │  │Module 1 │ │Module 2 │ │Module 3│ │Mod 4 │ │Module 5│ │ │
│  │  │Face (6) │ │Head (6) │ │Gaze (8)│ │Hand(9)│ │Phone(8)│ │ │
│  │  └────┬────┘ └────┬────┘ └───┬────┘ └──┬───┘ └───┬────┘ │ │
│  │       └──────┬─────┴────┬─────┴────┬────┘         │      │ │
│  │              ▼          ▼          ▼              ▼      │ │
│  │        ┌──────────────────────────────────────────┐      │ │
│  │        │   37-D Feature Vector Concatenation       │      │ │
│  │        └───────────────────┬───────────────────────┘      │ │
│  │                            ▼                              │ │
│  │        ┌──────────────────────────────────────────┐      │ │
│  │        │  Random Forest Classifier (100 trees)     │      │ │
│  │        │  Output: P(Cheating) ∈ [0.0, 1.0]        │      │ │
│  │        └───────────────────┬───────────────────────┘      │ │
│  └────────────────────────────┼──────────────────────────────┘ │
│                               │                                │
│           ┌───────────────────┼───────────────────┐            │
│           ▼                   ▼                   ▼            │
│   P < 0.50              P ≥ 0.50          Save to DB           │
│   (Normal)            (Suspicious)     (AES-256 Encrypted)     │
│                           │                                    │
│                           ▼                                    │
│               ┌──────────────────────┐                         │
│               │  WebSocket Broadcast │                         │
│               │  to Faculty Dashboard│                         │
│               │  (Sub-200ms latency) │                         │
│               └──────────────────────┘                         │
└──────────────────────────────────────────────────────────────┘
```

---

## 6. Dataset Details

### 6.1 Primary Dataset

| Property | Detail |
|----------|--------|
| **Dataset Name** | Mendeley Exam Proctoring Suspicious Behaviours Dataset |
| **DOI** | 10.17632/39xs8th543.1 |
| **Source** | Mendeley Data (Open Access Research Data Repository) |
| **Total Samples** | 5,500 validated records |
| **Number of Features** | 37 behavioral features |
| **Number of Classes** | 2 (Normal/Honest: 0, Suspicious/Cheating: 1) |
| **Class Distribution** | Approximately balanced — 52% Normal, 48% Suspicious |
| **Feature Modules** | 5 modules: Face Detection (6), Head Pose (6), Eye Gaze (8), Hand Movement (9), Device Detection (8) |

### 6.2 Feature Description by Module

| Module | Feature Name | Data Type | Range/Domain |
|--------|-------------|-----------|--------------|
| Face Detection | `face_detected` | Binary | {0, 1} |
| Face Detection | `face_count` | Integer | N₀ |
| Face Detection | `face_confidence` | Float | [0.0, 1.0] |
| Face Detection | `face_bbox_area` | Float | [0.0, 1.0] (normalized) |
| Face Detection | `face_center_x` | Float | [0.0, 1.0] (normalized) |
| Face Detection | `face_center_y` | Float | [0.0, 1.0] (normalized) |
| Head Pose | `head_yaw` | Float | [-90, +90] degrees |
| Head Pose | `head_pitch` | Float | [-90, +90] degrees |
| Head Pose | `head_roll` | Float | [-90, +90] degrees |
| Head Pose | `yaw_deviation` | Float | [0.0, 1.0] (normalized) |
| Head Pose | `pitch_deviation` | Float | [0.0, 1.0] (normalized) |
| Head Pose | `roll_deviation` | Float | [0.0, 1.0] (normalized) |
| Eye Gaze | `gaze_horizontal` | Float | [-1.0, +1.0] |
| Eye Gaze | `gaze_vertical` | Float | [-1.0, +1.0] |
| Eye Gaze | `gaze_screen_focus` | Float | [0.0, 1.0] |
| Eye Gaze | `blink_count` | Float | Blinks per minute |
| Eye Gaze | `left_eye_openness` | Float | [0.0, 1.0] |
| Eye Gaze | `right_eye_openness` | Float | [0.0, 1.0] |
| Eye Gaze | `gaze_deviation` | Float | [0.0, +inf) |
| Eye Gaze | `saccade_rate` | Float | [0.0, +inf) |
| Hand Movement | `hand_detected` | Binary | {0, 1} |
| Hand Movement | `hand_count` | Integer | {0, 1, 2} |
| Hand Movement | `hand_near_face` | Float | [0.0, 1.0] |
| Hand Movement | `hand_near_ear` | Float | [0.0, 1.0] |
| Hand Movement | `hand_near_pocket` | Float | [0.0, 1.0] |
| Hand Movement | `hand_movement_speed` | Float | [0.0, 1.0] |
| Hand Movement | `hand_obscuring_mouth` | Float | [0.0, 1.0] |
| Hand Movement | `both_hands_visible` | Binary | {0, 1} |
| Hand Movement | `keyboard_typing_heuristic` | Float | [0.0, 1.0] |
| Device Detection | `phone_detected` | Binary | {0, 1} |
| Device Detection | `phone_confidence` | Float | [0.0, 1.0] |
| Device Detection | `device_screen_glow` | Float | [0.0, 1.0] |
| Device Detection | `reflective_surface_score` | Float | [0.0, 1.0] |
| Device Detection | `audio_whisper_score` | Float | [0.0, 1.0] |
| Device Detection | `secondary_person_presence` | Binary | {0, 1} |
| Device Detection | `tab_switch_flag` | Binary | {0, 1} |
| Device Detection | `mouth_movement_talking` | Float | [0.0, 1.0] |

### 6.3 Preprocessing Plan

| Step | Operation | Details |
|------|-----------|---------|
| 1 | Data Loading | Load CSV from Mendeley repository; verify 5,500 rows x 37 columns + 1 label column |
| 2 | Missing Value Handling | Check for NaN/null values; apply median imputation for continuous features and mode imputation for binary features |
| 3 | Feature Normalization | Min-Max scaling of angular features (yaw, pitch, roll) to [0, 1]; standard scaling for rate-based features (blink_count, saccade_rate) |
| 4 | Class Balance Verification | Confirm approximately balanced split (52:48); if imbalanced, apply SMOTE oversampling |
| 5 | Train-Test Split | Stratified 80:20 split preserving class distribution |
| 6 | Cross-Validation | Stratified 5-Fold Cross-Validation for hyperparameter tuning and model selection |
| 7 | Feature Importance Analysis | Random Forest feature importance ranking to identify most discriminative behavioral cues |

---

## 7. System Architecture Diagram

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    TIER 1: PRESENTATION & CLIENT-EDGE LAYER                │
│                                                                            │
│  ┌─────────────────────────────────┐  ┌──────────────────────────────────┐ │
│  │ React (Vite) SPA                │  │ Client-Edge Modules              │ │
│  │ - Admin Dashboard               │  │ - WebRTC Camera Capture          │ │
│  │ - Faculty/Examiner Portal       │  │   (320x240 @ 0.25 Hz)           │ │
│  │ - Student Exam Interface        │  │ - Canvas Frame Serializer        │ │
│  │ - Role-Tailored Views           │  │ - 10-Second Autosave Engine      │ │
│  │ - Real-Time Alert Listener      │  │ - Browser Focus Sentinel         │ │
│  └─────────────────────────────────┘  └──────────────────────────────────┘ │
│                                                                            │
└──────────────────────────────┬─────────────────────────────────────────────┘
                               │ HTTPS / TLS 1.3 & WSS (Encrypted Transport)
                               ▼
┌───────────────────────────────────────────────────────────────────────────┐
│            TIER 2: API GATEWAY, AUTHENTICATION & SECURITY FIREWALL         │
│                                                                            │
│  ┌────────────────────┐ ┌─────────────────────┐ ┌───────────────────────┐ │
│  │ FastAPI Gateway     │ │ Identity & Auth     │ │ Security Controls     │ │
│  │ - Reverse Proxy     │ │ - JWT Token Issuer  │ │ - Sliding-Window      │ │
│  │ - Request Router    │ │   (HS256 Signing)   │ │   Rate Limiter        │ │
│  │ - CORS Protection   │ │ - bcrypt Password   │ │ - Request Sanitizer   │ │
│  │ - Input Validation  │ │   Hashing           │ │ - IP-Based Throttling │ │
│  │                     │ │ - RFC 6238 TOTP MFA │ │                       │ │
│  └────────────────────┘ └─────────────────────┘ └───────────────────────┘ │
│                                                                            │
└──────────────────────────────┬─────────────────────────────────────────────┘
                               │ Injected Session & Role-Verified Context
                               ▼
┌───────────────────────────────────────────────────────────────────────────┐
│          TIER 3: CORE APPLICATION & EXAM ORCHESTRATION LAYER               │
│                                                                            │
│  ┌────────────────────┐ ┌─────────────────────┐ ┌───────────────────────┐ │
│  │ Exam Lifecycle      │ │ Evaluation Engine   │ │ Communication Hub     │ │
│  │ - State Machine     │ │ - Auto-Grading      │ │ - WebSocket Pool      │ │
│  │   (Draft -> Pub ->  │ │ - Decrypted Answer  │ │ - Alert Broadcaster   │ │
│  │    Completed)       │ │   Comparison        │ │ - Event Dispatcher    │ │
│  │ - RBAC Enforcement  │ │ - Score Calculation │ │                       │ │
│  │   (require_role)    │ │                     │ │                       │ │
│  │ - Autosave Manager  │ │                     │ │                       │ │
│  │ - Audit Logger      │ │                     │ │                       │ │
│  └────────────────────┘ └─────────────────────┘ └───────────────────────┘ │
│                                                                            │
└──────────┬────────────────────────────────────────┬───────────────────────┘
           │ AI Pipeline                            │ ORM + Ciphers
           ▼                                        ▼
┌──────────────────────────────────┐  ┌────────────────────────────────────┐
│ TIER 4: MULTIMODAL AI ENGINE    │  │ TIER 5: PERSISTENCE & CRYPTO LAYER │
│                                  │  │                                    │
│ 5-Module Feature Extractor:     │  │ Cryptographic Envelope Subsystem:  │
│ - Module 1: Face Detection (6)  │  │ - Fernet AES-256 Symmetric Cipher │
│ - Module 2: Head Pose (6)       │  │ - SHA-256 Key Derivation Function │
│ - Module 3: Eye Gaze (8)        │  │ - Zero-Plaintext at Rest          │
│ - Module 4: Hand Movement (9)   │  │                                    │
│ - Module 5: Device Detection (8)│  │ Relational Database:               │
│                                  │  │ - PostgreSQL / SQLite              │
│ Ensemble Classifier:            │  │ - Tables: users, exams, questions, │
│ - 100-Tree Random Forest        │  │   submissions, proctoring_events,  │
│ - Mendeley 5,500 Dataset        │  │   audit_logs                       │
│ - P(Cheating) in [0.0, 1.0]    │  │ - Encrypted Columns:              │
│ - Threshold t = 0.50            │  │   question_text_encrypted,         │
│                                  │  │   correct_answer_encrypted,        │
│ Alert Broadcaster:              │  │   answers_encrypted                │
│ - WebSocket push on anomaly     │  │                                    │
└──────────────────────────────────┘  └────────────────────────────────────┘
```

---

## 8. Threat Model

### 8.1 What is Protected (Assets)

| Asset | Description | Protection Mechanism |
|-------|-------------|---------------------|
| **Examination Question Papers** | Question text stored in the database | AES-256 Fernet encryption at rest (`question_text_encrypted` column) |
| **Correct Answer Keys** | Answer keys stored in the database | AES-256 Fernet encryption at rest (`correct_answer_encrypted` column) |
| **Student Submissions** | Student answers stored in the database | AES-256 Fernet encryption at rest (`answers_encrypted` column) |
| **User Credentials** | Passwords and authentication tokens | bcrypt hashing (work factor 12); JWT with HMAC-SHA256 signing |
| **Academic Integrity** | Ensuring students do not cheat during exams | Multimodal AI proctoring with real-time behavioral analysis |
| **System Access Control** | Preventing unauthorized access to admin/faculty functions | Server-side RBAC with `require_role()` dependency injection |
| **User Accounts** | Protection against unauthorized account access | RFC 6238 TOTP MFA; in-memory sliding-window rate limiting |
| **Audit Trail** | Forensic record of all administrative actions | Append-only `audit_logs` table with user, action, timestamp, IP |

### 8.2 Attacker Capabilities (Threat Actors)

| Threat Actor | Capabilities | Motivation |
|-------------|-------------|------------|
| **Malicious Student** | Standard laptop with webcam; can use secondary devices (phone, tablet); can collaborate with peers; can use physical notes off-screen; can attempt tab switching | Cheat on exams to obtain higher grades without genuine effort |
| **Credential Attacker** | Automated brute-force tools; stolen credential databases from external breaches; credential stuffing scripts | Gain unauthorized access to student/faculty/admin accounts |
| **Insider (Rogue Admin/DBA)** | Direct database access via SQL client; ability to read database tables and backup files | Leak exam questions before the exam; alter student grades; sell question papers |
| **Network Eavesdropper** | Passive network traffic interception (MITM); packet sniffing on unencrypted channels | Intercept exam questions or answers during transit |
| **Privilege Escalation Attacker** | Valid student account; knowledge of API endpoint structure; ability to craft HTTP requests | Access faculty or admin API endpoints to modify exams, view answers, or change roles |
| **Impersonator** | Access to a student's credentials; willing proxy test-taker | Take the exam on behalf of an enrolled student |

### 8.3 Attack Types and Countermeasures

| Attack Type | Description | Countermeasure in This System |
|-------------|-------------|-------------------------------|
| **Exam Cheating (Behavioral)** | Student looks away from screen, uses phone, consults secondary person, reads physical notes | 5-module multimodal AI proctoring engine analyzing 37 behavioral features per frame; real-time flagging when P(Cheating) >= 0.50 |
| **Tab Switching / Alt-Tab** | Student switches to browser tabs or other applications to search for answers | Browser focus sentinel (Page Visibility API); `tab_switch_flag` feature in proctoring vector |
| **Multiple Person Collusion** | Unauthorized person visible in webcam frame assisting the student | `secondary_person_presence` detection via face count module; `face_count > 1` triggers immediate alert |
| **Phone/Device Usage** | Student uses smartphone or tablet to photograph questions or look up answers | YOLOv8-based phone detection module; `phone_detected`, `phone_confidence`, `device_screen_glow` features |
| **SQL Injection** | Attacker injects malicious SQL to extract plaintext questions/answers from the database | Parameterized queries via SQLAlchemy ORM; even if DB is accessed, all sensitive data is AES-256 encrypted ciphertext |
| **Database Dump / Backup Leak** | Insider or attacker obtains raw database file or backup | Zero-plaintext at rest: all question text, answer keys, and submissions encrypted; raw SQL inspection reveals no readable content |
| **Brute-Force Login** | Automated attempts to guess user passwords via repeated login requests | In-memory sliding-window rate limiter on `/api/auth/login`; bcrypt with high work factor (slow hash computation) |
| **Credential Stuffing** | Reusing leaked credentials from other breaches to access accounts | RFC 6238 TOTP MFA requires a second factor (time-based code from authenticator app) even if password is compromised |
| **JWT Token Forgery** | Attacker attempts to forge or modify JWT tokens to impersonate users or escalate roles | HMAC-SHA256 signing with server-side secret; token expiration enforcement; `token_type` validation |
| **Privilege Escalation** | Student sends crafted HTTP requests directly to admin/faculty API endpoints | Server-side `require_role()` dependency that extracts role from verified JWT token and rejects with HTTP 403 if role is insufficient |
| **Man-in-the-Middle (MITM)** | Attacker intercepts communication between client and server | TLS 1.3 encrypted transport (HTTPS + WSS); all API and WebSocket channels encrypted in transit |
| **Session Hijacking** | Attacker steals a valid JWT token from network traffic or browser storage | Short-lived access tokens (configurable expiration); refresh token rotation; TLS-only transport |

### 8.4 Threat Model Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        THREAT LANDSCAPE                               │
│                                                                       │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  ┌────────────┐  │
│  │ Malicious   │  │ Credential   │  │ Insider    │  │ Network    │  │
│  │ Student     │  │ Attacker     │  │ (Rogue DBA)│  │ Eavesdrop  │  │
│  └──────┬──────┘  └──────┬───────┘  └─────┬──────┘  └─────┬──────┘  │
│         │                │                 │               │          │
│         ▼                ▼                 ▼               ▼          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  ┌────────────┐  │
│  │ Behavioral  │  │ Brute Force  │  │ DB Dump /  │  │ MITM /     │  │
│  │ Cheating    │  │ Credential   │  │ SQL Inject │  │ Packet     │  │
│  │ Phone Use   │  │ Stuffing     │  │ Backup Leak│  │ Sniffing   │  │
│  │ Collusion   │  │              │  │            │  │            │  │
│  └──────┬──────┘  └──────┬───────┘  └─────┬──────┘  └─────┬──────┘  │
└─────────┼────────────────┼─────────────────┼───────────────┼──────────┘
          │                │                 │               │
          ▼                ▼                 ▼               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      DEFENSE-IN-DEPTH COUNTERMEASURES                 │
│                                                                       │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────┐ ┌──────────────┐ │
│  │ AI Proctoring│ │ Rate Limiter │ │ AES-256     │ │ TLS 1.3      │ │
│  │ (37-D Vector │ │ + bcrypt     │ │ Fernet      │ │ HTTPS + WSS  │ │
│  │  + RF 100T)  │ │ + TOTP MFA   │ │ Encryption  │ │ Encrypted    │ │
│  │ Real-time WS │ │ + JWT Auth   │ │ at Rest     │ │ Transport    │ │
│  │ Alerts       │ │              │ │ Zero-Plain  │ │              │ │
│  └──────────────┘ └──────────────┘ └─────────────┘ └──────────────┘ │
│                                                                       │
│  ┌──────────────┐ ┌──────────────┐                                   │
│  │ Server-Side  │ │ Audit Log    │                                   │
│  │ RBAC         │ │ (Forensic    │                                   │
│  │ require_role │ │  Trail)      │                                   │
│  └──────────────┘ └──────────────┘                                   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 9. References

[1] Y. Atoum, L. Chen, A. X. Liu, S. D. H. Hsu, and X. Liu, "Automated Online Exam Proctoring," *IEEE Transactions on Multimedia*, vol. 19, no. 7, pp. 1609-1624, Jul. 2017.

[2] A. Nigam, R. Pasricha, T. Singh, and P. Churi, "A Systematic Review on AI-Based Online Exam Proctoring Systems," *IEEE Access*, vol. 9, pp. 64227-64240, 2021.

[3] H. Li, M. Xu, J. Wang, and Y. Kang, "A Multimodal AI Proctoring System for Massive Open Online Courses," *IEEE Transactions on Learning Technologies*, vol. 14, no. 3, pp. 364-375, Jun. 2021.

[4] S. Garg and V. Sharma, "Role-Based Access Control and Cryptographic Security in Cloud-Based E-Assessment Systems," *IEEE Access*, vol. 10, pp. 58312-58326, 2022.

[5] S. Hu, Y. Liu, and Z. Zhang, "Real-Time Gaze and Head Pose Tracking for Cheating Detection in Online Tests," *IEEE Transactions on Human-Machine Systems*, vol. 50, no. 4, pp. 312-323, Aug. 2020.

[6] D. A. Prathish, P. Athul, and P. R. Sreeraj, "An Intelligent System for Online Exam Monitoring," in *Proc. IEEE International Conference on Smart Technologies and Management (ICSTM)*, 2016, pp. 138-142.

[7] M. Cote, F. Jean, A. B. Albu, and D. Capson, "Video Summarization for Remote Invigilation of Online Exams," in *Proc. IEEE Winter Conference on Applications of Computer Vision (WACV)*, 2016, pp. 1-9.

[8] M. A. Hasan, S. Ahmed, and K. Wahid, "CNN-Based Object Detection for Online Exam Proctoring," in *Proc. IEEE International Conference on Electrical, Computer and Communication Engineering (ECCE)*, 2021, pp. 1-6.

[9] L. C. O. Tiong and H. J. Lee, "E-Cheating Prevention Measures: Detection of Cheating at Online Examinations Using Deep Learning Approach," *IEEE Access*, vol. 9, pp. 149185-149198, 2021.

[10] T. S. Indi, S. Gunge, M. Indi, and A. Biradar, "AI-Based Proctoring for Virtual Assessments: Online Proctored Examinations," *IEEE Transactions on Education*, vol. 64, no. 4, pp. 432-441, Nov. 2021.

[11] C. Kasliwal, S. Patil, D. Puri, and M. K. Bhanarkar, "Cheating Detection in Online Exams Using Computer Vision," in *Proc. IEEE International Conference on Computing Communication Control and Automation (ICCUBEA)*, 2021, pp. 1-6.

[12] P. Pandey, R. Kumar, and S. Singh, "Secure Online Examination System Using Blockchain Technology," in *Proc. IEEE International Conference on Computing, Communication, and Intelligent Systems (ICCCIS)*, 2022, pp. 278-283.

[13] A. Thomas and A. A. Raorane, "Biometric Authentication for Secure E-Learning Examination Systems," in *Proc. IEEE International Conference on Recent Trends in Electronics, Information and Communication Technology (RTEICT)*, 2020, pp. 115-119.

[14] M. Masud, G. Muhammad, and H. Alhumyani, "Smart Anti-Cheating Exam System Using IoT and Machine Learning," *IEEE Internet of Things Journal*, vol. 9, no. 16, pp. 14584-14593, Aug. 2022.

[15] J. Jia and J. He, "Facial Action Unit Analysis for Remote Exam Monitoring," in *Proc. IEEE International Conference on Automatic Face and Gesture Recognition (FG)*, 2021, pp. 1-8.

---

*Document prepared for Review 1: Problem and Design*
*B.Tech Capstone Project — September 2026*
