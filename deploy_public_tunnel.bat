@echo off
echo ======================================================================
echo   Deploying Exam Portal to Public URL via Cloudflare Quick Tunnel
echo ======================================================================
echo.
echo [1/3] Starting FastAPI Backend on Port 8001...
start "Exam Portal Backend" "%~dp0start_backend.bat"

echo [2/3] Starting React / Vite Frontend on Port 5174...
start "Exam Portal Frontend" "%~dp0start_frontend.bat"

echo.
echo Waiting 5 seconds for local services to initialize...
ping 127.0.0.1 -n 6 >nul

echo [3/3] Generating random public HTTPS tunnel...
echo (Look below for your random *.trycloudflare.com address)
echo ======================================================================
npx --yes cloudflared tunnel --url http://localhost:5174
pause
