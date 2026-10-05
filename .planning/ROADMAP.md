# Roadmap: False Alert Suppression Pipeline

**Milestone:** v1.8 Interactive Network Topology Graph Diagram  
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
| 11 | v1.5 | Multi-Dimensional Filters & Micro-Visualizations | Role & Health filter chips, 24h activity sparklines, severity mini-bars, and status pulses | NOC-VIZ-01 - NOC-VIZ-04 | Complete ✓ |
| 12 | v1.5 | Interactive SRE Drawer & Incident Timeline | Multi-agent decision timeline, Assurance telemetry tabs, and one-click quick triage actions | NOC-DRAWER-01 - NOC-DRAWER-03 | Complete ✓ |
| 13 | v1.6 | DNAC Client Assurance & Device Extensions | Implement `/network-device` and `/device-health` query methods in `DNACClient` | DNAC-01, DNAC-02 | Complete ✓ |
| 14 | v1.6 | Backend Live Polling & Telemetry Endpoints | Add `/api/devices/{name}/telemetry` and `/api/devices/{name}/live-poll` endpoints | DNAC-03, DNAC-04 | Complete ✓ |
| 15 | v1.6 | Frontend SRE Drawer Live Wire-Up | Connect drawer telemetry/inventory tabs and Poll DNAC button to live API with fallback | DNAC-05, DNAC-06 | Complete ✓ |
| 16 | v1.7 | Details Drawer Scrollbar & Viewport Layout | Accessible, visible, theme-aware scrollbars and fixed-header flex layout for device details drawer | DRAWER-01 - DRAWER-03 | Complete ✓ |
| 17 | v1.8 | SVG Topology Canvas & Hierarchical Links | Zoomable/pannable SVG graph canvas, hierarchical tier placement, and animated connection links | GRAPH-01 - GRAPH-04 | Complete ✓ |
| 18 | v1.8 | Health Nodes, Filter Sync & SRE Drawer | Rich micro-cards, pulsing alert indicators, filter reactivity, and drawer integration | GRAPH-05 - GRAPH-07 | Planned |



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

**Status:** Complete ✓

**Requirements:**
- **NOC-VIZ-01**: User can filter device inventory by Role chips (All, Core, Distribution, Access, Wireless, Security). (✓ Verified)
- **NOC-VIZ-02**: User can filter by Health status chips (All, Healthy, Warning, Critical) and ServiceNow ticket state. (✓ Verified)
- **NOC-VIZ-03**: User can see a 24-hour alert distribution micro-bar/sparkline on each device card showing activity volume over time. (✓ Verified)
- **NOC-VIZ-04**: User can see live severity distribution mini-bars and pulsing status indicators for active alerts. (✓ Verified)

**Success Criteria:**
1. Filter bar features clickable pill chips for Role and Health with instant reactive filtering. (✓ Verified)
2. Device cards display SVG/canvas micro-visualizations representing recent alert distributions. (✓ Verified)
3. Critical and warning devices display visual pulse animations denoting active incident state. (✓ Verified)

---

## Phase 12: Interactive SRE Investigation Drawer & Incident Timeline

**Goal:** Elevate the device slide-out panel into an enterprise SRE triage workstation with an interactive chronological multi-agent decision timeline (Ingest → Agent 1 → Agent 2 → Agent 3 → Agent 4), Assurance telemetry vitals tabs, and one-click triage actions.

**Status:** Complete ✓

**Requirements:**
- **NOC-DRAWER-01**: User can view an interactive, multi-agent chronological decision timeline for each alert (Ingestion → Agent 1 Backdate → Agent 2 ML Transience → Agent 3 DLX Queue → Agent 4 ServiceNow). (✓ Verified)
- **NOC-DRAWER-02**: User can inspect live Cisco DNA Center Assurance telemetry attributes, device health vitals, and raw payload details in dedicated tabs. (✓ Verified)
- **NOC-DRAWER-03**: User can perform quick triage actions (e.g., Copy Incident, Simulate Alert on Device, Trigger Re-check) directly from the drawer. (✓ Verified)

**Success Criteria:**
1. Clicking any device opens a drawer containing a visual multi-agent decision timeline for active alerts. (✓ Verified)
2. Tabbed navigation inside drawer exposes Overview, Active Alerts, Chronological Timeline, and Assurance Telemetry. (✓ Verified)
3. Action buttons allow quick triage (e.g. copying incident ticket details, simulating new alert for device). (✓ Verified)

---

<details>
<summary>✅ v1.6 Live DNAC Assurance Telemetry & Asset Integration (Phases 13-15) — SHIPPED 2026-10-05</summary>

Full archive: [.planning/milestones/v1.6-ROADMAP.md](milestones/v1.6-ROADMAP.md)

- [x] **Phase 13: DNAC Client Assurance & Device Extensions** (1/1 plan) — completed 2026-10-05
- [x] **Phase 14: Backend Live Polling & Telemetry Endpoints** (1/1 plan) — completed 2026-10-05
- [x] **Phase 15: Frontend SRE Drawer Live Wire-Up** (1/1 plan) — completed 2026-10-05

</details>

<details>
<summary>✅ v1.7 NOC Details Drawer Scrollbar & Usability Polish (Phase 16) — SHIPPED 2026-10-05</summary>

- [x] **Phase 16: Details Drawer Scrollbar & Viewport Layout** (1/1 plan) — completed 2026-10-05

</details>

---

## Phase 17: SVG Topology Canvas & Hierarchical Links

**Goal:** Implement the interactive SVG network topology graph canvas with smooth pan/zoom controls, deterministic 3-tier coordinate calculation (Core, Distribution & Security, Access Edge), and animated connection links with traffic pulses and link health states.

**Status:** Complete ✓

**Requirements:**
- **GRAPH-01**: User can view network devices in an interactive, zoomable and pannable SVG canvas graph diagram with smooth mouse wheel zooming, drag-to-pan, and fit-to-screen controls. (✓ Verified)
- **GRAPH-02**: Canvas provides floating navigation controls (Zoom In, Zoom Out, Fit to View, Reset 100%) and a fast sub-mode toggle between Graph View and Card Grid View. (✓ Verified)
- **GRAPH-03**: Devices are arranged into 3 distinct hierarchical network tiers (Core & WAN Backbone at top, Distribution & Security in middle, Campus & Access Edge at bottom) with subtle background tier lanes. (✓ Verified)
- **GRAPH-04**: Interconnected network links (edges) connect upstream and downstream devices with health-aware styling (teal for nominal, amber for warning, red for critical) and subtle animated traffic pulses. (✓ Verified)

**Success Criteria:**
1. Navigating to "Topology" displays an interactive SVG graph canvas with floating zoom controls (+, -, fit, 100%). (✓ Verified)
2. Mouse drag pans the canvas smoothly, and mouse wheel adjusts zoom level with bounded limits (0.4x to 2.2x). (✓ Verified)
3. Devices are clearly grouped into 3 horizontal tier lanes: Core at top, Distribution/Security in middle, Access Edge at bottom. (✓ Verified)
4. Smooth bezier links connect Core routers to Distribution switches and Distribution to Access nodes, with color coding matching network link health. (✓ Verified)
5. Operators can toggle between "Graph View" and "Card Grid View" with a single click. (✓ Verified)

---

## Phase 18: Health Nodes, Filter Sync & SRE Drawer

**Goal:** Complete the interactive graph experience by rendering rich micro-cards for device nodes, animating health status pulses for critical incidents, connecting toolbar filters (Role, Health, Search) to reactive node dimming, and integrating node clicks with the slide-out SRE details drawer.

**Status:** Planned

**Requirements:**
- **GRAPH-05**: Device nodes render as rich micro-cards with role icons, hostnames, management IPs, health status dots (including pulsing red for critical), and active alert count badges.
- **GRAPH-06**: Clicking any device node on the graph canvas opens the 580px slide-out SRE details drawer for that device with glowing selection highlight.
- **GRAPH-07**: Node rendering reactively adapts to active Role, Health, and search query filters by highlighting matches and dimming non-matches.

**Success Criteria:**
1. Each device node renders as a modern, glassmorphic micro-card with device name, role icon, IP, and health indicator dot.
2. Nodes with active critical alerts display an animated radar pulse indicator.
3. Clicking any node selects it with a glowing accent ring and immediately opens the 580px SRE details drawer with full Alert Triage, Live Telemetry, Inventory, and Action Bar capabilities.
4. Using Role, Health, or Search filters keeps matching nodes in full brightness while smoothly dimming non-matching nodes to 20% opacity.
5. All automated contract tests pass and the production Vite bundle compiles cleanly with 0 errors.

