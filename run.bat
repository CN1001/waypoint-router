@echo off
start "Backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
start "Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
