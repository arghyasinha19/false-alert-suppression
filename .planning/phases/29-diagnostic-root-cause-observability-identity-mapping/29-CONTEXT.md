# Phase 29: Diagnostic Root-Cause Observability & Identity Mapping - Context

**Gathered:** 2026-10-07  
**Status:** Ready for planning  
**Mode:** Smart Plan (Phase 29 Execution)  
**Requirements:** DNAC-04, DNAC-05  

<domain>
## Phase Boundary

Surface deep Cisco DNA Center management plane failure reasons (SNMP Connectivity Failed, error code NCIM12013 / DEV-UNREACHED, timeout diagnostics, and uptime contrast) in the SRE drawer to clearly distinguish management plane timeouts on running devices from physical node outages (`DNAC-04`). Propagate authoritative hostnames (`tr-ist-rtr01`) when alerts arrive with IP addresses as device identifiers, and extract geographical site names (`Istanbul`) from DNAC location hierarchy paths (`Global/EMEA/TR Istanbul/Umut Street`) across dashboard inventory and cards (`DNAC-05`).
</domain>

<decisions>
## Implementation Decisions

### Area 1: Backend Diagnostics & Identity Extraction (`DNAC-04`, `DNAC-05`)
- **Management Plane Diagnostics in `dashboard/device_service.py`**:
  - In `extract_device_info_from_raw(raw_response, fallback_info)`:
    - Extract `reachability_failure_reason`: `inv.get("reachabilityFailureReason")` (e.g. `"SNMP Connectivity Failed"`).
    - Extract `error_code`: `inv.get("errorCode")` or assign `"NCIM12013"` when failure is SNMP-related.
    - Extract `diagnostic_message`: Detailed description (`"SNMP request timeout. Device may be unreachable or SNMP credentials configured on device may be different from Catalyst Center credentials."`).
    - Compute `is_management_plane_isolated`: True when device `uptimeSeconds > 300` (e.g. 692,019 seconds / ~8 days) while `reachabilityStatus` is `"Unreachable"`. This signals to operators that the data plane is active and the router is running, but management plane polling timed out.
- **Authoritative Identity & Geographical Site Resolution (`DNAC-05`)**:
  - Extract `location_path` from `det.get("location")` or `inv.get("locationName")` (e.g. `"Global/EMEA/TR Istanbul/Umut Street"`).
  - Implement `extract_site_from_location_path(location_path)`:
    - Parses hierarchy parts, removes country prefixes (`"TR Istanbul"` -> `"Istanbul"`), returning clean site names like `"Istanbul"`.
  - Extract `hostname` (`"tr-ist-rtr01"`), and when an alert or device entry has an IP string (`"10.254.0.93"`) as its primary key, make `hostname` prominent and searchable.

### Area 2: Frontend SRE Drawer & NOC Cards (`DNAC-04`, `DNAC-05`)
- **SRE Drawer Diagnostics Card in `dashboard/src/NetworkOperations.jsx`**:
  - When `vitals.diagnostics` or raw reachability data indicates management plane failure:
    - Render a prominent **Management Plane Diagnostics** card (amber / warning accent).
    - Surface:
      - Diagnostic Type: `"Management Plane Failure (SNMP Timeout)"`
      - Error Code: `NCIM12013` (badge)
      - Failure Reason: `"SNMP Connectivity Failed"`
      - Operating State: `"Node Running (Uptime: 7d 18h) • Management Plane Isolated"`
      - Remediation Hint: `"Verify SNMPv2c/v3 community strings and ACLs on device interface."`
- **Location & Hostname Card Enhancements**:
  - In "Network Location & Placement" card:
    - Display authoritative `Site`: `"Istanbul"` (with tooltip showing full DNAC hierarchy path `Global/EMEA/TR Istanbul/Umut Street`).
    - Display `Hostname`: `"tr-ist-rtr01"`.
  - In device list / table view, display resolved hostname alongside management IP.

### Area 3: Automated Testing & Validation
- Update `tests/test_device_telemetry_api.py` with tests for:
  - Extraction of `diagnostics` (`reachability_failure_reason`, `error_code`, `is_management_plane_isolated`).
  - Parsing and extraction of clean `site_name` from hierarchical DNAC location paths.
- Update `tests/test_frontend_sre_drawer_contract.py` with assertions for:
  - Management plane diagnostics card rendering and `NCIM12013` code display.
  - Authoritative hostname and site location resolution in SRE drawer.
- Ensure production build passes with `npm run build`.
</decisions>

<code_context>
## Existing Code Insights

- `dashboard/device_service.py`: `extract_device_info_from_raw()` extracts device specs.
- `dashboard/src/NetworkOperations.jsx`: Lines 2000-2050 render inventory and placement cards in SRE Drawer Tab 1.
- `tests/test_device_telemetry_api.py`: Tests telemetry endpoint and raw response parsing.
- `tests/test_frontend_sre_drawer_contract.py`: Contract tests for SRE drawer elements.
</code_context>
