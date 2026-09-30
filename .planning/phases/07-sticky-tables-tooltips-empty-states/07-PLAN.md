# Phase 7 Plan: Sticky Tables, Tooltips & Empty States

**Phase:** 7  
**Milestone:** v1.4 Complete UI/UX Expert Audit Implementation  
**Status:** In Progress  

## Goals

Ensure table headers in the Traceability Matrix and Device Rankings remain sticky during scrolling, enforce strict cell truncation with hover tooltips, and provide illustrated empty states for zero-match filters across the dashboard.

## Requirements Covered

- `TABLE-01`: User can scroll the Traceability Matrix with sticky column headers staying pinned at the top.
- `TABLE-02`: User can view Device Ranking and Traceability tables with robust cell truncation and hover tooltips.
- `STATE-01`: User sees rich empty state placeholders when filters or searches match 0 items.

## Design Contract Reference

- See `07-UI-SPEC.md` for sticky header styles (`z-index: 10`, `backdrop-filter: blur(8px)`), container heights (`max-height: 480px` for matrix, `440px` for ranking), `.table-empty-state` specifications, and tooltip copywriting.

## Execution Waves

### Wave 1: CSS Architecture (`dashboard/src/App.css`)

1. **Sticky Header Styles (`TABLE-01`)**:
   - Update `.data-table th` to include `z-index: 10;`, `box-shadow: 0 1px 0 var(--card-border);`, and `backdrop-filter: blur(8px);` so headers never bleed through or get obscured when rows scroll underneath.
   - Add sticky properties to `.rank-table th`:
     ```css
     .rank-table th {
       position: sticky;
       top: 0;
       background: var(--bg-secondary);
       z-index: 10;
       box-shadow: 0 1px 0 var(--card-border);
       backdrop-filter: blur(8px);
     }
     ```
2. **Scroll Containers (`TABLE-01`)**:
   - Provide standard scroll classes or styling for table containers with `max-height: 480px; overflow-y: auto; overflow-x: auto;` (Traceability Matrix) and `max-height: 440px; overflow-y: auto; overflow-x: auto;` (Device Ranking).
3. **Empty State Component Classes (`STATE-01`)**:
   - Define `.table-empty-state`:
     - Centered flex container with `padding: 3rem 1.5rem; text-align: center; align-items: center; justify-content: center;`
     - `.empty-state-badge`: 44x44px circular backdrop (`background: rgba(37, 99, 235, 0.08); color: var(--accent-blue); display: flex; align-items: center; justify-content: center; border-radius: 50%; margin: 0 auto 0.75rem auto;`)
     - `.empty-state-title`: `font-size: 0.95rem; font-weight: 700; color: var(--text-primary); margin: 0 0 0.35rem 0;`
     - `.empty-state-desc`: `font-size: 0.82rem; color: var(--text-secondary); max-width: 420px; line-height: 1.5; margin: 0 auto 1rem auto;`
     - `.empty-state-action`: Pill button with icon (`padding: 0.45rem 1rem; font-size: 0.78rem; font-weight: 600; border-radius: 6px; display: inline-flex; align-items: center; gap: 0.4rem; cursor: pointer; transition: all var(--transition-fast);`)
4. **Cell Truncation & Ellipsis (`TABLE-02`)**:
   - Enforce truncation across `.data-table td` and `.rank-table td` for event IDs, device names, issue descriptions, and ServiceNow references.

### Wave 2: Component Integration (`dashboard/src/FalseAlertMetrics.jsx` & `dashboard/src/AlertPatterns.jsx`)

5. **Device Ranking Sticky Scroll & Header Tooltips (`TABLE-01`, `TABLE-02`)**:
   - Wrap `.rank-table` in `<div style={{ overflowX: 'auto', maxHeight: '440px', overflowY: 'auto' }}>`.
   - Add descriptive `title` attributes to all Device Ranking column headers:
     - Rank: "Device rank based on alert volume"
     - Device: "Device hostname — click to filter Detailed Traceability Matrix"
     - Total: "Total alert count recorded for this device"
     - Genuine Alerts: "Alerts verified as actionable and genuine"
     - False / Suppressed: "Alerts identified as backdated, redundant, or false positives"
     - Auto-Resolving: "Alerts expected to clear without human intervention"
     - Uncertain: "Alerts with low machine learning confidence requiring investigation"
     - SNOW Created: "New ServiceNow incident tickets dispatched"
     - SNOW Reopened: "ServiceNow incident tickets reopened due to recurring issues"
     - Volume: "Relative alert volume distribution across ranked devices"
   - Add rich empty state when `deviceRanking.length === 0`.
6. **Detailed Traceability Matrix Sticky Scroll, Tooltips & Rich Empty State (`TABLE-01`, `TABLE-02`, `STATE-01`)**:
   - Ensure the scroll container has `maxHeight: '480px', overflowY: 'auto', overflowX: 'auto'`.
   - Add descriptive `title` attributes to all `TRACE_COLUMNS` header elements.
   - Enforce hover tooltips on each data cell (`title` attributes on Event ID, Device, Severity, Issue Name, Timestamp, Classification with confidence, Queue, and ServiceNow action with incident ID).
   - Replace basic 1-line empty state with rich `.table-empty-state` structure:
     - Badge with `<FilterX size={22} />`
     - Headline: "No alerts match the current matrix filters"
     - Description: "Try broadening your search term or resetting the severity, ML category, or ServiceNow filter pills."
     - Reset button with `<RotateCcw size={13} /> Clear matrix filters` that resets search, severity, outcome, snow, AND device filter.
7. **Alert Patterns Detail Table Sticky Headers & Empty State (`TABLE-01`, `STATE-01`)**:
   - Add `maxHeight: '460px', overflowY: 'auto'` to Pattern Detail Table scroll wrapper.
   - Add descriptive `title` attributes to column headers.
   - Upgrade `patterns.length === 0` row to `.table-empty-state` with `<SearchX size={22} />`.

### Wave 3: Verification & Visual Polish

8. **Automated Verification**:
   - Run `npm run lint` in `dashboard/` to verify zero linting errors.
   - Run `npm run build` in `dashboard/` to verify clean bundle compilation.
   - Run `python -m pytest -q` to verify backend integrity.
9. **Live Browser Verification**:
   - Use `browser_subagent` to test `http://localhost:5173/`.
   - Verify scrolling the Traceability Matrix keeps headers pinned stickily with backdrop-filter blur.
   - Verify scrolling Device Ranking keeps headers pinned stickily.
   - Verify hover tooltips on truncated cells and headers.
   - Type an unmatchable query (e.g. `xyznonexistent`) into Traceability Matrix search to verify the rich `.table-empty-state` renders cleanly.
   - Click "Clear matrix filters" to verify immediate restoration of the full table.
