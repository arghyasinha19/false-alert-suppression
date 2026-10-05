# Phase 14: Backend Live Polling & Telemetry Endpoints — Summary

**Status:** Complete  
**Commit:** `ce4b2d6`  
**Date:** 2026-10-05  

## One-liner

Implemented FastAPI live Assurance telemetry lookup and on-demand device status polling in `dashboard/api.py` backed by `dashboard/device_service.py`, with MongoDB caching in `device_telemetry`, graceful offline fallbacks, dual singular/plural route aliases, and a comprehensive test suite.

## What Was Built

### New: `dashboard/device_service.py`
- **`get_or_resolve_device_id(device_name, mongo_client, dnac_client)`**: Two-tier resolution checking MongoDB `device_telemetry` and `alert_results` caches first, supporting raw 36-char UUIDs, and falling back to `DNACClient.get_device_by_name_or_ip(device_name)`.
- **`fetch_device_telemetry(device_name, mongo_client, dnac_client)`**: Retrieves normalized 9-key vitals (`cpu`, `memory`, `packet_drop`, `health_score`, `interface_error_count`, `poe_status`, `uptime_seconds`, `reachable`, `raw_response`) and hardware specs (`model`, `serial`, `mac`, `os_version`, `ip_address`). Caches live results in MongoDB collection `device_telemetry`. Falls back to `source: "cached_offline"` or `source: "offline"` with null vitals and `reachable: false` on failure.
- **`poll_device_live(device_name, mongo_client, dnac_client)`**: Synchronously re-evaluates all active, non-backdated alerts for the device via `check_dashboard_dnac_status`, updates `dnac_live_status` and `dnac_last_checked` in MongoDB `alert_results`, fetches fresh telemetry vitals, and returns consolidated state.

### Modified: `dashboard/api.py`
- Registered `GET /api/devices/{device_name}/telemetry` and alias `GET /api/device/{device_name}/telemetry`.
- Registered `POST /api/devices/{device_name}/live-poll` and alias `POST /api/device/{device_name}/live-poll`.
- Internalized error handling so external DNAC connection drops return informative HTTP 200 payloads rather than unhandled 500 errors.

### New: `tests/test_device_telemetry_api.py`
8 unit and integration test scenarios verified with `TestClient`:
1. `test_get_telemetry_live_success` — Live DNAC health retrieval returns 200 with `source: 'dnac_live'`.
2. `test_get_telemetry_singular_route_alias` — `/api/device/{name}/telemetry` alias behaves identically to `/api/devices/...`.
3. `test_get_telemetry_offline_with_cached_state` — Unreachable DNAC falls back to last-known cached state with `source: 'cached_offline'`.
4. `test_get_telemetry_offline_without_cache` — Missing cache returns null vitals with `source: 'offline'` and `reachable: false`.
5. `test_get_telemetry_device_not_found` — `DeviceNotFoundError` yields graceful offline fallback.
6. `test_post_live_poll_success` — Live poll re-checks alerts in MongoDB, updates statuses, and returns fresh vitals.
7. `test_post_live_poll_singular_alias` — `/api/device/{name}/live-poll` alias verified.
8. `test_post_live_poll_dnac_offline_graceful` — Unreachable DNAC during live poll returns `status: "warning"` with `dnac_reachable: false` (no HTTP 500).

## Requirements Delivered

- **DNAC-03**: Backend endpoint `GET /api/devices/{device_name}/telemetry` returns structured live DNAC vitals with `source: "dnac_live" | "cached_offline" | "offline"` and timestamp. (✓ Verified)
- **DNAC-04**: Backend endpoint `POST /api/devices/{device_name}/live-poll` triggers an immediate on-demand DNAC issue and telemetry refresh, returning updated device state. (✓ Verified)

## Decisions Implemented

All decisions from `14-CONTEXT.md` honored: D-01 through D-10.

## Files Changed

| Action | File |
|---|---|
| CREATED | `dashboard/device_service.py` |
| MODIFIED | `dashboard/api.py` |
| CREATED | `tests/test_device_telemetry_api.py` |

## Test Verification

```
tests/test_device_telemetry_api.py::test_get_telemetry_live_success PASSED
tests/test_device_telemetry_api.py::test_get_telemetry_singular_route_alias PASSED
tests/test_device_telemetry_api.py::test_get_telemetry_offline_with_cached_state PASSED
tests/test_device_telemetry_api.py::test_get_telemetry_offline_without_cache PASSED
tests/test_device_telemetry_api.py::test_get_telemetry_device_not_found PASSED
tests/test_device_telemetry_api.py::test_post_live_poll_success PASSED
tests/test_device_telemetry_api.py::test_post_live_poll_singular_alias PASSED
tests/test_device_telemetry_api.py::test_post_live_poll_dnac_offline_graceful PASSED

============================== 8 passed in 6.16s ==============================
```

---

*Phase 14 complete — 2026-10-05*
