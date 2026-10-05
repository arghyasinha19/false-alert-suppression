---
phase: 15
plan: 15-01
status: ready
wave: 1
depends_on: []
files_modified:
  - dashboard/src/App.jsx
  - dashboard/src/NetworkOperations.jsx
  - dashboard/src/App.css
  - tests/test_frontend_sre_drawer_contract.py
autonomous: true
requirements:
  - DNAC-05
  - DNAC-06
---

# Phase 15: Frontend SRE Drawer Live Wire-Up — Plan

**Phase:** 15  
**Status:** Ready  
**Milestone:** v1.6 Live DNAC Assurance Telemetry & Asset Integration  
**Requirements:** DNAC-05, DNAC-06  
**Context:** `.planning/phases/15-frontend-sre-drawer-live-wire-up/15-CONTEXT.md`  
**UI Contract:** `.planning/phases/15-frontend-sre-drawer-live-wire-up/15-UI-SPEC.md`  

---

## Overview

Phase 15 connects the slide-out SRE triage drawer in `dashboard/src/NetworkOperations.jsx` and styling in `dashboard/src/App.css` to the live backend endpoints established in Phase 14 (`GET /api/devices/{name}/telemetry` and `POST /api/devices/{name}/live-poll`).

This replaces procedurally generated numbers and artificial `setTimeout` polling with:
1. Real HTTP live polling from the SRE Action Bar and drawer header with active spinner feedback.
2. Fleet-wide data synchronization (`onRefresh` propagation to parent `App.jsx`).
3. Immediate telemetry retrieval upon opening the device drawer with subtle background upgrade loading indicators.
4. Dual-placement provenance badges (`● DNAC LIVE` / `⟳ CACHED` / `○ OFFLINE` in header pill and tab banners).
5. Honest null states (`"—"`, 0% muted gauge meters, and offline retry banners) when telemetry is unreachable or null.

---

## Threat Model (ASVS Level 1)

<threat_model>
### Attack Surface & Security Mitigations

1. **URI Path Traversal & Injection via Device Name:**
   - *Threat:* Malicious or malformed device names (e.g. `../../admin` or characters like `?`, `#`, `/`) injected into client fetch calls.
   - *Mitigation:* All dynamic fetch URLs in `NetworkOperations.jsx` MUST sanitize device names with `encodeURIComponent(selectedDevice.device_name)`.

2. **Race Conditions & Asynchronous State Overwrites:**
   - *Threat:* Rapidly clicking between multiple devices in the grid could allow slower HTTP responses from previously selected devices to overwrite the currently active drawer's telemetry.
   - *Mitigation:* Implement an `AbortController` or active request token reference (`activeDeviceFetchRef`) to abort prior in-flight requests and ignore responses that do not match `selectedDeviceNameRef.current`.

3. **Client-Side Denial of Service via Error Cascades:**
   - *Threat:* Non-200 responses, network disconnects, or unexpected JSON schemas from the backend causing unhandled JavaScript runtime exceptions that crash the React component tree.
   - *Mitigation:* Wrap all API calls in defensive `try / catch / finally` blocks with safe default state assignments and dynamic error toasts. The UI must never crash on network failure.
</threat_model>

---

## Files Changed

| Action | File | Description |
|---|---|---|
| MODIFY | `dashboard/src/App.jsx` | Passes `onRefresh={fetchData}` callback to `<NetworkOperations>` to support fleet-wide sync on live polling |
| MODIFY | `dashboard/src/NetworkOperations.jsx` | Replaces procedural vitals and `setTimeout` with live endpoints, state management, dual badges, and honest null states |
| MODIFY | `dashboard/src/App.css` | Adds CSS tokens and classes for `.noc-provenance-pill`, `.noc-provenance-banner`, `.noc-loading-dot`, and offline states |
| CREATE | `tests/test_frontend_sre_drawer_contract.py` | Automated contract test verifying frontend source code integration, API routes, and parameter handling |

---

## Tasks

<tasks>

### Task 1 — Integrate Live Telemetry Fetching & State Management (DNAC-06)

<read_first>
- `dashboard/src/NetworkOperations.jsx`
- `.planning/phases/15-frontend-sre-drawer-live-wire-up/15-CONTEXT.md`
- `.planning/phases/15-frontend-sre-drawer-live-wire-up/15-UI-SPEC.md`
</read_first>

<action>
In `dashboard/src/NetworkOperations.jsx`:
1. Add state hooks for telemetry management:
   ```javascript
   const [deviceTelemetry, setDeviceTelemetry] = useState(null);
   const [loadingTelemetry, setLoadingTelemetry] = useState(false);
   const telemetryAbortRef = useRef(null);
   ```
2. Create `fetchDeviceTelemetry(deviceName)` helper:
   - Aborts any ongoing request via `telemetryAbortRef.current?.abort()`.
   - Creates a new `AbortController` and assigns to `telemetryAbortRef.current`.
   - Sets `loadingTelemetry(true)`.
   - Calls `fetch('/api/devices/' + encodeURIComponent(deviceName) + '/telemetry', { signal: controller.signal })`.
   - On HTTP 200 / valid JSON response:
     - Check `if (selectedDeviceNameRef.current === deviceName)` to guard against race conditions.
     - Set `deviceTelemetry(data)`.
     - Set `loadingTelemetry(false)`.
   - On error:
     - If not an `AbortError`: set `loadingTelemetry(false)`, keep any existing baseline or set fallback `{ source: 'offline', telemetry: null, device_info: null }`.
3. In `openDevicePanel(device)`:
   - Call `setDeviceTelemetry(null)` (or retain matching cached entry).
   - Trigger `fetchDeviceTelemetry(device.device_name)`.
4. In `closePanel()`:
   - Abort any in-flight fetch via `telemetryAbortRef.current?.abort()`.
   - In cleanup timeout, reset `deviceTelemetry` to `null` and `loadingTelemetry` to `false`.
</action>

<acceptance_criteria>
- `dashboard/src/NetworkOperations.jsx` defines `deviceTelemetry` and `loadingTelemetry` state hooks.
- `openDevicePanel` initiates `fetch` to `/api/devices/{encodeURIComponent(device.device_name)}/telemetry`.
- Rapidly switching devices aborts in-flight requests and avoids setting stale telemetry.
- No unhandled Promise rejections occur if the network is disconnected or the request is aborted.
</acceptance_criteria>

---

### Task 2 — Implement Dual Provenance Badges & Honest Null State Rendering (DNAC-06)

<read_first>
- `dashboard/src/NetworkOperations.jsx`
- `dashboard/src/App.css`
- `.planning/phases/15-frontend-sre-drawer-live-wire-up/15-UI-SPEC.md`
</read_first>

<action>
1. In `dashboard/src/App.css`, add styles adhering to `15-UI-SPEC.md`:
   - `.noc-provenance-pill`: Display inline-flex, align-items center, gap 4px, font-size 11px, font-weight 700, border-radius 999px, padding 2px 8px.
     - `.noc-provenance-pill.live`: Background `rgba(16, 185, 129, 0.12)`, color `var(--accent-green-bright)`, border `1px solid rgba(16, 185, 129, 0.25)`.
     - `.noc-provenance-pill.cached`: Background `rgba(245, 158, 11, 0.12)`, color `var(--accent-yellow-bright)`, border `1px solid rgba(245, 158, 11, 0.25)`.
     - `.noc-provenance-pill.offline`: Background `rgba(100, 116, 139, 0.12)`, color `var(--text-tertiary)`, border `1px solid rgba(100, 116, 139, 0.25)`.
   - `.noc-loading-dot`: 6px diameter pulsing dot with CSS `@keyframes noc-pulse` animation.
   - `.noc-provenance-banner`: Pinned at top of Telemetry and Inventory tabs with flex layout, gap 8px, font-size 12px, border-radius `var(--radius-sm)`, padding 8px 12px, margin-bottom 12px.
     - Includes styling for `.noc-retry-btn` (compact transparent button with hover border).
   - `.noc-gauge-meter.muted`: Background `rgba(255, 255, 255, 0.04)`.

2. In `dashboard/src/NetworkOperations.jsx`:
   - Compute active vitals from `deviceTelemetry`:
     ```javascript
     const telemetrySource = deviceTelemetry?.source || (loadingTelemetry ? 'loading' : 'cached_offline');
     const liveVitals = deviceTelemetry?.telemetry;
     const liveDeviceInfo = deviceTelemetry?.device_info;
     ```
   - In drawer header (`detail-panel-header`), render header provenance pill next to device title:
     - Displays `● DNAC LIVE` when `telemetrySource === 'dnac_live'`.
     - Displays `⟳ CACHED` when `telemetrySource === 'cached_offline'`.
     - Displays `○ OFFLINE` when `telemetrySource === 'offline'`.
     - If `loadingTelemetry` is true, render `<span className="noc-loading-dot" />` indicating active synchronization.
   - In **Assurance Telemetry Tab**:
     - Render tab provenance banner at the top showing sync timestamp and source.
     - If `telemetrySource === 'offline'`, render warning banner with text: `"DNAC Unreachable • Displaying offline baseline record"` and a `"Retry Poll"` button that calls `handlePollDNAC()`.
     - Render KPI vitals cards honestly:
       - CPU: `liveVitals?.cpu_utilization != null ? `${liveVitals.cpu_utilization}%` : '—'`
       - RAM: `liveVitals?.memory_utilization != null ? `${liveVitals.memory_utilization}%` : '—'`
       - Gauge bars: width `${liveVitals?.cpu_utilization || 0}%`, width `${liveVitals?.memory_utilization || 0}%`. If null, gauge bar width is `0%`.
       - Packet Loss: `liveVitals?.packet_loss_pct != null ? `${liveVitals.packet_loss_pct}%` : '0.00%'`
       - Reachability: `liveVitals?.reachable ? 'Reachable (Optimal)' : 'Degraded / Unreachable'`
       - Temperature: `liveVitals?.temperature_celsius != null ? `${liveVitals.temperature_celsius}°C` : '—'`
       - PoE Usage: `liveVitals?.poe_usage || '—'`
       - Power State: `liveVitals?.power_supply_status || 'Dual Redundant (OK)'`
   - In **Device Inventory Tab**:
     - Render tab provenance banner at the top.
     - Model: `liveDeviceInfo?.model || selectedDevice.device_name`
     - OS / Firmware: `liveDeviceInfo?.os_version || '—'`
     - Serial Number: `liveDeviceInfo?.serial || '—'`
     - MAC Address: `liveDeviceInfo?.mac || '—'`
     - IP Address: `liveDeviceInfo?.ip_address || selectedDevice.ip_address || '—'`
     - Uptime: Format `liveVitals?.uptime_seconds` (or backend `liveDeviceInfo?.uptime`) into clean `X days, Y hours` string.
</action>

<acceptance_criteria>
- Drawer header displays `.noc-provenance-pill` with color-coded live/cached/offline indicator.
- Assurance Telemetry and Device Inventory tabs render top provenance banner with sync timestamp.
- When `deviceTelemetry.source === 'offline'` or metrics are null, cards render `" — "` and 0% gauge bar rather than fake numbers.
- `Retry Poll` button appears in offline banner and triggers `handlePollDNAC`.
</acceptance_criteria>

---

### Task 3 — Wire "Poll DNAC" to Real Endpoint with Fleet Sync & Dynamic Toasts (DNAC-05)

<read_first>
- `dashboard/src/App.jsx`
- `dashboard/src/NetworkOperations.jsx`
- `.planning/phases/15-frontend-sre-drawer-live-wire-up/15-CONTEXT.md`
</read_first>

<action>
1. In `dashboard/src/App.jsx`:
   - Pass `onRefresh={fetchData}` to `<NetworkOperations devices={devices} lastRefresh={lastRefresh} pollInterval={POLL_INTERVAL} onRefresh={fetchData} />`.

2. In `dashboard/src/NetworkOperations.jsx`:
   - Accept `onRefresh` prop in `NetworkOperations({ devices: rawDevices, lastRefresh, pollInterval = 15000, onRefresh })`.
   - Update `handlePollDNAC`:
     ```javascript
     const handlePollDNAC = async () => {
       if (!selectedDevice || pollingHealth) return;
       setPollingHealth(true);
       try {
         const resp = await fetch(
           `/api/devices/${encodeURIComponent(selectedDevice.device_name)}/live-poll`,
           { method: 'POST' }
         );
         if (!resp.ok) {
           throw new Error(`HTTP error ${resp.status}`);
         }
         const data = await resp.json();
         
         // Update local drawer telemetry immediately
         if (data.telemetry || data.device_info) {
           setDeviceTelemetry({
             device_name: selectedDevice.device_name,
             source: data.source || (data.dnac_reachable ? 'dnac_live' : 'cached_offline'),
             synced_at: data.timestamp,
             telemetry: data.telemetry,
             device_info: data.device_info
           });
         }
         
         // Trigger fleet-wide dashboard refresh
         if (typeof onRefresh === 'function') {
           onRefresh();
         }
         
         // Dynamic toast feedback
         if (data.status === 'success') {
           addToast(
             'DNAC Live Synchronized',
             `Synchronized ${data.alerts_updated ?? 0} alerts and refreshed telemetry for ${selectedDevice.device_name}.`,
             'success'
           );
         } else {
           addToast(
             'DNAC Controller Unreachable',
             'Cisco DNA Center Assurance returned offline status. Retaining cached telemetry.',
             'warning'
           );
         }
       } catch (err) {
         console.error('Failed to poll DNAC:', err);
         addToast(
           'Assurance Polling Failed',
           `Network error connecting to /api/devices/${selectedDevice.device_name}/live-poll.`,
           'error'
         );
       } finally {
         setPollingHealth(false);
       }
     };
     ```
   - Ensure both Poll DNAC buttons (drawer header and sticky action bar) have `disabled={pollingHealth}` and show `<RefreshCw className={pollingHealth ? 'spin' : ''} />`.
</action>

<acceptance_criteria>
- `App.jsx` passes `onRefresh={fetchData}` to `NetworkOperations`.
- `handlePollDNAC` performs real `fetch` with method `POST` to `/api/devices/{name}/live-poll`.
- The artificial `setTimeout` in `handlePollDNAC` is completely removed.
- On success, `onRefresh()` is invoked and local drawer state updates immediately.
- Dynamic toast appears matching server response status (`success`, `warning`, or `error`).
</acceptance_criteria>

---

### Task 4 — Lint, Production Build & Automated Contract Verification

<read_first>
- `dashboard/package.json`
- `tests/test_device_telemetry_api.py`
</read_first>

<action>
1. Run linter and type/syntax checks:
   ```bash
   cd dashboard && npm run lint
   ```
2. Run Vite production build:
   ```bash
   cd dashboard && npm run build
   ```
3. Create `tests/test_frontend_sre_drawer_contract.py` using Python's `ast` / file inspection and FastAPI `TestClient`:
   - Asserts `NetworkOperations.jsx` references `/api/devices/${encodeURIComponent(` or equivalent for both `telemetry` and `live-poll`.
   - Asserts `setTimeout` is no longer used for simulated polling in `handlePollDNAC`.
   - Asserts `App.jsx` passes `onRefresh` to `NetworkOperations`.
   - Asserts `App.css` defines `.noc-provenance-pill` and `.noc-provenance-banner`.
   - Asserts backend telemetry endpoint responses match the schema expected by `NetworkOperations.jsx`.
4. Run full test suite:
   ```bash
   pytest tests/test_frontend_sre_drawer_contract.py tests/test_device_telemetry_api.py -v
   ```
</action>

<acceptance_criteria>
- `npm run lint` finishes with 0 errors and 0 warnings.
- `npm run build` succeeds and produces minified artifacts in `dist/`.
- `pytest tests/test_frontend_sre_drawer_contract.py tests/test_device_telemetry_api.py -v` passes 100% green.
</acceptance_criteria>

</tasks>

---

## Must-Haves (Goal-Backward Verification)

- **M-01:** Opening any device drawer triggers an immediate HTTP GET request to `/api/devices/{name}/telemetry` and populates the Assurance Telemetry and Device Inventory tabs.
- **M-02:** Clicking "Poll DNAC" in either the drawer header or sticky action bar triggers an HTTP POST request to `/api/devices/{name}/live-poll`, spins the refresh icon, and disables the button during in-flight communication.
- **M-03:** Live poll completion dynamically updates the drawer vitals, triggers `onRefresh()` to synchronize fleet views, and displays appropriate toast notifications (`success` / `warning` / `error`).
- **M-04:** Dual-placement provenance indicators display correct status (`● DNAC LIVE` / `⟳ CACHED` / `○ OFFLINE`) in both the drawer header pill and tab banners.
- **M-05:** When telemetry is offline or vitals are null, honest null states (`"—"`, 0% muted meter, offline retry banner) are rendered without fabricated numbers.
- **M-06:** Zero linter errors/warnings in `npm run lint`, clean Vite production build in `npm run build`, and 100% passing tests in `pytest`.
