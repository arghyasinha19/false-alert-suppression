# Phase 28: Live Reachability Cross-Referencing in Alert Verification - Context

**Gathered:** 2026-10-07  
**Status:** Ready for planning  
**Mode:** Smart Plan (Phase 28 Execution)  
**Requirements:** DNAC-03  

<domain>
## Phase Boundary

Enhance alert status verification in `workflow/tools/dnac_status.py` so that alerts on devices with explicit unreachability state in Cisco DNA Center (`communicationState: UNREACHABLE` / `reachabilityStatus: Unreachable` from `/device-detail` and `/network-device/{id}`) are acknowledged as `ACTIVE` rather than falling through to `UNCERTAIN`. Ensure delayed verification (`workflow/delayed.py`) and background sync (`dashboard/dnac_sync.py`) reflect live reachability state accurately without altering ML model classification weights or prompt logic.
</domain>

<decisions>
## Implementation Decisions

### Area 1: Alert Status Verification Reachability Cross-Referencing (`DNAC-03`)
- **Fallback to Live Device Reachability in `workflow/tools/dnac_status.py`**:
  - In `check_alert_status()`, if primary `issue_id` lookup does not resolve to an active or closed issue, and device-scoped Assurance scan (`get_device_issues()`) finds no matching issue:
    1. Cross-reference device reachability by calling `client.get_device_health(device_id)`.
    2. Check both high-level `health["reachable"]` and deep raw response fields:
       - `raw_response.network_device.reachabilityStatus` (`"Unreachable"`)
       - `raw_response.device_detail.communicationState` (`"UNREACHABLE"`)
       - `raw_response.network_device.reachabilityFailureReason` (e.g., `"SNMP Connectivity Failed"`)
       - `raw_response.network_device.errorCode` (`"DEV-UNREACHED"`)
    3. If the device is explicitly confirmed unreachable:
       - Return `ACTIVE`. This acknowledges the active network fault / reachability issue, preventing it from defaulting to `UNCERTAIN`.
    4. If the device is explicitly confirmed reachable (`reachable is True`):
       - If the incoming alert was a reachability-related alert (`_is_reachability_alert(issue_name)`) and Assurance reports zero active issues:
         - Return `RESOLVED`. The transient reachability blip has cleared.
       - If the incoming alert was a domain-specific issue (e.g., `"BGP peer down"`, `"Fan failure"`, `"Interface error"`) that is not tracked by overall device reachability:
         - Retain `UNCERTAIN` (preserving backwards compatibility and escalating to ServiceNow).
- **Missing `device_id` Auto-Resolution**:
  - If `device_id` is not supplied but `device_name` is provided (e.g., IP address `10.254.0.93` or hostname `tr-ist-rtr01`), call `client.get_device_by_name_or_ip(device_name)` before failing to `UNCERTAIN`. If resolved, proceed with the device-scoped scan and reachability cross-reference.

### Area 2: Integration with Delayed Verification & Background Sync
- **Delayed Verification Flow (`workflow/delayed.py`)**:
  - Ensure `run_delayed_check(alert)` passes normalized `device_name=alert.get("device_name") or alert.get("device")`, `device_id=alert.get("device_id")`, and `issue_id=alert.get("issue_id") or alert.get("instance_id")`.
  - When `check_alert_status` returns `ACTIVE` for an unreachable device, delayed check marks it as `Non-Auto Resolving` and cleanly escalates to ServiceNow.
- **Background Sync (`dashboard/dnac_sync.py`)**:
  - Automatically benefits from `check_alert_status` enhancement through `check_dashboard_dnac_status`, writing `dnac_live_status: "ACTIVE"` to MongoDB for unreachable devices instead of leaving them in `"UNCERTAIN"`.

### Area 3: Testing & Regression Invariants
- Retain 100% pass rate for existing `test_dnac_fallback.py` tests.
- Add dedicated test suite `tests/test_live_reachability_verification.py` verifying:
  - Unreachable device with Assurance issue absent -> returns `ACTIVE`.
  - Unreachable device with SNMP timeout failure -> returns `ACTIVE`.
  - Auto-resolving reachability alert on restored device (`reachable: True`) -> returns `RESOLVED`.
  - Domain-specific non-reachability alert on reachable device with no match -> returns `UNCERTAIN`.
  - Auto-resolution of `device_id` from `device_name`.
  - Delayed check escalation behavior in `workflow/delayed.py`.
</decisions>

<code_context>
## Existing Code Insights

- `workflow/tools/dnac_status.py`: Lines 71-127 define `check_alert_status()` and fallback order.
- `app/dnac_client.py`: Lines 447-553 define `get_device_health()` returning `{"reachable": bool, "health_score": int, "raw_response": {"device_detail": ..., "network_device": ...}}`.
- `workflow/delayed.py`: Lines 21-61 define `run_delayed_check()` which calls `check_alert_status()`.
- `dashboard/dnac_sync.py`: Uses `check_dashboard_dnac_status()` which delegates to `check_alert_status()`.
- `test_dnac_fallback.py`: Tests `check_alert_status` fallbacks.
</code_context>
