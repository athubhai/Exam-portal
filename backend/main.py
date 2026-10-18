import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from database import check_db_connection

# Import all routers
from routers.auth import router as auth_router
from routers.exams import router as exams_router
from routers.submissions import router as submissions_router
from routers.proctoring import router as proctoring_router
from routers.admin import router as admin_router
from routers.mfa import router as mfa_router
from routers.profile import router as profile_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Secure Online Exam Portal with AI-Driven Proctoring, AES-256 Encryption & Role-Based Access Control",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register All API Routers under /api
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(exams_router, prefix=settings.API_V1_STR)
app.include_router(submissions_router, prefix=settings.API_V1_STR)
app.include_router(proctoring_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix=settings.API_V1_STR)
app.include_router(mfa_router, prefix=settings.API_V1_STR)
app.include_router(profile_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "message": "Welcome to Secure Online Exam Portal API",
        "status": "online",
        "version": "1.0.0",
        "docs_url": "/docs",
        "features": [
            "Role-Based Access Control (RBAC)",
            "Fernet Authenticated Encryption (AES-128-CBC + HMAC-SHA256)",
            "Real-Time AI Proctoring (OpenCV + YOLOv8 + Synthetic Classifier)",
            "WebSockets Real-Time Suspicion Alerts (Authenticated)",
            "TOTP Multi-Factor Authentication (Encrypted at Rest)",
            "Audit Trail Logging",
            "User Profile Management & Password Change"
        ]
    }

@app.get("/api/health")
def health_check():
    start_time = time.time()
    db_health = check_db_connection()
    latency_ms = round((time.time() - start_time) * 1000, 2)
    
    return {
        "status": "ok",
        "message": "Backend FastAPI service is running",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "latency_ms": latency_ms,
        "database": db_health,
        "environment": "development"
    }
