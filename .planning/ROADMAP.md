# Roadmap: False Alert Suppression Pipeline

**Milestone:** v1.9 UI/UX Audit Remediation  
**Status:** Planning  

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
| 18 | v1.8 | Health Nodes, Filter Sync & SRE Drawer | Rich micro-cards, pulsing alert indicators, filter reactivity, and drawer integration | GRAPH-05 - GRAPH-07 | Complete ✓ |
| 19 | v1.9 | Critical Layout & Status Fixes | Fix responsive collapse below 1100px and ensure connection status reflects offline states | UI-01, UI-02 | Complete ✓ |
| 20 | v1.9 | Data Visibility & Bounds | Implement persistent scrollbars, table edge masks, and strict independent scroll bounds for the topology graph | UI-03, UI-04 | Not started |
| 21 | v1.9 | Trust & Contrast Remediation | Fix text-tertiary contrast ratios and route chart colors through CSS tokens for dark mode reliability | UI-05, UI-06 | Not started |
| 22 | v1.9 | Accessibility & Hit Areas | Increase hit areas to 32px minimum, fix sidebar keyboard navigation, add aria-current, ensure accessible names | UI-07, UI-08, UI-16, UI-17 | Not started |
| 23 | v1.9 | Craft & Consistency Polish | Standardize typography scale, KPI cards, empty states, and eliminate demo scaffolding | UI-09-UI-22 | Not started |

---

<details>
<summary>✅ v1.0 - v1.7 Past Milestones</summary>

Refer to repository history for prior phase details.
</details>

<details>
<summary>✅ v1.8 Interactive Network Topology Graph Diagram (Phases 17-18) — SHIPPED 2026-10-05</summary>

- [x] **Phase 17: SVG Topology Canvas & Hierarchical Links** (1/1 plan) — completed 2026-10-05
- [x] **Phase 18: Health Nodes, Filter Sync & SRE Drawer** (1/1 plan) — completed 2026-10-05
</details>

---

## Phase 19: Critical Layout & Status Fixes

**Goal:** Fix the 1100px breakpoint collapse in `.content-area` and ensure the API connection status correctly reflects offline states instead of returning false positives.

**Status:** Complete ✓ (2/2 plans complete)
- [x] **Plan 19-01**: Fluid Flexbox Layout & 1100px Breakpoint Stabilization (UI-01)
- [x] **Plan 19-02**: Authoritative Connection State Machine, Polling Resiliency & Mock Demarcation (UI-02)

**Requirements:**
- **UI-01**: Fix responsive collapse below 1100px in the `.content-area` by removing `calc(100vw - ...)` constraints and letting flexbox size it correctly.
- **UI-02**: Sidebar connection status must accurately reflect API failures by explicitly handling fetch errors, updating the "LIVE" badge to "Stale" on failure, and properly separating mock data from live status.

**Success Criteria:**
1. The `.content-area` scales fluidly below 1100px without shrinking to a sliver.
2. The connection status explicitly displays "Offline" when the API is down and handles empty JSON correctly.
3. The dashboard clearly demarcates mock data from live telemetry when in offline mode.

---

## Phase 20: Data Visibility & Bounds

**Goal:** Implement persistent scrollbars, table edge masks, and strict independent scroll bounds for the topology graph canvas.

**Status:** Not started

**Requirements:**
- **UI-03**: Constrain the topology graph canvas to its own bounds with independent scroll and zoom containers to prevent overflowing the main window.
- **UI-04**: Add permanently visible scrollbars to data tables, implement right-edge gradient masks on horizontally scrolling tables, and explicitly cap vertical lists.

**Success Criteria:**
1. All scrollable regions have persistently visible scrollbars (not just on hover).
2. Overflowing tables clearly show edge masking indicating more content.
3. The topology graph is bounded to its container and does not create an inaccessible horizontal/vertical overflow on the entire window.

---

## Phase 21: Trust & Contrast Remediation

**Goal:** Fix `text-tertiary` contrast ratios, route chart colours through CSS tokens for dark mode reliability, and ensure text contrast passes minimums.

**Status:** Not started

**Requirements:**
- **UI-05**: Adjust `text-tertiary` to meet contrast minimums (`#64748b` in light mode, `#94a3b8` in dark mode) and darken blue pill text to pass AA contrast.
- **UI-06**: Refactor charts to use CSS tokens from `index.css` via `getComputedStyle` or a theme palette object, ensuring chart legends, grids, and axes integrate with dark mode.

**Success Criteria:**
1. Secondary text throughout the application passes AA contrast limits.
2. SVG charts dynamically pull their colors from the CSS variables to match active themes properly.
3. Contrast errors highlighted in UI-05 and UI-06 are fully resolved.

---

## Phase 22: Accessibility & Hit Areas

**Goal:** Increase interactive hit areas to 32px minimum, fix sidebar keyboard navigation, add `aria-current`, and ensure tables/forms have accessible names.

**Status:** Not started

**Requirements:**
- **UI-07**: Increase all interactive element (buttons, pills, selects) minimum heights to 32px with 44px hit areas, and raise table/filter typography to 12-13px.
- **UI-08**: Update the Ops Assistant chat panel to be non-modal (inset the content area) or properly manage focus and dim the backdrop.
- **UI-16**: Update sidebar navigation to use real `<button>` elements, add `aria-current="page"`, add a `:focus-visible` ring, and trigger tooltips on focus.
- **UI-17**: Ensure all form controls have visible labels, add `scope="col"` to table headers, and provide visually-hidden captions per table.

**Success Criteria:**
1. Interactive hit areas conform to WCAG limits.
2. Sidebar navigation is accessible entirely via keyboard (Tab and Enter).
3. The chat panel either shifts content seamlessly or implements strict modal focus trapping + backdrop dimming.
4. Screen readers announce clear accessible names for forms and tables.

---

## Phase 23: Craft & Consistency Polish

**Goal:** Standardize typography scale, KPI card designs, empty states, and eliminate demo scaffolding from the chrome.

**Status:** Not started

**Requirements:**
- **UI-09-22**: Address medium-priority inconsistencies including scaling typography (12/13/15/18/24/34), standardizing KPI cards to the NOC card design, clarifying domain shorthand, unifying empty states, and removing demo simulation scaffolding.

**Success Criteria:**
1. App uses 6 strict typography font sizes.
2. Unified KPI card design utilized universally across NOC and Metric views.
3. Unneeded demo buttons removed.
4. Empty states standardized across all tables and charts.
