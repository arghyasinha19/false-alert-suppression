# Requirements: False Alert Suppression Pipeline

**Defined:** 2026-10-01  
**Milestone:** v1.5 Executive & Observability Network Operations Center (NOC) Overhaul  
**Core Value:** Accurately identify false or transient network alerts to prevent unnecessary ServiceNow ticket creation and reduce operational noise without missing genuine network degradation.

## Milestone v1.5 Requirements: Executive & Observability NOC Overhaul

### Executive Telemetry & Health KPIs (NOC-KPI)
- [x] **NOC-KPI-01**: User can view Fleet Health Score (% index based on weighted device operational availability) with animated counter.
- [x] **NOC-KPI-02**: User can view False Alert Noise Reduction / Suppression Rate (%) at fleet level.
- [x] **NOC-KPI-03**: User can view Active Incident Blast Radius (# affected sites & degraded devices).
- [x] **NOC-KPI-04**: User can view Mean Resolution Velocity / MTTA metric for auto-resolved vs escalated incidents.
- [x] **NOC-KPI-05**: User can view Site Resilience Ratio (e.g. 8/9 Nominal sites) in the top executive summary strip.

### Multi-Mode Representation Engine (NOC-VIEW)
- [x] **NOC-VIEW-01**: User can toggle between 3 presentation modes: "Executive Topology", "SRE High-Density Table", and "Regional Site Matrix" with seamless animated state switching.
- [x] **NOC-VIEW-02**: In Executive Topology view, devices are organized by network infrastructure tier (Core & WAN, Distribution & Security, Campus & Access) with roll-up health indicators.
- [x] **NOC-VIEW-03**: In SRE High-Density Table view, user can sort by device name, active alerts, severity, last seen, and health with inline status chips and sticky headers.
- [x] **NOC-VIEW-04**: In Regional Site Matrix view, user can view site-level health status cards with quick-click filtering by site.

### Filter Bar & Micro-Visualizations (NOC-VIZ)
- [x] **NOC-VIZ-01**: User can filter device inventory by Role chips (All, Core, Distribution, Access, Wireless, Security).
- [x] **NOC-VIZ-02**: User can filter by Health status chips (All, Healthy, Warning, Critical) and ServiceNow ticket state.
- [x] **NOC-VIZ-03**: User can see a 24-hour alert distribution micro-bar/sparkline on each device card showing activity volume over time.
- [x] **NOC-VIZ-04**: User can see live severity distribution mini-bars and pulsing status indicators for active alerts.

### Interactive SRE Investigation Drawer (NOC-DRAWER)
- [x] **NOC-DRAWER-01**: User can view an interactive, multi-agent chronological decision timeline for each alert (Ingestion → Agent 1 Backdate → Agent 2 ML Transience → Agent 3 DLX Queue → Agent 4 ServiceNow).
- [x] **NOC-DRAWER-02**: User can inspect live Cisco DNA Center Assurance telemetry attributes, device health vitals, and raw payload details in dedicated tabs.
- [x] **NOC-DRAWER-03**: User can perform quick triage actions (e.g., Copy Incident, Simulate Alert on Device, Trigger Re-check) directly from the drawer.

## Future Requirements

- Real-time WebSockets streaming updates instead of polling interval.
- Geographic interactive vector map (Leaflet or Mapbox).
- Multi-tenancy support for partitioned customer network views.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Modifying ML training checkpoints or models | Handled in dedicated ML training pipeline workflows; this milestone focuses on observability, representations, and NOC UX. |
| Third-party heavy charting libraries (e.g. D3, Highcharts) | Dashboard uses lightweight SVG sparklines and Recharts aligned with design tokens. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| NOC-KPI-01 | Phase 9 | Complete ✓ |
| NOC-KPI-02 | Phase 9 | Complete ✓ |
| NOC-KPI-03 | Phase 9 | Complete ✓ |
| NOC-KPI-04 | Phase 9 | Complete ✓ |
| NOC-KPI-05 | Phase 9 | Complete ✓ |
| NOC-VIEW-01 | Phase 10 | Complete ✓ |
| NOC-VIEW-02 | Phase 10 | Complete ✓ |
| NOC-VIEW-03 | Phase 10 | Complete ✓ |
| NOC-VIEW-04 | Phase 10 | Complete ✓ |
| NOC-VIZ-01 | Phase 11 | Complete ✓ |
| NOC-VIZ-02 | Phase 11 | Complete ✓ |
| NOC-VIZ-03 | Phase 11 | Complete ✓ |
| NOC-VIZ-04 | Phase 11 | Complete ✓ |
| NOC-DRAWER-01 | Phase 12 | Complete ✓ |
| NOC-DRAWER-02 | Phase 12 | Complete ✓ |
| NOC-DRAWER-03 | Phase 12 | Complete ✓ |

**Coverage:**
- v1.5 requirements: 16 total
- Mapped to phases: 16 (100%)
- Unmapped: 0 ✓

---
*Requirements defined: 2026-10-01*  
*Last updated: 2026-10-01 after Milestone v1.5 requirements definition*
