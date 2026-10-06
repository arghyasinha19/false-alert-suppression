# Roadmap: False Alert Suppression Pipeline

**Milestone:** v2.0 Multi-Site Hierarchical Topology & WAN Observability  
**Status:** In Progress (Planning Phases)  

## Overview

| Phase | Milestone | Name | Goal | Requirements | Status |
|-------|-----------|------|------|--------------|--------|
| 24 | v2.0 | Global Multi-Site WAN Interconnect Canvas | Render interactive macro site nodes, aggregated site health badges, blast radius indicators, and inter-site WAN links | SITE-01, SITE-02, SITE-03 | Complete |
| 25 | v2.0 | Site-Specific LAN Topology Drill-Down & Breadcrumbs | Drill down into site LAN graphs with intuitive breadcrumbs and site-switcher navigation | SITE-04, SITE-05, SITE-06 | Complete |
| 26 | v2.0 | Cross-View Site Synchronization & Filter Alignment | Synchronize site selection and location filtering bi-directionally across Site Matrix, SRE Table, and Topology | SITE-07, SITE-08 | Complete |

---

## Phase 24: Global Multi-Site WAN Interconnect Canvas

**Goal:** Implement Level 1 Global Multi-Site WAN topology map rendering interactive macro site nodes, aggregated site health badges, blast radius indicators, and inter-site WAN links.

**Status:** Complete

**Requirements:**
- **SITE-01**: User can view an interactive Global Multi-Site WAN topology map displaying all registered physical locations/sites as interactive macro nodes interconnected by WAN links.
- **SITE-02**: User can view site-level health rollup badges (`nominal`, `degraded`, `critical`), active alert counts, avoided ticket totals, and blast radius indicators on each macro site node.
- **SITE-03**: User can view inter-site WAN connection links with live health status, latency, and animated packet/flow indicators between interconnected sites.

**Success Criteria:**
1. Operators can view all geographic locations (London, Singapore, New York, Mumbai, etc.) as interactive macro nodes on an SVG WAN interconnect canvas.
2. Each site macro node displays aggregated health status, active alert volume, avoided ticket counts, and blast radius metrics.
3. Inter-site WAN connection links show link health, latency metrics, and animated pulse flows for active data paths.

---

## Phase 25: Site-Specific LAN Topology Drill-Down & Breadcrumbs

**Goal:** Implement Level 2 Site LAN tier graph drill-down with intuitive breadcrumb navigation and site switcher selector.

**Status:** Complete

**Requirements:**
- **SITE-04**: User can drill down into any site from the Global WAN map (via click or site-switcher selector) to view that site's local Core ↔ Distribution ↔ Access tier topology graph.
- **SITE-05**: User can navigate between the Global WAN overview and local site views using responsive breadcrumbs (`Global WAN Interconnect > UK-LON (London)`) with single-click return to global.
- **SITE-06**: User can filter devices within a site's LAN topology while preserving site boundaries and context.

**Success Criteria:**
1. Clicking any site macro node or selecting a site in the site selector drills down into that site's local Core ↔ Distribution ↔ Access LAN graph.
2. Operators can navigate between Global WAN and Site LAN via persistent breadcrumbs with single-click return to the global overview.
3. Filtering by role, health, or search operates cleanly within the active site scope without losing site context.

---

## Phase 26: Cross-View Site Synchronization & Filter Alignment

**Goal:** Synchronize site selection and location filtering bi-directionally across Regional Site Matrix, SRE High-Density Table, and Multi-Site Topology views.

**Status:** Complete

**Requirements:**
- **SITE-07**: Selecting a site in the Regional Site Matrix automatically filters or transitions the Topology view to that site's LAN graph.
- **SITE-08**: Filtering by location in the SRE Table or multi-dimensional filter bar synchronizes with the Topology view's active site scope.

**Success Criteria:**
1. Clicking "Inspect Site" in the Regional Site Matrix automatically switches to the Topology view and drills into that site's LAN graph.
2. Changing the location filter in the SRE Table or filter bar updates the Topology view's active site scope.
3. Automated regression and contract test suite verifies multi-site hierarchy, breadcrumb routing, and cross-view sync.

---

<details>
<summary>✅ Past Milestones (v1.0 - v1.9)</summary>

### v1.0 - v1.7 Foundations, Metrics & Observability
- **Phase 1 (v1.0)**: False Alert Metrics Alignment (`METRIC-01` - `METRIC-05`) — Complete ✓
- **Phase 2 (v1.1)**: Application Bring-Up (`UP-01` - `UP-04`) — Complete ✓
- **Phase 3 (v1.2)**: Custom Date & Time Range Filtering (`TIME-01` - `TIME-04`) — Complete ✓
- **Phase 4 (v1.4)**: Network Operations Responsive Redesign (`NETOPS-01`, `NETOPS-02`) — Complete ✓
- **Phase 5 (v1.4)**: Collapsible Sidebar Rail & Breadcrumbs (`NAV-01`, `NAV-02`) — Complete ✓
- **Phase 6 (v1.4)**: Micro-Interactions & Animated Counters (`ANIM-01`, `ANIM-02`, `STATE-02`) — Complete ✓
- **Phase 7 (v1.4)**: Sticky Tables, Tooltips & Empty States (`TABLE-01`, `TABLE-02`, `STATE-01`) — Complete ✓
- **Phase 8 (v1.4)**: Comprehensive Dark & Light Theme System (`THEME-01`, `THEME-02`) — Complete ✓
- **Phase 9 (v1.5)**: Executive Telemetry & Health KPI Strip (`NOC-KPI-01` - `NOC-KPI-05`) — Complete ✓
- **Phase 10 (v1.5)**: Multi-Mode Representation Engine (`NOC-VIEW-01` - `NOC-VIEW-04`) — Complete ✓
- **Phase 11 (v1.5)**: Multi-Dimensional Filters & Micro-Visualizations (`NOC-VIZ-01` - `NOC-VIZ-04`) — Complete ✓
- **Phase 12 (v1.5)**: Interactive SRE Drawer & Incident Timeline (`NOC-DRAWER-01` - `NOC-DRAWER-03`) — Complete ✓
- **Phase 13 (v1.6)**: DNAC Client Assurance & Device Extensions (`DNAC-01`, `DNAC-02`) — Complete ✓
- **Phase 14 (v1.6)**: Backend Live Polling & Telemetry Endpoints (`DNAC-03`, `DNAC-04`) — Complete ✓
- **Phase 15 (v1.6)**: Frontend SRE Drawer Live Wire-Up (`DNAC-05`, `DNAC-06`) — Complete ✓
- **Phase 16 (v1.7)**: Details Drawer Scrollbar & Viewport Layout (`DRAWER-01` - `DRAWER-03`) — Complete ✓

### v1.8 Interactive Network Topology Graph Diagram
- **Phase 17**: SVG Topology Canvas & Hierarchical Links (`GRAPH-01` - `GRAPH-04`) — Complete ✓
- **Phase 18**: Health Nodes, Filter Sync & SRE Drawer (`GRAPH-05` - `GRAPH-07`) — Complete ✓

### v1.9 UI/UX Audit Remediation
- **Phase 19**: Critical Layout & Status Fixes (`UI-01`, `UI-02`) — Complete ✓
- **Phase 20**: Data Visibility & Bounds (`UI-03`, `UI-04`) — Complete ✓
- **Phase 21**: Trust & Contrast Remediation (`UI-05`, `UI-06`) — Complete ✓
- **Phase 22**: Accessibility & Hit Areas (`UI-07`, `UI-08`, `UI-16`, `UI-17`) — Complete ✓
- **Phase 23**: Craft & Consistency Polish (`UI-09-22`) — Complete ✓

</details>
