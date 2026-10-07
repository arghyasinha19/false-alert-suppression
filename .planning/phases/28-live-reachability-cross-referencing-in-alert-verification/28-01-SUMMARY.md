---
phase: 28-live-reachability-cross-referencing-in-alert-verification
plan: 28-01
requirements_completed:
  - DNAC-03
---

# Plan 28-01 Summary: Live Reachability Cross-Referencing in Alert Verification

**Execution Date:** 2026-10-07  
**Status:** Completed  
**Requirements Satisfied:** DNAC-03  

## What Was Done

1. **Live Reachability Fallback in `workflow/tools/dnac_status.py` (`DNAC-03`)**:
   - Defined `_REACHABILITY_KEYWORDS` recognizer matching reachability/connectivity keywords (`unreachable`, `reachability`, `connectivity`, `connection timeout`, `ping`, `offline`, `disconnect`, `dev-unreached`, `ncim12013`, `device down`, `node down`).
   - Added auto-resolution of missing `device_id` from `device_name` (hostname or IP) via `client.get_device_by_name_or_ip()`.
   - Cross-referenced live device reachability state using `client.get_device_health(device_id)` when Assurance issues return no exact match:
     - If the device is explicitly confirmed unreachable (`health.get("reachable") is False`, `reachabilityStatus == "Unreachable"`, `communicationState == "UNREACHABLE"`, or failure reason is present), acknowledges the alert as **`ACTIVE`** instead of falling through to `UNCERTAIN`.
     - If the device is confirmed reachable (`health.get("reachable") is True`) and the alert is a reachability-type alert with zero active issues in DNAC, returns **`RESOLVED`** (handling auto-resolving reachability blips).
     - If the device is reachable but the alert is a domain-specific issue (e.g., BGP peer down) with no match, returns **`UNCERTAIN`** to escalate to ServiceNow.
     - Gracefully catches exceptions from `get_device_health()` and logs warnings while returning `UNCERTAIN`.

2. **Delayed Verification Parameter Forwarding (`workflow/delayed.py`)**:
   - Updated `run_delayed_check()` to forward normalized `device_name=alert.get("device_name") or alert.get("device")` and `issue_id=alert.get("issue_id") or alert.get("instance_id")`.
   - Ensured that when `check_alert_status` returns `ACTIVE` for unreachable devices, delayed check cleanly classifies the incident as `Non-Auto Resolving` and escalates to ServiceNow.

3. **Production Hardening Test Isolation (`tests/test_prod_hardening.py`)**:
   - Enhanced `_isolate` fixture to guarantee `DNAC_USERNAME`, `DNAC_PASSWORD`, `RABBITMQ_USERNAME`, and `RABBITMQ_PASSWORD` environment variables are reliably restored across all test runs.

4. **Dedicated Test Suite & Verification**:
   - Created `tests/test_live_reachability_verification.py` with 8 comprehensive unit and flow tests covering:
     - Unreachable device returns `ACTIVE` when Assurance issues empty.
     - Device with SNMP timeout `NCIM12013` returns `ACTIVE`.
     - Any alert on unreachable node returns `ACTIVE`.
     - Restored device returns `RESOLVED` for cleared reachability alert.
     - Unmatched domain alert returns `UNCERTAIN`.
     - Auto-resolution of `device_id` by hostname/IP.
     - Exception handling returns `UNCERTAIN`.
     - Delayed check flow escalates as `Non-Auto Resolving`.
   - Ran combined regression suite: 54 tests passed in 12.58s with 0 failures (`test_device_telemetry_api.py`, `test_frontend_sre_drawer_contract.py`, `test_prod_hardening.py`, `test_live_reachability_verification.py`, `test_dnac_fallback.py`).
   - Ran `dashboard` build (`vite build`): compiled cleanly in 820ms.
