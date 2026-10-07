---
phase: 29-diagnostic-root-cause-observability-identity-mapping
plan: 29-02
requirements_completed:
  - DNAC-04
  - DNAC-05
---

# Plan 29-02 Summary: Frontend SRE Drawer Management-Plane Diagnostics & Site Identity Observability

**Execution Date:** 2026-10-07  
**Status:** Completed  
**Requirements Satisfied:** DNAC-04, DNAC-05  

## What Was Done

1. **Frontend SRE Drawer Diagnostics & Identity Resolution (`dashboard/src/NetworkOperations.jsx`)**:
   - Extracted `resolvedSite`: Prioritizes `liveDeviceInfo.site_name`, parsed location path tokens (stripping country prefixes), or cached/alert location.
   - Extracted `resolvedHostname`: Prioritizes authoritative hostname (`liveDeviceInfo.hostname`, `rawNetworkDevice.hostname`, `rawDeviceDetail.nwDeviceName`).
   - Extracted management plane diagnostics:
     - `failureReason`: `SNMP Connectivity Failed`
     - `errorCode`: `NCIM12013` (or `DEV-UNREACHED`)
     - `isIsolated`: Evaluates active node uptime during reachability outage (`Node Active (Uptime: 7d, 18 hours) • Management Plane Isolated`)
     - `diagMessage`: Cisco diagnostic remediation guidance.

2. **Management Plane Diagnostics Card (SRE Drawer Tab 3)**:
   - Added a prominent diagnostic card (`noc-diagnostic-card`) rendered whenever a device experiences reachability or management plane failure.
   - Displays error code badge (`NCIM12013`), failure reason, operating state pill (`● Node Active • Management Plane Isolated`), and controller diagnostic explanation.
   - Prevents operators from mistaking management plane / SNMP polling timeouts for total hardware/power outages.

3. **Authoritative Hostname & Location Placement**:
   - Drawer Header: When `device_name` is an IP (e.g. `10.254.0.93`), displays authoritative hostname `tr-ist-rtr01` as primary title with the IP in monospace subtitle.
   - Location & Placement Card: Surfaces resolved site (`Istanbul`), full DNAC location hierarchy path (`Global/EMEA/TR Istanbul/Umut Street`), and authoritative hostname row.

4. **Automated Contract Tests & Production Build**:
   - Added `test_management_plane_diagnostics_and_site_observability_contract()` in `tests/test_frontend_sre_drawer_contract.py`.
   - All 7 tests in `test_frontend_sre_drawer_contract.py` pass.
   - Frontend build (`npm run build`) in `dashboard` compiled cleanly in 845ms.
