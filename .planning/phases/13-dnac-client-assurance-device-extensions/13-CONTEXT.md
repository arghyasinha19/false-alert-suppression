# Phase 13: DNAC Client Assurance & Device Extensions - Context

**Gathered:** 2026-10-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 13 extends `app/dnac_client.py` with two new query methods on `DNACClient`:

1. **`get_device_by_name_or_ip(device_name_or_ip: str) -> list[dict]`** — queries `GET /dna/intent/api/v1/network-device` with smart parameter routing (hostname vs IP detection) and returns a list of matching device dicts. Raises `DeviceNotFoundError` on zero matches; raises `DNACConnectionError` on network/HTTP errors.

2. **`get_device_health(device_id: str) -> dict`** — queries `GET /dna/intent/api/v1/device-health` by device UUID and returns a normalized dict of telemetry vitals. Raises `DNACConnectionError` if DNAC cannot return health data.

Additionally:
- **New `app/exceptions.py`** module housing `DeviceNotFoundError` and `DNACConnectionError`.
- **Token retry-once retrofit** into existing methods (`get_issue_status`, `get_device_issues`) plus new methods.
- **Integration tests** in `tests/` marked `@pytest.mark.integration` that hit the real DNAC at `https://10.48.200.53`.

No frontend or API endpoint changes in this phase (those belong to Phases 14-15).
</domain>

<decisions>
## Implementation Decisions

### Device Lookup Contract (get_device_by_name_or_ip)
- **D-01 (Return type):** Returns `List[dict]` always. If DNAC returns 2+ matches, all are returned — the caller decides which to use.
- **D-02 (Zero matches):** Raises `DeviceNotFoundError` (from `app/exceptions.py`) with the queried identifier in the message.
- **D-03 (Network/HTTP errors):** Catches and re-raises as `DNACConnectionError`. Distinguishes "device not in DNAC" from "DNAC is unreachable".
- **D-04 (Query param routing):** Detect IPv4 with `re.fullmatch(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', value)`. If yes, use `?managementIpAddress={value}`; otherwise use `?hostname={value}`.
- **D-05 (Response shape):** Each dict contains curated snake_case keys (device_name, ip_address, model, os_version, serial, mac, reachable, device_id) PLUS a `raw_response` key with the full original DNAC object.

### Token Refresh Strategy
- **D-06 (Retry-once-on-401):** Private helper `_request_with_retry(method, url, **kwargs)`. On 401: set `self.token = None`, call `self.authenticate()`, retry once. If retry still 401, raise.
- **D-07 (Retrofit scope):** Retrofit the retry logic to existing methods `get_issue_status` and `get_device_issues` in this phase too.

### Health API Query Form (get_device_health)
- **D-08 (Input):** Accepts UUID only (`device_id: str`). Callers must resolve hostname to UUID first via `get_device_by_name_or_ip()`.
- **D-09 (Failure):** Raises `DNACConnectionError` on 404 or 5xx. No offline fallback dict.
- **D-10 (Telemetry fields):** Returns: cpu_utilization (%), memory_utilization (%), packet_drop (%), health_score (0-10), interface_error_count, poe_status, uptime_seconds, reachable (bool), raw_response.

### Return Type Shape and Exceptions
- **D-11 (Plain dicts):** Both methods return plain dict / List[dict]. No TypedDicts or dataclasses.
- **D-12 (Exception location):** New `app/exceptions.py` with `DNACError(Exception)` base class, `DeviceNotFoundError(DNACError)`, and `DNACConnectionError(DNACError)`.

### Testing
- **D-13 (Integration tests only):** `tests/test_dnac_client_integration.py` with `@pytest.mark.integration`. Hits real DNAC at `https://10.48.200.53`. CI skips automatically.
- **D-14 (Test scope):** Auth, device lookup by hostname, by IP, DeviceNotFoundError on fake name, get_device_health valid UUID, DNACConnectionError invalid UUID, 401 retry behavior.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing DNAC Client
- `app/dnac_client.py` — Existing DNACClient class. New methods add here; existing methods retrofitted.

### DNAC Monitor (Config Loading Pattern)
- `dashboard/dnac_monitor.py` — Shows how DNACClient is loaded from config.yaml.

### Configuration
- `config.yaml` — dnac.base_url (https://10.48.200.53), dnac.verify_ssl.
- `.env.example` — DNAC_USERNAME, DNAC_PASSWORD env vars.

### Requirements
- `.planning/REQUIREMENTS.md` — DNAC-01 and DNAC-02 requirements.
- `.planning/ROADMAP.md` — Phase 13 success criteria.

### Codebase Map
- `.planning/codebase/INTEGRATIONS.md` — DNAC API endpoint inventory (Section: Network Assurance).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `DNACClient._get_headers()` — Auth headers with lazy token fetch.
- `DNACClient.authenticate()` — Token fetch logic; called by retry mechanism.
- `get_device_issues()` — Response unwrap pattern (data.get("response", data)); same pattern for new methods.

### Established Patterns
- Auth: X-Auth-Token header, lazily fetched. Phase 13 adds explicit 401 retry.
- SSL: `verify=self.verify_ssl` on every requests call.
- Logging: "DNAC Request:" before, "DNAC Response:" after. New methods follow exact format.
- Response unwrap: `data.get("response", data)` for DNAC envelope.

### Integration Points
- `app/exceptions.py` (new) imported by `app/dnac_client.py` and future `dashboard/api.py` (Phase 14).
- `tests/test_dnac_client_integration.py` (new) runs against live DNAC.

</code_context>

<specifics>
## Specific Ideas

- `_request_with_retry()` should be a generic private helper wrapping GET/POST/DELETE to avoid copy-paste.
- `DeviceNotFoundError` message: `f"No device found in DNAC matching: {device_name_or_ip}"`.
- `DNACConnectionError` message includes HTTP status or exception message for debuggability.
- Use `re.fullmatch` (not `re.match`) for strict IPv4 detection.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 13-dnac-client-assurance-device-extensions*
*Context gathered: 2026-10-05*
