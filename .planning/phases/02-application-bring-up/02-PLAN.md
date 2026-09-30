# Phase 2 Plan: Application Bring-Up & Local Orchestration

## Objective
Launch and verify the operational dashboard stack (FastAPI backend on port 8004 and Vite React frontend on port 5173), confirm end-to-end API polling, and provide a single-command launcher script.

## Tasks
1. **Create Startup Script (`start_dashboard.py`)**:
   - Spawns both the FastAPI backend (`uvicorn dashboard.api:app --host 127.0.0.1 --port 8004`) and Vite dev server (`npm run dev`).
   - Handles graceful shutdown on SIGINT/Ctrl+C.
2. **Launch Backend Service**:
   - Start FastAPI backend with `run_command` (as daemon background process).
   - Verify health via `http://127.0.0.1:8004/api/alerts` returning HTTP 200 with alerts array.
3. **Launch Frontend Dev Server**:
   - Start Vite dev server in `dashboard/` with `run_command` (as daemon background process).
   - Verify HTTP 200 on `http://localhost:5173`.
4. **End-to-End Verification**:
   - Check API connection between frontend and backend.
   - Verify False Alert Metrics tab displays 60 total alerts with accurate KPI counts.
5. **Phase Summary & Commit**:
   - Record accomplishments in `02-SUMMARY.md` and commit changes.
