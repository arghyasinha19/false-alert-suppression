# Plan 20-02 Summary: High-Contrast Scrollbars, Horizontal Edge Masks & Vertical List Capping

**Phase:** 20 — Data Visibility & Bounds  
**Plan:** 20-02  
**Wave:** 2  
**Status:** Completed  
**Requirements Covered:** UI-04  
**Decisions Covered:** D-05, D-06, D-07, D-08, D-09, D-10, D-11, D-12, D-13, D-14, D-15, D-16  

---

## What Changed

1. **Permanently Visible 8px High-Contrast Scrollbars (`D-05`, `D-06`, `D-07`, `D-08`)**:
   - Updated `dashboard/src/index.css` to define 8px scrollbar rules across `.table-scroll-container`, `.data-table-scroll-wrap`, `.table-scroll-wrapper`, and `.detail-panel-body`.
   - Dark mode uses high-contrast slate thumb `rgba(148, 163, 184, 0.45)` with hover `rgba(203, 213, 225, 0.65)` on sunken track `rgba(255, 255, 255, 0.04)`.
   - Light mode uses `rgba(100, 116, 139, 0.40)` with hover `rgba(71, 85, 105, 0.60)` on sunken track `rgba(0, 0, 0, 0.05)`.
   - Set thumb border radius to 6px with transparent border inset padding.

2. **Reusable `TableScrollWrapper` Component (`D-09`, `D-10`, `D-11`, `D-12`)**:
   - Created `dashboard/src/components/TableScrollWrapper.jsx` to wrap horizontally scrollable tables.
   - Monitors container scroll events and resize observer to dynamically toggle `.has-overflow-left` and `.has-overflow-right` with a 2px boundary tolerance.
   - In `dashboard/src/App.css`, implemented 28px linear gradient edge masks on `::before` and `::after` (`left: 0` and `right: 0`), blending into `var(--card-bg)`.
   - Set `bottom: 8px` on edge masks to ensure full clearance of horizontal scrollbars, preventing obstruction or click-hijacking.

3. **Sticky Headers Across Scrollable Tables (`D-13`)**:
   - Enforced `position: sticky; top: 0; z-index: 5; backdrop-filter: blur(8px);` on table headers across `dashboard/src/App.css` for `.table-scroll-wrapper table th`, `.table-scroll-container thead th`, and `.data-table thead th`.

4. **Prominent Counter Chips with Filter Indicator (`D-14`)**:
   - Styled `.table-counter-chip` displaying `"Showing {visible} of {total} {items}"` in slate-400 monospace font with subtle border and background pill.
   - Added `.filter-active-dot` (6px primary blue dot) indicating when filtering reduces the displayed set.
   - Integrated counter chips on:
     - Detailed Traceability Matrix (`FalseAlertMetrics.jsx`)
     - Device Ranking Table (`FalseAlertMetrics.jsx`)
     - SRE High-Density Table (`NetworkOperations.jsx`)
     - Alert Patterns Table (`AlertPatterns.jsx`)

5. **Vertical List Capping & Progressive Disclosure (`D-15`, `D-16`)**:
   - Capped default table view to 10 rows with `"Show all {total} rows / Show 10 rows"` toggles (`.table-expand-toggle-btn`) in `FalseAlertMetrics.jsx` and `AlertPatterns.jsx`.
   - In `NetworkOperations.jsx`, capped SRE Details Drawer active alerts list at 5 items with `"Show {N - 5} more alerts / Show fewer alerts"` toggle (`.detail-alerts-toggle-btn`) and a `"Showing 5 of {N} alerts"` counter badge.

6. **Contract Test Suite**:
   - Implemented `tests/test_table_visibility_bounds_contract.py` covering scrollbar geometry/contrast, edge mask clearance, sticky headers, counter chip structure, and drawer alert capping.
   - 6/6 tests passing in 0.24s.

---

## Verification

- `pytest tests/test_table_visibility_bounds_contract.py tests/test_topology_bounds_contract.py`: 11 passed in 0.24s.
- `pytest tests/`: 52 passed, 7 skipped, 0 failed in 6.79s.
- `npm run build`: Production client built in 1.06s with 0 errors.
