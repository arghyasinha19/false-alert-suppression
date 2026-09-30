# Phase 1 Plan: False Alert Metrics Alignment

## Objective
Verify and update the "Total Processed" metric in False Alert Metrics to accurately equal the sum of all mutually exclusive alert classification outcomes (`Suppressed + Auto-Resolving + Non-Auto-Resolving + Uncertain`). Ensure that "Tickets Avoided" is properly derived as `Suppressed + Auto-Resolving` (avoiding double-counting). Ensure that selecting a category filter maintains the total system processed count on the "Total Processed" card (with an active filtered sub-value badge) and toggles category filter states on the Row 2 KPI cards without zeroing out other category metrics.

## Implementation Tasks

### Task 1: Separate Scope Filtering and Category Filtering in `FalseAlertMetrics.jsx`
- Define `scopeAlerts`: alerts matching `deviceFilter` and `timeRange` (represents the full alert volume within the chosen scope).
- Define `filteredAlerts`: `scopeAlerts` matching `categoryFilter` (used for table and detail views).
- Compute `kpi` metrics from `scopeAlerts`:
  - `backdated` (Suppressed): count where `results.agent_1.data.is_backdated` is true.
  - `autoResolving`: count where not backdated and `results.agent_2.data.predicted_category` is 'auto resolving'.
  - `nonAutoResolving`: count where not backdated and `results.agent_2.data.predicted_category` is 'non-auto resolving'.
  - `uncertain`: count where not backdated and not auto/non-auto resolving.
  - `total`: strictly `backdated + autoResolving + nonAutoResolving + uncertain` (which equals `scopeAlerts.length`).
  - `ticketsAvoided`: `backdated + autoResolving`.
  - `suppressionRate`: `total > 0 ? ((ticketsAvoided) / total * 100).toFixed(1) : 0`.
  - `filteredCount`: `filteredAlerts.length`.

### Task 2: Enhance KPI Cards Display and Toggle Behavior
- "Total Processed" Card:
  - Display `{kpi.total}`.
  - If `categoryFilter !== 'ALL'`, display sub-value: `"{filteredCount} {categoryLabel} filtered ({kpi.total} total ingested)"`.
  - Otherwise, display: `"{kpi.total} alerts ingested"`.
- "Tickets Avoided" Card:
  - Display `{kpi.ticketsAvoided}`.
  - Sub-value: `"SNOW tickets prevented ({kpi.backdated} suppressed + {kpi.autoResolving} auto-resolved)"`.
- Row 2 Category KPI Cards:
  - Add `active` class when `categoryFilter` matches that card's category.
  - Toggle category filter on click (`onClick={() => setCategoryFilter(f => f === TARGET ? 'ALL' : TARGET)}`).
  - Keep category volume numbers visible (`{kpi.backdated}`, `{kpi.autoResolving}`, `{kpi.nonAutoResolving}`, `{kpi.uncertain}`) so the user always sees the breakdown that sums to Total Processed.

### Task 3: Verify Backend KPI Consistency
- Review `dashboard/api.py` and `dashboard/chat_agent.py` to ensure `total_alerts` strictly equals `backdated + auto_resolving + non_auto_resolving + uncertain`.

### Task 4: Validation & Testing
- Run test simulations and verify that:
  - `kpi.total === kpi.backdated + kpi.autoResolving + kpi.nonAutoResolving + kpi.uncertain`.
  - `kpi.ticketsAvoided === kpi.backdated + kpi.autoResolving`.
  - Clicking category cards toggles filtering and keeps the total count visible.
  - Vite build succeeds without errors.
