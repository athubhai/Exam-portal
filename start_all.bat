@echo off
echo ========================================================
echo   Launching Exam Portal - Backend and Frontend
echo ========================================================
start "Exam Portal Backend" "%~dp0start_backend.bat"
ping 127.0.0.1 -n 3 >nul
start "Exam Portal Frontend" "%~dp0start_frontend.bat"
echo.
echo Both servers have been launched in separate windows!
echo - Backend:  http://127.0.0.1:8001 (API docs: http://127.0.0.1:8001/docs)
echo - Frontend: http://localhost:5174
echo.
