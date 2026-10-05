# Phase 15: Frontend SRE Drawer Live Wire-Up — Summary

**Status:** Complete  
**Commit:** Pending  
**Date:** 2026-10-05  

## One-liner

Connected the slide-out SRE triage drawer in `NetworkOperations.jsx` to live Cisco DNA Center telemetry and live polling backend endpoints, adding active spinner feedback, fleet-wide background sync via `onRefresh()`, dual-placement provenance badges (`● DNAC LIVE` / `⟳ CACHED` / `○ OFFLINE`), and honest null states.

## What Was Built

### 1. Live Telemetry Fetching & State Integration (`NetworkOperations.jsx`)
- Added `deviceTelemetry`, `loadingTelemetry`, and `telemetryAbortRef` state management.
- Implemented `fetchDeviceTelemetry(deviceName)` which initiates `GET /api/devices/${encodeURIComponent(deviceName)}/telemetry` immediately when `openDevicePanel(device)` is invoked.
- Incorporated `AbortController` cancellation to eliminate async race conditions when switching between devices rapidly.
- Retains existing cached vitals while fetching and seamlessly upgrades once the live payload resolves without layout pop-in.

### 2. Dual-Placement Provenance Indicators (`NetworkOperations.jsx` & `App.css`)
- **Header Status Pill:** Added color-coded status pills directly beside the device title in the drawer header:
  - `● DNAC LIVE` with green accent tint (`rgba(16, 185, 129, 0.12)`) and green text (`#10b981`).
  - `⟳ CACHED` with amber accent tint (`rgba(245, 158, 11, 0.12)`) and yellow text (`#f59e0b`).
  - `○ OFFLINE` with slate tint (`rgba(100, 116, 139, 0.12)`) and muted text (`#64748b`).
  - Pulsing loader dot (`.noc-loading-dot`) indicating active background re-checks.
- **Tab Provenance Banners:** Rendered sticky provenance banners at the top of the **Assurance Telemetry** and **Device Inventory** tabs with exact sync timestamps, data origin labels, and an embedded `Retry Poll` button when in offline state.

### 3. Real "Poll DNAC" Action & Fleet Refresh Sync (`App.jsx` & `NetworkOperations.jsx`)
- Replaced the procedural `setTimeout` in `handlePollDNAC` with a real HTTP `POST` to `/api/devices/${encodeURIComponent(selectedDevice.device_name)}/live-poll`.
- Pinned active spinners (`.spin`) and disabled states to both Poll DNAC buttons (drawer header and sticky action bar) during in-flight requests.
- Invokes parent `onRefresh()` upon successful response to synchronize background device cards, active alert counts, and SRE tables fleet-wide across all views.
- Displayed dynamic toasts matching actual backend outcomes:
  - Success: `"DNAC Live Synchronized"` with count of updated alerts.
  - Warning (Offline Controller): `"DNAC Controller Unreachable"` explaining cached state is retained.
  - Network Error: `"Assurance Polling Failed"` with problem path.

### 4. Honest Null States & Telemetry Rendering (`NetworkOperations.jsx` & `App.css`)
- Muted 0% gauge meters (`.noc-gauge-meter.muted`) and rendered honest `" — "` / `"No Signal"` text instead of fabricated numbers when metrics are null or unreachable.
- Formatted `uptime_seconds` into human-friendly `X days, Y hours` display.
- Enhanced Raw Payloads tab and Export Diagnostic Report with `live_telemetry_payload` and `telemetry_source`.

### 5. Automated Verification & Contract Suite (`tests/test_frontend_sre_drawer_contract.py`)
- Created 5 unit and integration tests verifying frontend code contracts, `onRefresh` propagation, CSS class existence, and backend schema compatibility.

## Requirements Delivered

- **DNAC-05**: Clicking "Poll DNAC" in `NetworkOperations.jsx` triggers `POST /api/devices/{device_name}/live-poll` with visual spinner and dynamic toast notification displaying actual response. (✓ Verified)
- **DNAC-06**: Assurance Telemetry and Device Inventory tabs in the SRE drawer render live vitals fetched from `/api/devices/{device_name}/telemetry` with live/offline source badges. (✓ Verified)

## Decisions Implemented

All decisions from `15-CONTEXT.md` honored:
- **D-01 (Fetch on drawer open):** `openDevicePanel` immediately triggers `fetchDeviceTelemetry`.
- **D-02 (Seamless upgrade):** Subtle loading dot indicator with seamless upgrade on response.
- **D-03 (Real HTTP call):** Replaced procedural `setTimeout` with `POST /api/devices/{name}/live-poll`.
- **D-04 (Fleet-wide refresh):** Local drawer updates immediately and calls `onRefresh()` to sync parent views.
- **D-05 (Dynamic toast feedback):** Accurate toasts for success, offline warning, and network error.
- **D-06 (Dual placement):** Header status pill + tab provenance banner with sync timestamp.
- **D-07 (Honest null states):** Rendered `" — "` and 0% gauge bar when telemetry is null or offline.
- **D-08 (CSS tokens & responsiveness):** Adhered to existing CSS variables and glassmorphism styling.

## Files Changed

| Action | File | Description |
|---|---|---|
| MODIFIED | `dashboard/src/App.jsx` | Passes `onRefresh={fetchData}` prop to `NetworkOperations` |
| MODIFIED | `dashboard/src/NetworkOperations.jsx` | Wires drawer to live endpoints, state management, dual badges, and honest null states |
| MODIFIED | `dashboard/src/App.css` | Adds CSS styles for `.noc-provenance-pill`, `.noc-provenance-banner`, `.noc-loading-dot`, `.noc-null-val` |
| CREATED | `tests/test_frontend_sre_drawer_contract.py` | Automated contract test for frontend and backend integration |
| CREATED | `.planning/phases/15-frontend-sre-drawer-live-wire-up/15-SUMMARY.md` | Phase 15 implementation summary |

## Test Verification

```text
============================= test session starts =============================
tests/test_frontend_sre_drawer_contract.py::test_network_operations_wireup_source_contract PASSED [  7%]
tests/test_frontend_sre_drawer_contract.py::test_app_jsx_passes_on_refresh_to_network_operations PASSED [ 15%]
tests/test_frontend_sre_drawer_contract.py::test_app_css_defines_provenance_and_banner_classes PASSED [ 23%]
tests/test_frontend_sre_drawer_contract.py::test_telemetry_endpoint_schema_contract PASSED [ 30%]
tests/test_frontend_sre_drawer_contract.py::test_live_poll_endpoint_schema_contract PASSED [ 38%]
tests/test_device_telemetry_api.py::test_get_telemetry_live_success PASSED [ 46%]
tests/test_device_telemetry_api.py::test_get_telemetry_singular_route_alias PASSED [ 53%]
tests/test_device_telemetry_api.py::test_get_telemetry_offline_with_cached_state PASSED [ 61%]
tests/test_device_telemetry_api.py::test_get_telemetry_offline_without_cache PASSED [ 69%]
tests/test_device_telemetry_api.py::test_get_telemetry_device_not_found PASSED [ 76%]
tests/test_device_telemetry_api.py::test_post_live_poll_success PASSED   [ 84%]
tests/test_device_telemetry_api.py::test_post_live_poll_singular_alias PASSED [ 92%]
tests/test_device_telemetry_api.py::test_post_live_poll_dnac_offline_graceful PASSED [100%]

============================= 13 passed in 6.11s ==============================

> dashboard@0.0.0 lint
> oxlint
Found 0 warnings and 0 errors.

> dashboard@0.0.0 build
> vite build
✓ built in 762ms
```

---

*Phase 15 complete — 2026-10-05*
