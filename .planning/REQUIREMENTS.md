# Requirements: False Alert Suppression Pipeline

**Defined:** 2026-10-05  
**Milestone:** v1.9 UI/UX Audit Remediation  
**Core Value:** Accurately identify false or transient network alerts to prevent unnecessary ServiceNow ticket creation and reduce operational noise without missing genuine network degradation.

## Milestone v1.9 Requirements: UI/UX Audit Remediation

### Critical Layout & Status Fixes (UI-CRITICAL)
- [x] **UI-01**: Fix responsive collapse below 1100px in the `.content-area` by removing `calc(100vw - ...)` constraints and letting flexbox size it correctly.
- [x] **UI-02**: Sidebar connection status must accurately reflect API failures by explicitly handling fetch errors, updating the "LIVE" badge to "Stale" on failure, and properly separating mock data from live status.
- [x] **UI-03**: Constrain the topology graph canvas to its own bounds with independent scroll and zoom containers to prevent overflowing the main window.

### Data Visibility & Bounds (UI-VISIBILITY)
- [x] **UI-04**: Add permanently visible scrollbars to data tables, implement right-edge gradient masks on horizontally scrolling tables, and explicitly cap vertical lists (e.g., "Showing 5 of 7").

### Trust & Contrast Remediation (UI-CONTRAST)
- [x] **UI-05**: Adjust `text-tertiary` to meet contrast minimums (`#64748b` in light mode, `#94a3b8` in dark mode) and darken blue pill text to pass AA contrast.
- [x] **UI-06**: Refactor charts to use CSS tokens from `index.css` via `getComputedStyle` or a theme palette object, ensuring chart legends, grids, and axes integrate with dark mode.

### Accessibility & Hit Areas (UI-A11Y)
- [x] **UI-07**: Increase all interactive element (buttons, pills, selects) minimum heights to 32px with 44px hit areas, and raise table/filter typography to 12-13px.
- [x] **UI-08**: Update the Ops Assistant chat panel to be non-modal (inset the content area) or properly manage focus and dim the backdrop.
- [x] **UI-16**: Update sidebar navigation to use real `<button>` elements, add `aria-current="page"`, add a `:focus-visible` ring, and trigger tooltips on focus.
- [x] **UI-17**: Ensure all form controls have visible labels, add `scope="col"` to table headers, and provide visually-hidden captions per table.

### Craft & Consistency Polish (UI-POLISH)
- [ ] **UI-09-22**: Address medium-priority inconsistencies including scaling typography (12/13/15/18/24/34), standardizing KPI cards to the NOC card design, clarifying domain shorthand, unifying empty states, and removing demo simulation scaffolding.

## Future Requirements

- Real-time WebSockets streaming updates for telemetry metrics instead of polling.
- Multi-tenancy support for partitioned customer network views.
- Dynamic interface flap timeline graph per port.
- User-customizable drag-and-drop node pinning with layout state persisted in localStorage.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Third-party heavy canvas libraries (`reactflow` v11) | Incompatible with React 19; native SVG delivers zero bundle bloat and 100% theme integration. |
| Manual port wiring CAD editor | Operators monitor and triage existing infrastructure; topology links are computed deterministically. |
| Altering backend API endpoints | Topology graph is purely client-side SVG representation consuming existing `/api/alerts` and `/api/devices`. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| UI-01 | Phase 19 | Satisfied |
| UI-02 | Phase 19 | Satisfied |
| UI-03 | Phase 20 | Satisfied |
| UI-04 | Phase 20 | Satisfied |
| UI-05 | Phase 21 | Satisfied |
| UI-06 | Phase 21 | Satisfied |
| UI-07 | Phase 22 | Satisfied |
| UI-08 | Phase 22 | Satisfied |
| UI-16 | Phase 22 | Satisfied |
| UI-17 | Phase 22 | Satisfied |
| UI-09-22 | Phase 23 | Satisfied |

**Coverage:**
- v1.9 requirements: 11 total
- Satisfied: 11 (100.0%)
- Pending: 0 (0.0%)

---
*Requirements defined: 2026-10-05*  
*Last updated: 2026-10-06 after Phase 23 completion*
