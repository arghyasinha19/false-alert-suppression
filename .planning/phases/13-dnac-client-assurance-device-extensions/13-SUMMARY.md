# Phase 13: DNAC Client Assurance & Device Extensions — Summary

**Status:** Complete
**Commit:** d03217b
**Date:** 2026-10-05

## One-liner

Extended DNACClient with device inventory lookup + live health telemetry methods, added a shared exceptions module, retrofitted 401 token retry into all client methods, and wrote a full integration test suite against the live DNAC appliance.

## What Was Built

### New: `app/exceptions.py`
Three-class exception hierarchy:
- `DNACError(Exception)` — base for all DNAC client errors
- `DeviceNotFoundError(DNACError)` — raised when zero devices match a hostname/IP query; stores `.identifier` attribute
- `DNACConnectionError(DNACError)` — raised on network errors, HTTP 4xx/5xx, and empty response conditions

### Modified: `app/dnac_client.py`

**New imports:** `import re` + `from app.exceptions import DeviceNotFoundError, DNACConnectionError`

**New private method — `_request_with_retry(method, url, **kwargs)`:**
- Wraps `requests.request()` with automatic one-shot 401 recovery
- On 401: clears `self.token`, calls `self.authenticate()`, retries once
- If retry still 401, returns response as-is for caller to handle

**Retrofitted existing methods:**
- `get_issue_status`: replaced direct `requests.get` with `_request_with_retry("GET", url)`
- `get_device_issues`: replaced direct `requests.get` with `_request_with_retry("GET", url, params=params)`

**New method — `get_device_by_name_or_ip(device_name_or_ip: str) -> list`:**
- Auto-detects IPv4 vs hostname via `re.fullmatch(r"\d{1,3}\....")`
- Routes to `?managementIpAddress=` or `?hostname=` accordingly
- Returns `List[dict]` with 9 curated snake_case keys + `raw_response`
- Raises `DeviceNotFoundError` on zero results
- Raises `DNACConnectionError` on network/HTTP errors

**New method — `get_device_health(device_id: str) -> dict`:**
- Accepts DNAC UUID only (`GET /dna/intent/api/v1/device-health?deviceId=`)
- Handles both list and dict DNAC response shapes
- Returns 9-key normalized telemetry dict (cpu, memory, packet_drop, health_score, interface_error_count, poe_status, uptime_seconds, reachable, raw_response)
- Numeric fields coerced to `float`/`int` or `None` via safe helpers
- Raises `DNACConnectionError` on 404, 5xx, or empty list response

### New: `tests/test_dnac_client_integration.py`
7 integration tests, all `@pytest.mark.integration`:
1. `test_authenticate_returns_token` — token is non-empty string, cached
2. `test_get_device_by_hostname` — lookup by hostname returns all 9 keys
3. `test_get_device_by_ip` — lookup by IPv4 routes correctly
4. `test_get_device_by_fake_hostname_raises_device_not_found` — raises `DeviceNotFoundError`
5. `test_get_device_health_valid_uuid` — returns 9-key dict, types verified
6. `test_get_device_health_invalid_uuid_raises_connection_error` — raises `DNACConnectionError`
7. `test_token_retry_on_401` — corrupt token triggers re-auth transparently

Tests skip automatically when `DNAC_USERNAME` is not set (CI-safe).

## Decisions Implemented

All decisions from `13-CONTEXT.md` honored: D-01 through D-14.

## Files Changed

| Action | File |
|--------|------|
| CREATED | `app/exceptions.py` |
| MODIFIED | `app/dnac_client.py` |
| CREATED | `tests/test_dnac_client_integration.py` |

## Smoke Test

```
[OK] app/exceptions.py — all assertions passed
[OK] app/dnac_client.py — all methods present, imports clean
```

---

*Phase 13 complete — 2026-10-05*
