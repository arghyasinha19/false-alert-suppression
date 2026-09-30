# Phase 3 Plan: Custom Date & Time Range Filtering

**Phase:** 3  
**Milestone:** v1.2 Custom Date & Time Range Filtering  
**Status:** In Progress  

## Goals
Implement interactive custom start and end date/time range inputs in the False Alert Metrics filter bar, evaluate alert timestamps against custom temporal boundaries in `scopeAlerts`, dynamically update all KPIs, charts, and table matrix, and provide a single-click reset button.

## Requirements Covered
- `TIME-01`: Custom start and end date-time picker controls in `FalseAlertMetrics.jsx`.
- `TIME-02`: Temporal boundary filtering in `scopeAlerts` (supporting epoch ms, seconds, and ISO 8601).
- `TIME-03`: Dynamic recalculation of KPI summary totals, category breakdowns, and trace matrix.
- `TIME-04`: Reset / Clear control returning to presets or all-time scope.

## Execution Wave

### Wave 1: Implementation
1. **State & UI Picker (`FalseAlertMetrics.jsx`)**:
   - Add state: `customStartTime` (string `YYYY-MM-DDTHH:mm`), `customEndTime` (string `YYYY-MM-DDTHH:mm`).
   - Add `<option value="CUSTOM">📅 Custom Range...</option>` to the time range selector.
   - When `timeRange === 'CUSTOM'`, render an inline sub-bar or group with:
     - Start time: `<input type="datetime-local" className="filter-input-datetime" value={customStartTime} onChange={...} />`
     - End time: `<input type="datetime-local" className="filter-input-datetime" value={customEndTime} onChange={...} />`
     - Quick "Reset / Clear" button: clears start/end and sets `timeRange` back to `'ALL'`.
2. **Filter Logic (`scopeAlerts`)**:
   - If `timeRange === 'CUSTOM'`:
     - If `customStartTime` is provided, parse via `new Date(customStartTime).getTime()` and check `alertTimestamp >= startMs`.
     - If `customEndTime` is provided, parse via `new Date(customEndTime).getTime()` and check `alertTimestamp <= endMs`.
     - Support alerts with both start, end, or bounded range.
3. **Styling (`App.css`)**:
   - Add styling for `.filter-input-datetime` to harmonize with dark glassmorphism: background `var(--bg-secondary)`, border `var(--card-border)`, color `var(--text-primary)`, accent calendar icon.
   - Add styling for the custom range input wrapper and reset button.

### Wave 2: Verification
4. **Build Check**:
   - Run `npm run build` in `dashboard/` to ensure zero compilation or syntax errors.
5. **Interactive Verification in Browser**:
   - Use browser subagent to interact with `http://localhost:5173/`.
   - Select "Custom Range", input specific start and end dates/times.
   - Confirm that alert count and KPI cards update correctly.
   - Click "Reset" and verify restore to 60 alerts.
