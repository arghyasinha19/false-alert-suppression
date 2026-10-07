# Requirements: False Alert Suppression Pipeline

**Defined:** 2026-10-07  
**Milestone:** v2.1 Real DNAC Telemetry & Production Hardening  
**Core Value:** Accurately identify false or transient network alerts to prevent unnecessary ServiceNow ticket creation and reduce operational noise without missing genuine network degradation.

## Milestone v2.1 Requirements: Real DNAC Telemetry & Production Hardening

### DNAC Hardware & Spec Resolution (DNAC-SPEC)
- [x] **DNAC-01**: Backend `device_service.py` extracts hardware specifications (`model`, `serial`, `mac`, `os_version`, `ip_address`) directly from DNAC `raw_response.network_device` and `raw_response.device_detail`, persisting them to `device_telemetry` and avoiding `Unknown` defaults when raw DNAC inventory data is present.
- [x] **DNAC-02**: Frontend SRE drawer (`NetworkOperations.jsx`) prioritizes live/cached DNAC hardware specs and honest null states over synthetic procedural fallback values, ensuring real router specs (`Cisco 4331 ISR`, `FDO2517M1EG`) are rendered instead of procedural switch placeholders.

### Live Reachability & Alert Verification Alignment (DNAC-REACH)
- [x] **DNAC-03**: Alert status verification (`workflow/tools/dnac_status.py`) cross-references live device reachability state (`communicationState: UNREACHABLE` / `reachabilityStatus: Unreachable` from `/device-detail` and `/network-device/{id}`) so alerts on unreachable devices are acknowledged rather than defaulting to `UNCERTAIN` when DNAC explicitly confirms the device is unreached.

### Diagnostic Root-Cause Observability (DNAC-DIAG)
- [x] **DNAC-04**: SRE drawer and NOC device cards surface deep DNAC management-plane failure reasons (`reachabilityFailureReason: SNMP Connectivity Failed`, error code `NCIM12013`, and description), distinguishing SNMP timeouts/credential failures on running devices (uptime > 7 days) from physical node outages.

### Authoritative Identity & Location Mapping (DNAC-ID)
- [x] **DNAC-05**: Device service and API populate authoritative hostnames (`hostname: tr-ist-rtr01`) when alerts arrive with IP addresses as device names, and extract geographical site names (`Istanbul`) from DNAC location hierarchy paths (`Global/EMEA/TR Istanbul/Umut Street`).

## Future Requirements

- Real-time WebSockets streaming updates for telemetry metrics instead of polling.
- Multi-tenancy support for partitioned customer network views.
- Dynamic interface flap timeline graph per port.
- User-customizable drag-and-drop node pinning with layout state persisted in localStorage.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Retraining ML classification model for controller unreachability | Explicitly excluded per user instructions; ML model and alert category logic remain unchanged. |
| Altering DNAC RBAC or making unauthenticated calls | Must always use standard token auth (`POST /dna/system/api/v1/auth/token`). |
| External CMDB database sync beyond DNAC and ServiceNow | Ingested and cached DNAC telemetry is the single source of network truth. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DNAC-01 | Phase 27 | Complete |
| DNAC-02 | Phase 27 | Complete |
| DNAC-03 | Phase 28 | Complete |
| DNAC-04 | Phase 29 | Complete |
| DNAC-05 | Phase 29 | Complete |

**Coverage:**
- v2.1 requirements: 5 total
- Satisfied: 5 (100.0%)
- Pending: 0 (0.0%)

---
*Requirements defined: 2026-10-07*  
*Last updated: 2026-10-07 after Milestone v2.1 initialization*
