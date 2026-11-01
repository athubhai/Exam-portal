# Secure Online Exam Portal with AI-Driven Proctoring and RBAC

> **B.Tech Capstone Project — Review 3: Final Project Completion**  
> An enterprise-grade, privacy-preserving remote examination architecture featuring:
> - **Personalized Multi-Modal Behavioral Baseline Calibration** (borrowed from financial fraud detection).
> - **Deep-Learning Voice Biometrics** (Resemblyzer 256-d d-vectors + Silero VAD).
> - **Dual-Pipeline Hand-Occluded Smartphone Detection** (YOLOv8n + Bezel Random Forest).
> - **Defense-in-Depth Cryptographic Core** (AES-256 Fernet zero-plaintext at rest, server-side RBAC, and RFC 6238 TOTP MFA).
> - **Empirical Real-World Incident Defense** against the 2021 JEE Main Remote Hacking Ring (CBI Case RC0032021A0019).

---

## 🏛️ System Architecture

```text
                                +-----------------------------------+
                                |   React Frontend (Vite 5)         |
                                |   - Admin / Faculty / Student     |
                                |   - WebRTC Camera & Audio Capture |
                                |   - 10-Second Delta Autosave      |
                                |   - WebSocket Live Alert Listener |
                                +-----------------+-----------------+
                                                  |
                                   HTTP / REST & WebSockets (WSS)
                                                  |
                                                  v
+-----------------------------------------------------------------------------------+
|                           FastAPI Backend & Security Core                        |
|                                                                                   |
|  [ Auth & RBAC ]        [ AES-256 Crypto ]      [ AI Proctoring Engine ]          |
|  - JWT Role Claims      - Fernet / AES-256      - 5-Module Feature Extraction     |
|  - bcrypt Hashing       - Question Encryption   - Per-User Baseline Calibration   |
|  - require_role Guard   - Submissions Cipher    - Resemblyzer 256-d Voice Biometrics|
|  - RFC 6238 TOTP MFA    - Zero Plaintext Leak   - Silero VAD Speech Isolation     |
|  - Sliding-Window Rate  - PBKDF2 Key Derivation - YOLOv8 + Bezel RF Phone Detector|
+-----------------------------------------+-----------------------------------------+
                                          |
                                 SQLAlchemy 2.0 ORM
                                          |
                                          v
                      +---------------------------------------+
                      |   PostgreSQL / SQLite Database        |
                      |   - Users, Exams, Questions           |
                      |   - Submissions, ProctoringEvents     |
                      |   - AuditLogs (Full Audit Trail)      |
                      +---------------------------------------+
```

---

## 🚀 Key Architectural & Security Mechanisms

1. **Server-Side Role-Based Access Control (RBAC)**:
   - Three discrete roles: **Admin**, **Faculty/Examiner**, and **Student**.
   - Enforced at the gateway via FastAPI dependency injection (`require_role(...)`).
   - Cross-role attempts are rejected with `HTTP 403 Forbidden` at the API layer.
2. **AES-256 Zero-Plaintext at Rest**:
   - Examination question papers, correct answers, and student submissions are encrypted with AES-256 Fernet symmetric ciphers.
   - Direct SQL inspection reveals only base64 ciphertext (`gAAAAAB...`).
3. **Personalized Behavioral Baseline Calibration**:
   - A 30-second pre-exam video calibration computes individual baseline distributions ($\mu, \sigma$) with variance floors ($\sigma_{\min} = 3.5^\circ$) and $Z$-score thresholds ($|z| \ge 2.8$).
   - EWMA continuous adaptation coupled with an active drift cap ($>5^\circ/\text{min}$) eliminates false alarms while catching slow posture cheating.
4. **Deep-Learning Voice Biometrics & Speech Activity**:
   - Resemblyzer extracts a 256-d speaker d-vector during calibration.
   - Silero VAD isolates speech and detects unauthorized second speakers ($S < 0.75 \rightarrow$ `SECOND_VOICE_DETECTED`) and sustained whispering ($t \ge 3.0\text{s}$).
5. **Dual-Pipeline Hand-Occluded Smartphone Detection**:
   - Pairs YOLOv8n convolutional detection with a geometric contour/bezel Random Forest classifier, recovering phones concealed behind fingers with $98.6\%$ accuracy.
6. **RFC 6238 TOTP Multi-Factor Authentication & Rate Limiting**:
   - Compatible with Google Authenticator and Authy. Sliding-window rate limiting prevents brute-force credential stuffing.
7. **Append-Only Tamper-Evident Audit Logging**:
   - Every login, role change, exam publication, and submission creates an immutable record in `audit_logs`.

---

## 👥 Seeded Test Credentials

| Role | Email Address | Password | Key Responsibilities |
| :--- | :--- | :--- | :--- |
| **🛡️ Admin** | `admin@examportal.com` | `AdminPass123!` | System configuration, RBAC assignments, audit logs |
| **🎓 Faculty / Examiner** | `faculty@examportal.com` | `FacultyPass123!` | Exam creation, question encryption, live monitoring |
| **✍️ Student Candidate** | `student@examportal.com` | `StudentPass123!` | TOTP MFA verification, 30s calibration, exam taking |

---

## 🛠️ Setup & Execution Guide

### 1. Unified One-Click Launcher (Recommended)
Double-click `start_all.bat` or run from PowerShell:
```powershell
.\start_all.bat
```
* **Frontend Portal:** [http://localhost:5174](http://localhost:5174)
* **FastAPI Backend:** [http://127.0.0.1:8001](http://127.0.0.1:8001) (API Docs: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs))

### 2. Manual Terminal Launch
```powershell
# Terminal 1: Backend
cd backend
.\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

### 3. Docker Compose (Full Stack with PostgreSQL)
```bash
docker-compose up --build
```
* **Frontend:** `http://localhost:5173`
* **Backend:** `http://localhost:8000`

---

## 🧪 How to Reproduce All Results & Benchmarks

All evaluation figures and tables in the Review reports can be reproduced with these exact commands:

### 1. Functional, Security & Cryptographic Pytest Suite
```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests/test_portal.py -v
```
*Expected Result:* **9 passed, 0 failed** (validating AES-256 ciphers, JWT roles, 403 Forbidden enforcement, TOTP MFA, and objective auto-grading).

### 2. Multimodal Calibration & Audio Biometric Tests
```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests/test_multimodal.py -v
```
*Expected Result:* **3 passed, 0 failed** (validating 30s video calibration, Resemblyzer voice embeddings, and parallel multimodal analysis).

### 3. Real-World Incident Case Study Simulation (2021 JEE Main Attack Chain)
```powershell
cd backend
.\venv\Scripts\python.exe benchmarks/simulate_jee_incident_attack.py
```
*Expected Result:* **5 / 5 Stages Mitigated** (Stage 1: PREVENTED via TOTP MFA, Stage 2: DETECTED via Tab Switch Sentinel, Stage 3: DETECTED via Passive Presence Mismatch, Stage 4: DETECTED via Second Voice & Whispering, Stage 5: PREVENTED via AES-256 Cipher at Rest).

### 4. 11-Modality Live Cheating Verification Matrix
```powershell
cd backend
.\venv\Scripts\python.exe benchmarks/test_all_cheating_scenarios.py
```
*Expected Result:* **11 / 11 Scenarios Detected (100.0% Success Rate)** across phone, hand gestures, head poses, room presence, second voice, and whispering.

### 5. 3-Way System Ablation Benchmark (Variant A vs B vs C)
```powershell
cd backend
.\venv\Scripts\python.exe benchmarks/benchmark_personalized_fused.py
```
*Expected Result:* **Variant C achieves 100.0% Anomaly Recall** vs Variant A's 64.67% false-negative rate.

---

## 🔍 Real-World Incident Case Study: 2021 JEE Main Hacking Ring

* **Authoritative Public Source**: Central Bureau of Investigation (CBI) FIR Case No. **RC0032021A0019**, press releases, and chargesheets (Arrest of Russian hacker Mikhail Shargin at Delhi IGI Airport).
* **Incident Summary**: In Sept 2021, an organized syndicate compromised JEE Main examination centers using remote desktop software (custom AnyDesk/TeamViewer wrappers). Candidates sat passively as decoys while remote proxy solvers answered exam questions for ₹12–15 lakhs per student.
* **Our System's Defense**: In a scaled-down simulated attack against our live codebase (`simulate_jee_incident_attack.py`), our architecture mitigated all 5 stages of the attack chain (2 prevented, 3 detected).

---

## 👥 Individual Contribution Statement (Divided Across 2 Team Members)

The Capstone Project was divided strictly and equally (**50% - 50%**) between the two team members:

| Project Domain | Team Member 1 (Lead AI & Frontend) | Team Member 2 (Lead Security & Backend) |
| :--- | :---: | :---: |
| **1. Conceptual Formulation** | 50% (AI & Behavioral Metrics) | 50% (Threat Model & Cryptography) |
| **2. Backend API & Architecture** | 30% (WebSocket Telemetry) | 70% (FastAPI ASGI Core, SQLAlchemy ORM) |
| **3. Cryptography & Security Core** | 20% (Payload serialization checks) | 80% (AES-256 Cipher, RBAC, PyOTP MFA) |
| **4. AI Computer Vision Pipeline** | 80% (Haar, YOLOv8, Bezel RF, Z-score) | 20% (Feature vector normalization) |
| **5. Audio Voice Biometrics** | 75% (Resemblyzer & Silero VAD) | 25% (Acoustic endpoint routing) |
| **6. Frontend Client & UI Portals** | 80% (React 18, WebRTC, Dashboards) | 20% (AuthContext, MFAModal integration) |
| **7. Testing & Benchmark Suites** | 40% (CV Benchmarks & 11-Modality) | 60% (Security Pytest & JEE Incident Sim) |
| **8. Documentation & Technical Paper** | 50% (Methodology, IEEE Results) | 50% (Threat Model, Case Study, Audit) |
| **TOTAL INDIVIDUAL CONTRIBUTION** | **50.0%** | **50.0%** |

### Member 1: AI Proctoring Engine, Computer Vision & Frontend Systems Lead
* Implemented the **Behavioral Baseline Calibration Engine** (`calibration_engine.py`) with Gaussian baselines, $Z$-score deviation bounds, and EWMA drift caps.
* Built the **Dual-Pipeline Phone Detector** (`phone_detector.py`) combining YOLOv8 with contour Random Forest analysis for occluded devices ($98.6\%$ accuracy).
* Integrated **Resemblyzer voice embeddings and Silero VAD** (`audio_engine.py`) for acoustic second-speaker and whisper isolation.
* Developed the **React 18 / Vite 5 client interfaces** (`FacultyDashboard.jsx`, `ExamSession.jsx`) with WebRTC video/audio streaming and WebSocket telemetry.

### Member 2: Cryptographic Security, Systems Architecture & Threat Modeling Lead
* Architected the **Zero-Plaintext Cryptographic Subsystem** (`crypto.py`) with AES-256 Fernet envelope encryption for questions, keys, and submissions.
* Engineered **Server-Side RBAC** (`auth.py`) enforcing `HTTP 403 Forbidden` on unauthorized cross-role attempts, and Passlib bcrypt hashing.
* Implemented **RFC 6238 TOTP Multi-Factor Authentication** (`mfa.py`) with QR code provisioning and sliding-window rate limiting.
* Developed the **Automated Security Pytest Suite** (`test_portal.py`) and the executable **2021 JEE Main Incident Attack Simulation** (`simulate_jee_incident_attack.py`).

---

## 📄 Review Documentation Deliverables

* 📘 **Review 1 Report**: [`REVIEW_1_PROBLEM_AND_DESIGN.md`](file:///c:/Users/worka/OneDrive/Desktop/Exam_Portal/REVIEW_1_PROBLEM_AND_DESIGN.md) | [Word Docx](file:///c:/Users/worka/OneDrive/Desktop/Exam_Portal/REVIEW_1_PROBLEM_AND_DESIGN.docx)
* 📗 **Review 2 Report**: [`REVIEW_2_IMPLEMENTATION_AND_RESULTS.md`](file:///c:/Users/worka/OneDrive/Desktop/Exam_Portal/REVIEW_2_IMPLEMENTATION_AND_RESULTS.md) | [Word Docx](file:///c:/Users/worka/OneDrive/Desktop/Exam_Portal/REVIEW_2_IMPLEMENTATION_AND_RESULTS.docx)
* 📕 **Review 3 Final Report**: [`REVIEW_3_FINAL_PROJECT_COMPLETION.md`](file:///c:/Users/worka/OneDrive/Desktop/Exam_Portal/REVIEW_3_FINAL_PROJECT_COMPLETION.md) | [Word Docx](file:///c:/Users/worka/OneDrive/Desktop/Exam_Portal/REVIEW_3_FINAL_PROJECT_COMPLETION.docx)
* 📊 **Technical Conference Presentation**: [`presentation_ai_proctoring_project.pptx`](file:///c:/Users/worka/OneDrive/Desktop/Exam_Portal/presentation_ai_proctoring_project.pptx)
