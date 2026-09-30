# Roadmap: False Alert Suppression Pipeline

**Milestone:** v1.2 Custom Date & Time Range Filtering  
**Status:** In Progress  

## Overview

| Phase | Milestone | Name | Goal | Requirements | Status |
|-------|-----------|------|------|--------------|--------|
| 1 | v1.0 | False Alert Metrics Alignment | Verify and update "Total Processed" calculation and category filtering | METRIC-01 - METRIC-05 | Complete ✓ |
| 2 | v1.1 | Application Bring-Up | Launch Dashboard backend API and Vite frontend, verify live connectivity, and create start orchestration | UP-01 - UP-04 | Complete ✓ |
| 3 | v1.2 | Custom Date & Time Range Filtering | Implement start and end date-time range selection, dynamic scope filtering, and KPI recalculations | TIME-01 - TIME-04 | In Progress |

---

## Phase 3: Custom Date & Time Range Filtering

**Goal:** Implement interactive date and time range inputs in the False Alert Metrics filter bar, evaluate alert timestamps against custom temporal boundaries in `scopeAlerts`, dynamically update KPIs and tables, and provide reset actions.

**Requirements:**
- TIME-01: Add custom start and end date-time picker controls to the filter bar in `FalseAlertMetrics.jsx`.
- TIME-02: Implement custom date-time boundary filtering in `scopeAlerts` evaluating alert timestamps against user-specified start and end limits.
- TIME-03: Ensure KPI summary totals, category breakdowns, and trace matrix dynamically recalculate under custom range filters.
- TIME-04: Provide reset / clear controls and visual cues when custom date-time filtering is active.

**Success Criteria:**
1. Filter dropdown includes a "📅 Custom Range..." option that reveals Start and End `datetime-local` input controls with clear visual styling.
2. Selecting a start date/time and/or end date/time filters `scopeAlerts` precisely according to the temporal boundaries.
3. KPI cards (`Total Processed`, `Tickets Avoided`, `Suppressed`, `Auto-Resolving`, `Non-Auto-Resolving`, `Uncertain`) dynamically recalculate to match the alerts in the custom time window.
4. Traceability table and device distribution charts update immediately without UI stutter or console errors.
5. Clicking the "Clear / Reset" button restores the filter to "⏰ All Time" and hides/clears the custom date inputs.
