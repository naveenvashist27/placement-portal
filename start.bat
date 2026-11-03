@echo off
rem Starts database, backend and frontend, each in its own window.
cd /d "%~dp0"

docker compose up -d
start "Backend" cmd /k "cd backend && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Open http://localhost:5173 in your browser.
echo Close the Backend and Frontend windows to stop.
