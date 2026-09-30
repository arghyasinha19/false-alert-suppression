# Roadmap: False Alert Suppression Pipeline

**Milestone:** v1.0 False Alert Metrics Alignment  
**Created:** 2026-09-30  
**Status:** In Progress  

## Overview

| Phase | Name | Goal | Requirements | Status |
|-------|------|------|--------------|--------|
| 1 | False Alert Metrics Alignment | Verify and update "Total Processed" calculation, ensure category sum consistency, and improve category filter interaction in False Alert Metrics | METRIC-01, METRIC-02, METRIC-03, METRIC-04, METRIC-05 | In Progress |

---

## Phase 1: False Alert Metrics Alignment

**Goal:** Ensure the "Total Processed" field in False Alert Metrics strictly reflects the total number of alerts processed by the system (the sum of Suppressed, Auto-Resolving, Non-Auto-Resolving, and Uncertain alerts), preserves total system counts during category filtering, and ensures backend KPI consistency.

**Requirements:**
- METRIC-01: "Total Processed" equals sum of `Suppressed + Auto-Resolving + Non-Auto-Resolving + Uncertain`.
- METRIC-02: "Tickets Avoided" verified as derived metric (`Suppressed + Auto-Resolving`).
- METRIC-03: "Total Processed" KPI card displays total system alert volume with filtered sub-value when category filter is active.
- METRIC-04: Row 2 category KPI cards support toggle selection with active visual styling without resetting other category metrics to zero.
- METRIC-05: Backend KPI summary verification in `api.py` and `chat_agent.py`.

**Success Criteria:**
1. "Total Processed" displays the exact sum of all 4 categories (`Suppressed + Auto-Resolving + Non-Auto-Resolving + Uncertain`).
2. Selecting a category filter (e.g., clicking "Auto-Resolving" or "Backdated / Suppressed") filters the table matrix and charts while maintaining the total processed count on the KPI cards.
3. Clicking a category KPI card again toggles back to 'ALL'.
4. "Tickets Avoided" is clearly defined as `Suppressed + Auto-Resolving`, avoiding duplicate counting.
5. All UI builds pass without syntax errors or broken imports.
