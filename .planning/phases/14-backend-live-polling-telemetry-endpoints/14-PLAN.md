---
phase: 14
plan: 14-01
status: ready
wave: 1
depends_on: []
files_modified:
  - dashboard/device_service.py
  - dashboard/api.py
  - tests/test_device_telemetry_api.py
autonomous: true
requirements:
  - DNAC-03
  - DNAC-04
---

# Phase 14: Backend Live Polling & Telemetry Endpoints — Plan

**Phase:** 14  
**Status:** Ready  
**Milestone:** v1.6 Live DNAC Assurance Telemetry & Asset Integration  
**Requirements:** DNAC-03, DNAC-04  
**Context:** `.planning/phases/14-backend-live-polling-telemetry-endpoints/14-CONTEXT.md`  

---

## Overview

Phase 14 implements backend FastAPI endpoints for live Cisco DNA Center Assurance telemetry retrieval and on-demand device status polling in `dashboard/api.py`, supported by a clean service module `dashboard/device_service.py`:
1. `GET /api/devices/{device_name}/telemetry` (and alias `GET /api/device/{device_name}/telemetry`) — returns normalized telemetry vitals (`cpu`, `memory`, `packet_drop`, `health_score`, etc.) and hardware inventory (`model`, `serial`, `mac`, `os_version`, `ip_address`), with source tagging (`"dnac_live"`, `"cached_offline"`, or `"offline"`).
2. `POST /api/devices/{device_name}/live-poll` (and alias `POST /api/device/{device_name}/live-poll`) — synchronously re-verifies active alerts for that device via `check_dashboard_dnac_status`, persists updated `dnac_live_status` to MongoDB, fetches fresh health vitals, and returns consolidated device state without throwing 500 errors.
3. Dedicated test suite in `tests/test_device_telemetry_api.py` verifying all routes, mock DNAC responses, offline fallbacks, and error scenarios using FastAPI's `TestClient`.

---

## Files Changed

| Action | File | Description |
|---|---|---|
| CREATE | `dashboard/device_service.py` | Encapsulates UUID resolution, telemetry fetching/caching, and synchronous live polling logic |
| MODIFY | `dashboard/api.py` | Registers telemetry and live-poll endpoints with dual route aliases (`/devices` and `/device`) |
| CREATE | `tests/test_device_telemetry_api.py` | Unit & integration tests for telemetry and live-poll endpoints with full mock and fallback coverage |

---

## Tasks

<tasks>

### Task 1 — Create `dashboard/device_service.py`

<read_first>
- `dashboard/dnac_monitor.py`
- `dashboard/dnac_sync.py`
- `app/dnac_client.py`
- `app/exceptions.py`
- `.planning/phases/14-backend-live-polling-telemetry-endpoints/14-CONTEXT.md`
</read_first>

<action>
Create `dashboard/device_service.py` containing three core functions:

1. `get_or_resolve_device_id(device_name: str, mongo_client, dnac_client) -> tuple[Optional[str], Optional[dict]]`:
   - Checks MongoDB `device_telemetry` collection for an existing `device_id` mapping for `device_name`.
   - If not found, checks MongoDB `alert_results` for any alert where `alert_details.device_name` or `alert_details.device` matches `device_name` and has non-empty `alert_details.device_id`.
   - If `device_name` matches a 36-character UUID pattern (`^[0-9a-fA-F-]{36}$`), treat it directly as the `device_id`.
   - If still unmapped and `dnac_client` is available, call `dnac_client.get_device_by_name_or_ip(device_name)`. On success, take the first matched device object, extract `device_id = dev.get("device_id")` and `device_info = { "model": dev.get("model"), "serial": dev.get("serial"), "mac": dev.get("mac"), "os_version": dev.get("os_version"), "ip_address": dev.get("ip_address") }`.
   - Returns `(device_id, device_info)`.

2. `fetch_device_telemetry(device_name: str, mongo_client=None, dnac_client=None) -> dict`:
   - Implements Decisions D-01, D-02, D-03, D-08, D-10.
   - Resolves UUID and device_info using `get_or_resolve_device_id`.
   - Attempts live DNAC health retrieval via `dnac_client.get_device_health(device_id)` if UUID and `dnac_client` are present.
   - On success:
     - Extracts the 9 vitals: `cpu`, `memory`, `packet_drop`, `health_score`, `interface_error_count`, `poe_status`, `uptime_seconds`, `reachable`, and `raw_response`.
     - Caches document in MongoDB `device_telemetry` collection:
       `{ "device_name": device_name, "device_id": device_id, "telemetry": telemetry_dict, "device_info": device_info, "last_updated": now_iso, "source": "dnac_live" }` with `upsert=True` on `device_name`.
     - Returns payload with `source: "dnac_live"`, `timestamp: now_iso`, `telemetry`, and `device_info`.
   - On failure (`DNACConnectionError`, `DeviceNotFoundError`, network timeout, or `dnac_client is None`):
     - Attempts to retrieve last-known cached telemetry document from MongoDB `device_telemetry`.
     - If cached document found: returns it with `source: "cached_offline"`, cached `telemetry` (with `reachable: false`), and cached `device_info`.
     - If no cached document exists: returns graceful offline fallback with `source: "offline"`, `timestamp: now_iso`, empty/null telemetry vitals (`cpu: None`, `memory: None`, `packet_drop: None`, `health_score: None`, `reachable: False`, etc.), and minimal `device_info` with `model: "Unknown"`.
     - Never raises unhandled exceptions.

3. `poll_device_live(device_name: str, mongo_client=None, dnac_client=None) -> dict`:
   - Implements Decisions D-04, D-05, D-06, D-07, D-10.
   - Query MongoDB `alert_results` for alerts matching `device_name` where `dnac_live_status` is not `RESOLVED` (active/unresolved alerts).
   - For each matching alert, call `check_dashboard_dnac_status(...)` from `dashboard/dnac_monitor.py`.
   - Updates `dnac_live_status` and `dnac_last_checked` in MongoDB `alert_results`.
   - Calls `fetch_device_telemetry(device_name, mongo_client, dnac_client)` to fetch fresh telemetry and update `device_telemetry` cache.
   - Returns consolidated state:
     `{ "status": "success" if dnac_reachable else "warning", "device_name": device_name, "device_id": device_id, "dnac_reachable": dnac_reachable, "alerts_updated": count, "telemetry": telemetry_dict, "device_info": device_info, "timestamp": now_iso }`.
</action>

<acceptance_criteria>
- `dashboard/device_service.py` exists and is syntactically valid Python.
- `from dashboard.device_service import get_or_resolve_device_id, fetch_device_telemetry, poll_device_live` imports without errors.
- `fetch_device_telemetry("non_existent_device")` returns a dictionary containing keys `device_name`, `device_id`, `source`, `timestamp`, `telemetry`, `device_info` without throwing exceptions.
- `poll_device_live("non_existent_device")` returns a dictionary containing keys `status`, `device_name`, `dnac_reachable`, `alerts_updated`, `telemetry`, `device_info`, `timestamp` without throwing exceptions.
</acceptance_criteria>

---

### Task 2 — Update `dashboard/api.py` with Telemetry and Live-Poll Endpoints

<read_first>
- `dashboard/api.py`
- `dashboard/device_service.py`
- `dashboard/dnac_monitor.py`
- `.planning/phases/14-backend-live-polling-telemetry-endpoints/14-CONTEXT.md`
</read_first>

<action>
In `dashboard/api.py`:
1. Import `fetch_device_telemetry` and `poll_device_live` from `dashboard.device_service`.
2. Import `_load_dnac_client` from `dashboard.dnac_monitor`.
3. Add a helper `get_dnac_client()` to obtain a shared/cached `DNACClient` instance or instantiate via `_load_dnac_client()`.
4. Register the telemetry routes (supporting both plural `/api/devices` and singular `/api/device` aliases per Decision D-09):
   - `@app.get("/api/devices/{device_name}/telemetry")`
   - `@app.get("/api/device/{device_name}/telemetry")`
   Implementation calls `fetch_device_telemetry(device_name, mongo, get_dnac_client())` and returns the result.
5. Register the live-poll routes (supporting both plural `/api/devices` and singular `/api/device` aliases per Decision D-09):
   - `@app.post("/api/devices/{device_name}/live-poll")`
   - `@app.post("/api/device/{device_name}/live-poll")`
   Implementation calls `poll_device_live(device_name, mongo, get_dnac_client())` and returns the result.
6. Ensure both endpoints handle all exceptions internally and return HTTP 200 responses with structured status codes (`status: "success"` or `"warning"` or `"error"`) rather than unhandled 500s.
</action>

<acceptance_criteria>
- `dashboard/api.py` contains route definitions for `@app.get("/api/devices/{device_name}/telemetry")`, `@app.get("/api/device/{device_name}/telemetry")`, `@app.post("/api/devices/{device_name}/live-poll")`, and `@app.post("/api/device/{device_name}/live-poll")`.
- Calling `GET /api/devices/{device_name}/telemetry` with `fastapi.testclient.TestClient` returns HTTP 200 with JSON payload containing `source`, `timestamp`, `telemetry`, `device_info`.
- Calling `POST /api/devices/{device_name}/live-poll` with `fastapi.testclient.TestClient` returns HTTP 200 with JSON payload containing `status`, `device_name`, `dnac_reachable`, `alerts_updated`.
</acceptance_criteria>

---

### Task 3 — Create Comprehensive Test Suite in `tests/test_device_telemetry_api.py`

<read_first>
- `dashboard/api.py`
- `dashboard/device_service.py`
- `tests/test_dnac_client_integration.py`
</read_first>

<action>
Create `tests/test_device_telemetry_api.py` using `pytest`, `unittest.mock.patch`, and `fastapi.testclient.TestClient`:
1. `test_get_telemetry_live_success`:
   - Mock `DNACClient.get_device_by_name_or_ip` to return a sample device dict (`device_id: "uuid-1234", model: "C9300-48P"`).
   - Mock `DNACClient.get_device_health` to return sample 9-key vitals (`cpu: 18.5, memory: 44.2, packet_drop: 0.0, health_score: 10`).
   - Mock MongoDB client and collections.
   - Assert `GET /api/devices/edge-sw-01/telemetry` returns 200, `source == "dnac_live"`, `telemetry["cpu"] == 18.5`, `device_info["model"] == "C9300-48P"`.
2. `test_get_telemetry_singular_route_alias`:
   - Assert `GET /api/device/edge-sw-01/telemetry` returns identical structure as `/api/devices/...`.
3. `test_get_telemetry_offline_with_cached_state`:
   - Mock DNAC client raising `DNACConnectionError("DNAC unreachable")`.
   - Mock MongoDB returning a previously cached document in `device_telemetry`.
   - Assert `GET /api/devices/edge-sw-01/telemetry` returns 200, `source == "cached_offline"`, `telemetry["reachable"] is False`.
4. `test_get_telemetry_offline_without_cache`:
   - Mock DNAC client raising `DNACConnectionError("DNAC unreachable")`.
   - Mock MongoDB returning `None` for cache.
   - Assert `GET /api/devices/unknown-dev/telemetry` returns 200, `source == "offline"`, `telemetry["cpu"] is None`, `telemetry["reachable"] is False`.
5. `test_get_telemetry_device_not_found`:
   - Mock DNAC client raising `DeviceNotFoundError("missing-sw")`.
   - Assert `GET /api/devices/missing-sw/telemetry` returns 200 with `source == "offline"`.
6. `test_post_live_poll_success`:
   - Mock `check_dashboard_dnac_status` returning `"RESOLVED"`.
   - Mock MongoDB alerts update.
   - Mock `get_device_health` returning fresh vitals.
   - Assert `POST /api/devices/edge-sw-01/live-poll` returns 200, `status == "success"`, `dnac_reachable is True`, `alerts_updated >= 0`.
7. `test_post_live_poll_singular_alias`:
   - Assert `POST /api/device/edge-sw-01/live-poll` works identically.
8. `test_post_live_poll_dnac_offline_graceful`:
   - Mock DNAC client failing with `DNACConnectionError`.
   - Assert `POST /api/devices/edge-sw-01/live-poll` returns 200 with `status == "warning"` and `dnac_reachable is False` (no HTTP 500).
</action>

<acceptance_criteria>
- `tests/test_device_telemetry_api.py` exists with at least 8 distinct test functions covering live, cached, offline, and aliased routes.
- Running `pytest tests/test_device_telemetry_api.py -v` exits with code 0 (all tests pass).
</acceptance_criteria>

---

### Task 4 — Run Verification & Smoke Tests

<read_first>
- `tests/test_device_telemetry_api.py`
- `dashboard/api.py`
</read_first>

<action>
Execute pytest to verify the full suite passes without errors:
```bash
pytest tests/test_device_telemetry_api.py -v
```
Also run an end-to-end import check verifying that `dashboard/api.py` launches cleanly and that both new routes appear in `app.routes`:
```python
python -c "
from dashboard.api import app
route_paths = [r.path for r in app.routes]
assert '/api/devices/{device_name}/telemetry' in route_paths
assert '/api/device/{device_name}/telemetry' in route_paths
assert '/api/devices/{device_name}/live-poll' in route_paths
assert '/api/device/{device_name}/live-poll' in route_paths
print('All 4 routes successfully registered!')
"
```
</action>

<acceptance_criteria>
- `pytest tests/test_device_telemetry_api.py -v` passes with 100% green tests.
- All 4 route paths (`/api/devices/.../telemetry`, `/api/device/.../telemetry`, `/api/devices/.../live-poll`, `/api/device/.../live-poll`) are registered on the FastAPI app.
</acceptance_criteria>

</tasks>

---

## Must-Haves (Goal-Backward Verification)

- **M-01:** `GET /api/devices/{device_name}/telemetry` returns HTTP 200 with keys `device_name`, `device_id`, `source`, `timestamp`, `telemetry` (9 vitals), and `device_info` (5 specs).
- **M-02:** `POST /api/devices/{device_name}/live-poll` triggers live status check on active alerts and refreshes telemetry, returning HTTP 200 with `status`, `device_name`, `dnac_reachable`, `alerts_updated`, `telemetry`, and `timestamp`.
- **M-03:** When DNAC is unreachable or device is missing, endpoints never throw HTTP 500 errors; they return HTTP 200 with `source: 'cached_offline'` or `source: 'offline'`.
- **M-04:** Both `/api/devices/` and `/api/device/` route variants are registered and behave identically.
- **M-05:** `pytest tests/test_device_telemetry_api.py -v` passes with zero failures.
