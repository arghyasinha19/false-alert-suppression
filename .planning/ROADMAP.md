# Roadmap: False Alert Suppression Pipeline

**Milestone:** v1.4 Complete UI/UX Expert Audit Implementation  
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

---

## Phase 4: Network Operations Responsive Redesign

**Goal:** Transform the single-column device view into a 2–3 column responsive grid (`repeat(auto-fill, minmax(320px, 1fr))`) that eliminates empty horizontal space, with clean location and infrastructure headers.

**Requirements:**
- **NETOPS-01**: User can view network device inventory in a multi-column responsive grid (2–3 cols, minmax 320px) utilizing full screen width.
- **NETOPS-02**: User can view devices organized under distinct location and infrastructure group headers with device count badges and clean iconography.

**Success Criteria:**
1. Device inventory cards render in a multi-column responsive grid filling available horizontal space rather than a single narrow column. (✓ Verified)
2. Group headers cleanly distinguish geographic sites from infrastructure devices with accurate count badges. (✓ Verified)
3. Device tiles display telemetry, live health status, and SNOW badges cleanly across standard monitor (1707px) and laptop (1366px) viewports. (✓ Verified)

---

## Phase 5: Collapsible Sidebar Rail & Breadcrumbs

**Goal:** Add a sidebar collapse toggle that collapses the 260px sidebar into a 72px compact icon-only rail with floating tooltip labels, and add contextual route breadcrumbs to the top content header.

**Requirements:**
- **NAV-01**: User can toggle the sidebar between 260px expanded and 72px compact icon-only rail with tooltip labels.
- **NAV-02**: User can see a contextual breadcrumb indicator in the top header reflecting the active route.

**Success Criteria:**
1. Clicking the sidebar toggle collapses the sidebar to 72px width while preserving full navigation capability with icon tooltips. (✓ Verified)
2. The main content area expands smoothly to occupy the reclaimed horizontal space. (✓ Verified)
3. The content header displays breadcrumbs showing active context (e.g. `DNAC Ops Center > Alert Metrics`). (✓ Verified)

---

## Phase 6: Micro-Interactions & Animated Counters

**Goal:** Implement an animated numerical count-up effect (`0 → N`) for primary KPI card values, smooth page crossfade transitions, and refined visual styling for ServiceNow Ticket Details.

**Requirements:**
- **ANIM-01**: User sees an animated numerical count-up (`0 → N`) for primary KPI card values on load and refresh.
- **ANIM-02**: User experiences smooth crossfade transitions when switching between sidebar views.
- **STATE-02**: User sees an enhanced section divider and styled badges for ServiceNow Ticket Details.

**Success Criteria:**
1. Numbers in KPI cards animate from 0 to their actual counts with an ease-out curve on initial load and simulated alert ingestion. (✓ Verified)
2. Navigating between pages provides a fluid crossfade transition without flicker. (✓ Verified)
3. The ServiceNow Ticket Details section is demarcated with a polished section divider, icon badge, and clear typographic hierarchy. (✓ Verified)

---

## Phase 7: Sticky Tables, Tooltips & Empty States

**Goal:** Ensure table headers in the Traceability Matrix and Device Rankings remain sticky during scrolling, enforce strict cell truncation with hover tooltips, and provide illustrated empty states for zero-match filters.

**Requirements:**
- **TABLE-01**: User can scroll the Traceability Matrix with sticky column headers staying pinned at the top.
- **TABLE-02**: User can view Device Ranking and Traceability tables with robust cell truncation and hover tooltips.
- **STATE-01**: User sees rich empty state placeholders when filters or searches match 0 items.

**Success Criteria:**
1. Column headers remain pinned to the top of the table scroll viewport while scrolling through all rows. (✓ Verified)
2. Truncated cells show the full text content in a native hover tooltip. (✓ Verified)
3. Applying filters or searches that match 0 items displays a helpful, styled empty state with a "Clear Filters" action. (✓ Verified)

---

## Phase 8: Comprehensive Dark & Light Theme System

**Goal:** Implement a complete Dark / Light theme system with CSS tokens, a header theme toggle switch, and persistence in `localStorage`.

**Requirements:**
- **THEME-01**: User can switch between Light and Dark themes with saved `localStorage` preference.
- **THEME-02**: System applies cohesive dark mode tokens to header backdrops, cards, tables, and dialogs.

**Success Criteria:**
1. A theme toggle button allows instant switching between Light and Dark modes. (✓ Verified)
2. Dark theme provides high-contrast, polished styling across cards, sidebar, tables, charts, and slide-out panels. (✓ Verified)
3. The chosen theme persists across page refreshes and browser sessions. (✓ Verified)
