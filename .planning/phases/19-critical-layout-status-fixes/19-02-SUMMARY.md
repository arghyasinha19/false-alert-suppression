# Plan 19-02 Summary: Authoritative Connection State Machine, Polling Resiliency & Mock Demarcation

**Phase:** 19 — Critical Layout & Status Fixes  
**Plan:** 19-02  
**Wave:** 2  
**Status:** Completed  
**Requirements Covered:** UI-02  
**Decisions Covered:** D-05, D-06, D-07, D-08, D-09, D-10, D-11, D-12, D-13, D-14, D-15, D-16  

---

## What Changed

1. **Tri-State Connection State Machine (`D-05`, `D-06`)**:
   - Refactored binary boolean connection tracking to structured state: `{ status: 'connected' | 'stale' | 'offline', lastSuccessfulSync, lastAttempt, error, consecutiveFailures }`.
   - Transitions to `'connected'` on successful responses, `'stale'` on 1–2 consecutive poll failures after having been connected, and `'offline'` on initial failure or 3+ failures.
   - Preserves and freezes `lastSuccessfulSync` on failure, preventing false-positive "Updated 2s ago" displays.

2. **Strict Payload Validation & Nominal Empty Arrays (`D-08`, `D-15`)**:
   - Enhanced `fetchData` in `dashboard/src/App.jsx` to strictly validate `Array.isArray(alertsRes?.alerts)` and `Array.isArray(devicesRes?.devices)`.
   - Malformed payloads trigger immediate catch handling; valid empty arrays (`[]`) are accepted as connected.

3. **Progressive Retry Backoff & Window Focus Reconnection (`D-13`, `D-14`)**:
   - Switched from fixed `setInterval` to adaptive `setTimeout` polling with backoff: 10s on failure 1, 20s on failure 2, 60s for 3+ failures.
   - Added `window.addEventListener('focus', ...)` to trigger immediate re-checks when returning to the tab.
   - Added manual "Reconnect API" buttons in the content header, sidebar, and dismissible demo banner.

4. **Diagnostic Tooltip (`D-16`)**:
   - Added diagnostic tooltip to the Live/Stale/Offline badge detailing API endpoint, last sync time, last attempt, error reason, and retry cadence.

5. **Mock Data Demarcation & Top Dismissible Banner (`D-09`, `D-12`)**:
   - Added dedicated `[Mock / Seed Data]` amber chip in `.content-header-actions` when disconnected.
   - Added dismissible `.demo-mode-banner` at top of `.content-body` with "Reconnect API" and "Dismiss" actions.
   - Kept individual table rows and KPI cards clean and production-styled without noisy per-row demo watermarks.

6. **Status Propagation & SRE Drawer Provenance (`D-07`, `D-10`, `D-11`)**:
   - Passed `connectionStatus` and `lastSuccessfulSync` props to `NetworkOperations` and `FalseAlertMetrics`.
   - Updated `.noc-refresh-bar` dot, label, and timestamp in `dashboard/src/NetworkOperations.jsx` to reflect tri-state status.
   - Updated SRE details drawer to render "Simulated Device Profile" banner and disable "Poll DNAC" with tooltip "Backend API offline • Live controller polling unavailable" when offline.

7. **Automated Connection Status Contract Test Suite**:
   - Added `tests/test_connection_status_contract.py` asserting tri-state transitions, payload validation, timestamp freezing, retry backoff, mock demarcation, and drawer provenance handling.
   - All 7 tests passing (`pytest tests/test_connection_status_contract.py`).

---

## Verification

- `pytest tests/test_critical_layout_contract.py`: 5 passed.
- `pytest tests/test_connection_status_contract.py`: 7 passed.
- `npm run build`: built client environment for production cleanly with zero errors (544 modules transformed).
