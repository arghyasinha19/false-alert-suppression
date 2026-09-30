# Project Milestones

## Completed Milestones

### v1.0 False Alert Metrics Alignment (Completed 2026-09-30)
- **Goal:** Verify and align Total Processed KPI calculation, category filtering, and backend endpoints.
- **Shipped:**
  - `Total Processed` defined as strictly `Suppressed + Auto-Resolving + Non-Auto-Resolving + Uncertain`.
  - `Tickets Avoided` derived as `Suppressed + Auto-Resolving` (avoiding double-counting).
  - Scope alerts decoupled from category filter in `FalseAlertMetrics.jsx`.
  - Toggleable category KPI cards with active visual highlights.
  - Aligned `/api/kpi/summary` endpoints in `api.py` and `chat_agent.py`.

### v1.1 Application Bring-Up & Local Orchestration (Completed 2026-09-30)
- **Goal:** Launch, orchestrate, and verify all core services of the False Alert Suppression pipeline locally, ensuring the backend API, React dashboard, and health checks are fully operational and reachable.
- **Shipped:**
  - Created [`start_dashboard.py`](file:///c:/Users/Arghya/Desktop/Solutions/false-alert-suppression/start_dashboard.py) launcher.
  - Launched FastAPI backend (`dashboard/api.py`) on `http://127.0.0.1:8004` (verified HTTP 200 on `/api/alerts` and `/api/kpi/summary`).
  - Launched Vite React frontend (`dashboard/`) on `http://localhost:5173/` (verified HTTP 200).
  - Verified live data connection and polling.

### v1.2 Custom Date & Time Range Filtering (Completed 2026-09-30)
- **Goal:** Allow users to specify custom start and end date/time ranges in the False Alert Metrics filter bar to inspect alert volume and KPIs within exact historical windows.
- **Shipped:**
  - Added "Custom Range" button and dropdown selector option in `FalseAlertMetrics.jsx`.
  - Added glassmorphism-styled `From` and `To` datetime-local inputs, "Clear", and "Presets" quick-actions.
  - Built-in boundary filtering across `scopeAlerts` with dynamic KPI recalculations (Total Processed, Tickets Avoided, Suppression Rate, ServiceNow breakdown).
  - Verified with Vite build and browser subagent end-to-end testing.
