@echo off
cd /d "%~dp0backend"
echo ========================================================
echo   Starting Exam Portal FastAPI Backend on Port 8001
echo ========================================================
.\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload
pause
