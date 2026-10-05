# Phase 14: Backend Live Polling & Telemetry Endpoints - Context

**Gathered:** 2026-10-05  
**Status:** Ready for planning  

<domain>
## Phase Boundary

Phase 14 implements live telemetry lookup and on-demand live polling endpoints in `dashboard/api.py`:
1. `GET /api/devices/{device_name}/telemetry` (and alias `GET /api/device/{device_name}/telemetry`)
2. `POST /api/devices/{device_name}/live-poll` (and alias `POST /api/device/{device_name}/live-poll`)

These endpoints integrate:
- `app/dnac_client.py` (`get_device_by_name_or_ip`, `get_device_health`, `get_device_issues`)
- `dashboard/dnac_monitor.py` (`check_dashboard_dnac_status`, `_load_dnac_client`)
- MongoDB storage (`device_telemetry` collection for caching telemetry and UUID mapping, `alert_results` for alert status updates)
- Graceful offline fallbacks that never throw HTTP 500 errors when DNAC is unreachable or device is missing.

No frontend changes in this phase (frontend integration is Phase 15).  
No daemon startup or CLI test tool changes in this phase (those belong to Phase 16).
</domain>

<decisions>
## Implementation Decisions

### Telemetry Fallback & Offline Cache (GET /api/devices/{device_name}/telemetry)
- **D-01 (Offline fallback):** When DNAC is unreachable or device is missing, the endpoint returns HTTP 200 with an empty/null telemetry vitals dictionary and `source: 'offline'` (unless a cached record exists in `device_telemetry`).
- **D-02 (MongoDB caching):** Successful live DNAC telemetry fetches are cached in MongoDB collection `device_telemetry` with a timestamp and device metadata. If a subsequent live fetch fails, the cached record is returned with `source: 'cached_offline'`. If neither live nor cache is available, returns `source: 'offline'` with null vitals.

### Device Identifier & UUID Resolution
- **D-03 (Two-tier resolution):** When resolving `{device_name}` into DNAC's internal UUID:
  1. Check MongoDB cache (`device_telemetry` or `alert_results.alert_details.device_id`) for existing UUID mapping.
  2. If not found in cache, call `DNACClient.get_device_by_name_or_ip(device_name)` to retrieve device inventory and extract `device_id`.
  3. If `{device_name}` already matches UUID format (36-char string), query `get_device_health` directly.
  4. Cache the resolved UUID mapping in `device_telemetry` for future fast lookups.

### Live Poll Execution Scope (POST /api/devices/{device_name}/live-poll)
- **D-04 (Full live sync):** Live poll synchronously re-verifies active alert statuses on that device against DNAC and refreshes hardware telemetry vitals in a single call.
- **D-05 (Alert status mutation):** For all active alerts belonging to `{device_name}` in MongoDB, call `check_dashboard_dnac_status`, update `dnac_live_status` (`RESOLVED`, `ACTIVE`, `UNCERTAIN`) and `dnac_last_checked` in MongoDB `alert_results`.
- **D-06 (Telemetry refresh):** Call `get_device_health` for the device and update `device_telemetry` in MongoDB.
- **D-07 (Consolidated response):** Returns a consolidated device state object containing `status: "success" | "warning"`, `device_name`, `telemetry`, `device_info`, `alerts_updated` count, `dnac_reachable: bool`, and `timestamp`. If DNAC fails, returns `status: "warning"` with `dnac_reachable: false` and error message without throwing HTTP 500.

### Response Payload Schema & Route Aliasing
- **D-08 (Unified payload):** `GET /api/devices/{device_name}/telemetry` returns a unified JSON structure containing:
  - `device_name`: str
  - `device_id`: str (UUID)
  - `source`: `"dnac_live"` | `"cached_offline"` | `"offline"`
  - `timestamp`: ISO-8601 string
  - `telemetry`: 9-key vitals dictionary (`cpu`, `memory`, `packet_drop`, `health_score`, `interface_error_count`, `poe_status`, `uptime_seconds`, `reachable`, `raw_response`)
  - `device_info`: Hardware inventory dictionary (`model`, `serial`, `mac`, `os_version`, `ip_address`)
- **D-09 (Route aliasing):** Dual-register both `/api/devices/{device_name}/...` and `/api/device/{device_name}/...` for both endpoints (`/telemetry` and `/live-poll`) to ensure complete compatibility with frontend calls and existing singular routes (e.g. `/api/device/{device_name}/history`).

### Exceptions & Error Handling
- **D-10 (No 500 errors):** Catch `DNACError`, `DeviceNotFoundError`, and `DNACConnectionError` from `app.exceptions`. Translate to graceful HTTP 200 fallback payloads with `source: 'offline'` or `dnac_reachable: false`.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing API Endpoints
- `dashboard/api.py` — Existing FastAPI endpoints for alerts, simulation, and device history. Endpoints will be added here.

### DNAC Client & Exceptions
- `app/dnac_client.py` — `DNACClient` with `get_device_by_name_or_ip()` and `get_device_health()`.
- `app/exceptions.py` — `DNACError`, `DeviceNotFoundError`, `DNACConnectionError`.

### DNAC Monitor & Sync
- `dashboard/dnac_monitor.py` — `_load_dnac_client()` and `check_dashboard_dnac_status()`.
- `dashboard/dnac_sync.py` — MongoDB update pattern for `dnac_live_status` and `dnac_last_checked`.

### Database
- `workflow/tools/mongodb_client.py` — `MongoDBClient` connection helper.

### Requirements & Roadmap
- `.planning/REQUIREMENTS.md` — Requirements DNAC-03 and DNAC-04.
- `.planning/ROADMAP.md` — Phase 14 goals and success criteria.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_load_dnac_client()` in `dashboard/dnac_monitor.py` — Safely instantiates `DNACClient` from `config.yaml`, returning None on failure.
- `check_dashboard_dnac_status()` in `dashboard/dnac_monitor.py` — Checks DNAC status for an issue and returns `"ACTIVE"`, `"RESOLVED"`, or `"UNCERTAIN"` without raising.
- `mongo.get_collection("alert_results")` in `dashboard/api.py` — Pattern for accessing MongoDB collections with fallback handling.

### Established Patterns
- Safe helper: `safe_get(d, *keys, default=None)` in `dashboard/api.py`.
- MongoDB alert update: `collection.update_one({"alert_details.event_id": event_id}, {"$set": {...}})` from `dnac_sync.py`.
- Non-blocking fallbacks: If MongoDB or external services fail, return clean JSON without crashing the server.

### Integration Points
- `dashboard/api.py` registers new FastAPI endpoints.
- New MongoDB collection: `device_telemetry` stores cached telemetry documents indexed by `device_name`.

</code_context>

<specifics>
## Specific Ideas

- Return ISO-8601 UTC timestamps via `datetime.now(timezone.utc).isoformat()`.
- Ensure `device_info` fields map cleanly to the UI labels needed by the SRE drawer (model, serial, MAC, OS version, management IP).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed strictly within the Phase 14 backend domain.

</deferred>

---

*Phase: 14-backend-live-polling-telemetry-endpoints*  
*Context gathered: 2026-10-05*  
