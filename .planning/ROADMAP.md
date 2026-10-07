# Roadmap: False Alert Suppression Pipeline

**Milestone:** v2.1 Real DNAC Telemetry & Production Hardening  
**Status:** In Progress (Planning Phases)  

## Overview

| Phase | Milestone | Name | Goal | Requirements | Status |
|-------|-----------|------|------|--------------|--------|
| 27 | v2.1 | Authoritative DNAC Hardware & Spec Resolution | Parse hardware specs directly from DNAC raw inventory, eliminate synthetic procedural mock bleed-through in SRE drawer | DNAC-01, DNAC-02 | Complete |
| 28 | v2.1 | Live Reachability Cross-Referencing in Alert Verification | Cross-reference live device reachability state in delayed verification, acknowledging UNREACHABLE states instead of premature UNCERTAIN fallback | DNAC-03 | Complete |
| 29 | v2.1 | Diagnostic Root-Cause Observability & Identity Mapping | Surface deep SNMP failure reasons (NCIM12013) in SRE drawer, map IP identifiers to DNAC hostnames and geographical sites | DNAC-04, DNAC-05 | Planned |

---

## Phase 27: Authoritative DNAC Hardware & Spec Resolution

**Goal:** Extract authentic hardware specifications (model, serial, MAC, OS version, IP) directly from DNAC `raw_response.network_device` and `raw_response.device_detail`, and ensure the frontend SRE drawer displays authentic device specs instead of synthetic Catalyst 9300 switch mock values.

**Status:** Complete

**Requirements:**
- **DNAC-01**: Backend `device_service.py` extracts hardware specifications (`model`, `serial`, `mac`, `os_version`, `ip_address`) directly from DNAC `raw_response.network_device` and `raw_response.device_detail`, persisting them to `device_telemetry` and avoiding `Unknown` defaults when raw DNAC inventory data is present.
- **DNAC-02**: Frontend SRE drawer (`NetworkOperations.jsx`) prioritizes live/cached DNAC hardware specs and honest null states over synthetic procedural fallback values, ensuring real router specs (`Cisco 4331 ISR`, `FDO2517M1EG`) are rendered instead of procedural switch placeholders.

**Success Criteria:**
1. Device telemetry endpoint returns accurate hardware specs derived from DNAC `raw_response` even when `device_info` was not pre-populated.
2. SRE Drawer renders real platform ID (`Cisco 4331 Integrated Services Router`), real serial (`FDO2517M1EG`), real MAC (`6C:13:D5:BE:91:F0`), and real OS version (`17.12.8`).
3. Synthetic switch defaults (`Cisco Catalyst 9300-48UXM Switch`, `FCW2530646`, `10.14.76.67`) never display when real DNAC device data exists.

---

## Phase 28: Live Reachability Cross-Referencing in Alert Verification

**Goal:** Enhance alert status verification in `workflow/tools/dnac_status.py` so that alerts on devices with explicit unreachability status are acknowledged directly rather than falling through to UNCERTAIN.

**Status:** Complete

**Requirements:**
- **DNAC-03**: Alert status verification (`workflow/tools/dnac_status.py`) cross-references live device reachability state (`communicationState: UNREACHABLE` / `reachabilityStatus: Unreachable` from `/device-detail` and `/network-device/{id}`) so alerts on unreachable devices are acknowledged rather than defaulting to `UNCERTAIN` when DNAC explicitly confirms the device is unreached.

**Success Criteria:**
1. When Assurance issue endpoint does not match or is unavailable, `check_alert_status` verifies device reachability via `get_device_health()`.
2. Device explicitly marked `UNREACHABLE` with active controller disconnection alert maintains `ACTIVE` alert state rather than falling to `UNCERTAIN`.
3. Background sync `dnac_sync.py` and delayed verification reflect live reachability state accurately.

---

## Phase 29: Diagnostic Root-Cause Observability & Identity Mapping

**Goal:** Surface deep DNAC management plane failure reasons in the SRE drawer (SNMP timeouts, credential errors, uptime) and propagate authoritative hostnames and geographical site locations across the dashboard.

**Status:** Not Started

**Requirements:**
- **DNAC-04**: SRE drawer and NOC device cards surface deep DNAC management-plane failure reasons (`reachabilityFailureReason: SNMP Connectivity Failed`, error code `NCIM12013`, and description), distinguishing SNMP timeouts/credential failures on running devices (uptime > 7 days) from physical node outages.
- **DNAC-05**: Device service and API populate authoritative hostnames (`hostname: tr-ist-rtr01`) when alerts arrive with IP addresses as device names, and extract geographical site names (`Istanbul`) from DNAC location hierarchy paths (`Global/EMEA/TR Istanbul/Umut Street`).

**Success Criteria:**
1. SRE Drawer exhibits a dedicated "Management Plane Diagnostics" card showing SNMP error code (`NCIM12013`), failure reason, and operational uptime (`7 days, 18 hours`).
2. Devices named with IP addresses resolve to their real DNAC hostname (`tr-ist-rtr01`) in device headers, cards, and tables.
3. Geographical location extracts the human-readable site (`Istanbul`) from DNAC hierarchy string instead of repeating the raw IP address.

---

<details>
<summary>✅ Past Milestones (v1.0 - v2.0)</summary>

### v2.0 Multi-Site Hierarchical Topology & WAN Observability
- **Phase 24**: Global Multi-Site WAN Interconnect Canvas (`SITE-01`, `SITE-02`, `SITE-03`) — Complete ✓
- **Phase 25**: Site-Specific LAN Topology Drill-Down & Breadcrumbs (`SITE-04`, `SITE-05`, `SITE-06`) — Complete ✓
- **Phase 26**: Cross-View Site Synchronization & Filter Alignment (`SITE-07`, `SITE-08`) — Complete ✓

### v1.8 - v1.9 Topology Diagram & UI Audit Remediation
- **Phase 17**: SVG Topology Canvas & Hierarchical Links (`GRAPH-01` - `GRAPH-04`) — Complete ✓
- **Phase 18**: Health Nodes, Filter Sync & SRE Drawer (`GRAPH-05` - `GRAPH-07`) — Complete ✓
- **Phase 19 - 23**: UI/UX Audit Remediation (`UI-01` - `UI-22`) — Complete ✓

### v1.0 - v1.7 Foundations, Metrics & Observability
- **Phase 1 - 3**: Metrics Alignment, Bring-Up, Time Filtering — Complete ✓
- **Phase 4 - 8**: UI/UX Overhaul, Sidebar, Themes — Complete ✓
- **Phase 9 - 12**: Executive NOC Overhaul & SRE Drawer — Complete ✓
- **Phase 13 - 16**: Live DNAC Telemetry & Drawer Scrollbar — Complete ✓

</details>

---
*Roadmap defined: 2026-10-07*  
*Last updated: 2026-10-07 after Milestone v2.1 initialization*
