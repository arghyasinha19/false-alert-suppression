# Roadmap: False Alert Suppression Pipeline

**Milestone:** v1.5 Executive & Observability Network Operations Center (NOC) Overhaul  
**Status:** In Progress  

## Overview

| Phase | Milestone | Name | Goal | Requirements | Status |
|-------|-----------|------|------|--------------|--------|
| 1 | v1.0 | False Alert Metrics Alignment | Verify and update "Total Processed" calculation and category filtering | METRIC-01 - METRIC-05 | Complete ✓ |
| 2 | v1.1 | Application Bring-Up | Launch Dashboard backend API and Vite frontend, verify live connectivity, and create start orchestration | UP-01 - UP-04 | Complete ✓ |
| 3 | v1.2 | Custom Date & Time Range Filtering | Implement start and end date-time range selection, dynamic scope filtering, and KPI recalculations | TIME-01 - TIME-04 | Complete ✓ |
| 4 | v1.4 | Network Operations Responsive Redesign | Multi-column responsive device grid, eliminate whitespace waste, location grouping | NETOPS-01, NETOPS-02 | Complete ✓ |
| 5 | v1.4 | Collapsible Sidebar Rail & Breadcrumbs | 72px icon rail collapse toggle with tooltips & top header route breadcrumbs | NAV-01, NAV-02 | Complete ✓ |
| 6 | v1.4 | Micro-Interactions & Animated Counters | Animated KPI number count-up (`0 → N`), page crossfades, SNOW divider styling | ANIM-01, ANIM-02, STATE-02 | Complete ✓ |
| 7 | v1.4 | Sticky Tables, Tooltips & Empty States | Sticky table headers, cell tooltips, rich zero-match empty state views | TABLE-01, TABLE-02, STATE-01 | Complete ✓ |
| 8 | v1.4 | Comprehensive Dark & Light Theme System | System-wide theme toggle (Sun/Moon), CSS tokens, localStorage persistence | THEME-01, THEME-02 | Complete ✓ |
| 9 | v1.5 | Executive Telemetry & Health KPI Strip | Fleet Health Score %, Noise Suppression Ratio, Blast Radius, MTTR, and Site Resilience | NOC-KPI-01 - NOC-KPI-05 | Complete ✓ |
| 10 | v1.5 | Multi-Mode Representation Engine | Executive Topology, SRE High-Density Sortable Table, and Regional Site Matrix | NOC-VIEW-01 - NOC-VIEW-04 | Complete ✓ |
| 11 | v1.5 | Multi-Dimensional Filters & Micro-Visualizations | Role & Health filter chips, 24h activity sparklines, severity mini-bars, and status pulses | NOC-VIZ-01 - NOC-VIZ-04 | Pending |
| 12 | v1.5 | Interactive SRE Drawer & Incident Timeline | Multi-agent decision timeline, Assurance telemetry tabs, and one-click quick triage actions | NOC-DRAWER-01 - NOC-DRAWER-03 | Pending |

---

## Phase 9: Executive Telemetry & Health KPI Strip

**Goal:** Transform the top summary grid into an enterprise-grade Executive & Observability telemetry strip featuring Fleet Health Score (% index), Noise Suppression Rate (%), Active Blast Radius, Mean Time to Auto-Resolution, and Site Resilience Ratio with animated counters.

**Status:** Complete ✓

**Requirements:**
- **NOC-KPI-01**: User can view Fleet Health Score (% index based on weighted device operational availability) with animated counter. (✓ Verified)
- **NOC-KPI-02**: User can view False Alert Noise Reduction / Suppression Rate (%) at fleet level. (✓ Verified)
- **NOC-KPI-03**: User can view Active Incident Blast Radius (# affected sites & degraded devices). (✓ Verified)
- **NOC-KPI-04**: User can view Mean Resolution Velocity / MTTA metric for auto-resolved vs escalated incidents. (✓ Verified)
- **NOC-KPI-05**: User can view Site Resilience Ratio (e.g. 8/9 Nominal sites) in the top executive summary strip. (✓ Verified)

**Success Criteria:**
1. Top summary grid displays 5 executive observability KPI cards with icons, subtitles, and animated counters (`0 → N`). (✓ Verified)
2. Fleet Health Score calculates weighted availability reflecting critical vs warning device impacts. (✓ Verified)
3. Noise Suppression Rate clearly illustrates the percentage of alerts suppressed or auto-resolved at the network edge. (✓ Verified)
4. Blast Radius and Site Resilience indicate regional operational health at a glance. (✓ Verified)

---

## Phase 10: Multi-Mode Representation Engine

**Goal:** Provide 3 distinct representation modes for Network Operations: "Executive Topology" (infrastructure tier grouping), "SRE High-Density Table" (sortable telemetry table), and "Regional Site Matrix" (site status cards) with fluid view switching.

**Status:** Complete ✓

**Requirements:**
- **NOC-VIEW-01**: User can toggle between 3 presentation modes: "Executive Topology", "SRE High-Density Table", and "Regional Site Matrix" with seamless animated state switching. (✓ Verified)
- **NOC-VIEW-02**: In Executive Topology view, devices are organized by network infrastructure tier (Core & WAN, Distribution & Security, Campus & Access) with roll-up health indicators. (✓ Verified)
- **NOC-VIEW-03**: In SRE High-Density Table view, user can sort by device name, active alerts, severity, last seen, and health with inline status chips and sticky headers. (✓ Verified)
- **NOC-VIEW-04**: In Regional Site Matrix view, user can view site-level health status cards with quick-click filtering by site. (✓ Verified)

**Success Criteria:**
1. A segmented view switcher allows instant toggling between Executive Topology, SRE High-Density Table, and Regional Site Matrix. (✓ Verified)
2. Executive Topology cleanly groups devices by tier with roll-up health metrics. (✓ Verified)
3. SRE Table presents high-density rows with sorting on key metrics, sticky headers, and quick pagination or clean scrolling. (✓ Verified)
4. Regional Site Matrix provides an executive geo-site health view. (✓ Verified)

---

## Phase 11: Multi-Dimensional Filters & Micro-Visualizations

**Goal:** Provide rapid triage filtering across Device Roles, Health states, and ServiceNow tickets, augmented with device card micro-visualizations including 24-hour activity sparklines and severity breakdown mini-bars.

**Requirements:**
- **NOC-VIZ-01**: User can filter device inventory by Role chips (All, Core, Distribution, Access, Wireless, Security).
- **NOC-VIZ-02**: User can filter by Health status chips (All, Healthy, Warning, Critical) and ServiceNow ticket state.
- **NOC-VIZ-03**: User can see a 24-hour alert distribution micro-bar/sparkline on each device card showing activity volume over time.
- **NOC-VIZ-04**: User can see live severity distribution mini-bars and pulsing status indicators for active alerts.

**Success Criteria:**
1. Filter bar features clickable pill chips for Role and Health with instant reactive filtering.
2. Device cards display SVG/canvas micro-visualizations representing recent alert distributions.
3. Critical and warning devices display visual pulse animations denoting active incident state.

---

## Phase 12: Interactive SRE Investigation Drawer & Incident Timeline

**Goal:** Elevate the device slide-out panel into an enterprise SRE triage workstation with an interactive chronological multi-agent decision timeline (Ingest → Agent 1 → Agent 2 → Agent 3 → Agent 4), Assurance telemetry vitals tabs, and one-click triage actions.

**Requirements:**
- **NOC-DRAWER-01**: User can view an interactive, multi-agent chronological decision timeline for each alert (Ingestion → Agent 1 Backdate → Agent 2 ML Transience → Agent 3 DLX Queue → Agent 4 ServiceNow).
- **NOC-DRAWER-02**: User can inspect live Cisco DNA Center Assurance telemetry attributes, device health vitals, and raw payload details in dedicated tabs.
- **NOC-DRAWER-03**: User can perform quick triage actions (e.g., Copy Incident, Simulate Alert on Device, Trigger Re-check) directly from the drawer.

**Success Criteria:**
1. Clicking any device opens a drawer containing a visual multi-agent decision timeline for active alerts.
2. Tabbed navigation inside drawer exposes Overview, Active Alerts, Chronological Timeline, and Assurance Telemetry.
3. Action buttons allow quick triage (e.g. copying incident ticket details, simulating new alert for device).
