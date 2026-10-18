# Secure Online Exam Portal with AI-Driven Proctoring and RBAC

> **B.Tech Pre-Final Year Academic Project**  
> A full-stack, enterprise-grade secure examination platform with server-side Role-Based Access Control (RBAC), AES-256 encrypted question papers and answers at rest, real-time AI webcam proctoring, WebSocket suspicion alerting, and RFC 6238 TOTP Multi-Factor Authentication.

---

## 🏛️ System Architecture

```text
                                +-----------------------------------+
                                |   React Frontend (Vite)          |
                                |   - Admin / Faculty / Student     |
                                |   - WebRTC Camera Capture         |
                                |   - WebSocket Live Alert Listener |
                                +-----------------+-----------------+
                                                  |
                                   HTTP / REST & WebSockets
                                                  |
                                                  v
+-----------------------------------------------------------------------------------+
|                           FastAPI Backend & Security Core                        |
|                                                                                   |
|  [ Auth & RBAC ]        [ AES-256 Crypto ]      [ AI Proctoring Engine ]          |
|  - JWT Role Claims      - Fernet / AES-256      - OpenCV Feature Extraction       |
|  - bcrypt Hashing       - Question Encryption   - Mendeley 5,500 Dataset Model    |
|  - require_role Guard   - Submissions Cipher    - Cheating Probability Scoring    |
|  - TOTP MFA (pyotp)     - Zero Plaintext Leak   - Real-Time WebSocket Alerts      |
+-----------------------------------------+-----------------------------------------+
                                          |
                                 SQLAlchemy ORM
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

## 🚀 Key Features Implemented

1. **Role-Based Access Control (RBAC)**:
   - Three discrete roles: **Admin**, **Faculty/Examiner**, **Student**.
   - Enforced via FastAPI dependency injection (`require_role(...)`).
   - Rejects unauthorized cross-role attempts with `HTTP 403 Forbidden` at the API layer.
2. **AES-256 Encryption at Rest**:
   - Question text and correct answers are encrypted with AES-256 before writing to the database.
   - Student answers are encrypted with AES-256 upon submission.
   - Direct database inspection in SQL reveals zero plaintext examination content.
3. **AI Proctoring Engine**:
   - Analyzes periodic webcam frames across 5 distinct modules: Face Detection, Head Pose (Pitch/Yaw/Roll), Eye Gaze Direction, Hand Movement, and Mobile Phone/Device Detection.
   - Trained on the **Mendeley Proctoring Suspicious Behaviours Dataset** (DOI 10.17632/39xs8th543.1, 5,500 records, 37 features).
   - Random Forest Classifier outputs real-time cheating probability scores (0.0 to 1.0) and descriptive suspicion flags.
4. **Real-Time WebSockets Alerting**:
   - Live bidirectional streaming between Student exam sessions and the Faculty dashboard.
   - Suspicious frames automatically trigger alerts with snapshot previews on the examiner's screen.
5. **Security Hardening & MFA**:
   - RFC 6238 TOTP Multi-Factor Authentication (compatible with Google Authenticator & Authy).
   - In-memory rate limiting on `/api/auth/login` to prevent brute-force attacks.
   - Comprehensive audit logging (`AuditLogs`) capturing all logins, role changes, exam publications, and submissions.
6. **Automated Objective Grading & Autosave**:
   - Student answers autosave in the background every 10 seconds.
   - Submissions are evaluated against decrypted correct answers and auto-scored instantly.

---

## 👥 Seeded Test Credentials

| Role | Email Address | Password |
| :--- | :--- | :--- |
| **🛡️ Admin** | `admin@examportal.com` | `AdminPass123!` |
| **🎓 Faculty / Examiner** | `faculty@examportal.com` | `FacultyPass123!` |
| **✍️ Student Candidate** | `student@examportal.com` | `StudentPass123!` |

---

## 🛠️ Local Development & Execution

### 1. Backend (FastAPI)
```powershell
cd backend
.\venv\Scripts\activate
uvicorn main:app --reload --reload-exclude "venv/*" --port 8000
```
- Interactive Swagger API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/health`

### 2. Frontend (React + Vite)
```powershell
cd frontend
npm run dev
```
- Open browser at `http://localhost:5173`

---

## 🧪 Running Automated Test Suite

Run the full functional, security, and AI evaluation test suite:
```powershell
cd backend
.\venv\Scripts\pytest.exe tests/test_portal.py -v
```

**Test Coverage Summary**:
- ✅ `test_aes256_text_encryption`: AES-256 ciphertext encryption/decryption integrity.
- ✅ `test_aes256_json_encryption`: JSON payload cipher validation.
- ✅ `test_login_and_token_generation`: JWT issuance with embedded role claims.
- ✅ `test_invalid_login_rejected`: 401 Unauthorized rejection on bad credentials.
- ✅ `test_rbac_security_cross_role_access`: 403 Forbidden enforcement on student hitting admin/faculty APIs.
- ✅ `test_faculty_exam_crud_and_question_encryption`: Confirms raw DB questions are encrypted & student view strips correct answers.
- ✅ `test_student_exam_taking_and_autograde`: Autosave, submission locking, and auto-grading.
- ✅ `test_totp_mfa_generation_and_validation`: RFC 6238 TOTP verification.
- ✅ `test_ai_proctoring_classifier_metrics`: Held-out dataset accuracy, precision, and recall metrics.

---

## 🐳 Multi-Container Docker Deployment

Bring up the complete system (PostgreSQL, Backend API, and Frontend) with a single command:
```bash
docker-compose up --build
```
- Frontend UI: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
