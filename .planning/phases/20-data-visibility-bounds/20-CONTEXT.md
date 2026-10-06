# Phase 20: Data Visibility & Bounds - Context

**Gathered:** 2026-10-06  
**Status:** Ready for planning  

<domain>
## Phase Boundary

Phase 20 delivers comprehensive data visibility and viewport bounding enhancements across the Cisco DNA Center Ops Center dashboard:
1. **Topology Canvas Bounds & Scroll Hijacking (UI-03):** Constrain the interactive SVG topology graph canvas to its own bounds with dynamic viewport height `calc(100vh - 280px)`, prevent page scroll hijacking by requiring `Ctrl` / `Cmd` + scroll to zoom (with floating hint pill), clamp panning to soft boundaries so nodes are never lost off-screen, and add a dedicated Fullscreen / Expanded View toggle in the toolbar.
2. **Permanent Table Scrollbars & Contrast (UI-04):** Replace faint/hidden scrollbars with permanently visible 8px high-contrast scrollbars on all data tables and panels, featuring WCAG-compliant slate thumbs and subtle sunken tracks in both dark and light themes.
3. **Horizontal Table Edge Gradient Masks (UI-04):** Implement scroll-position-driven `::before` and `::after` gradient edge masks (28px) on all wide data tables, providing clear visual cues for off-screen columns that dynamically fade out when scrolled to the boundary.
4. **Vertical List Capping & Counters (UI-04):** Cap dense vertical tables and drawer alert lists with sticky headers (`top: 0; backdrop-filter`), prominent `"Showing X of Y"` header counter pills, and "Show more / Show all" controls.

</domain>

<decisions>
## Implementation Decisions

### Topology Canvas Bounds & Scroll Hijacking (UI-03)
- **D-01:** Guard wheel zooming: Require `Ctrl` / `Cmd` + scroll to zoom the topology canvas; regular wheel scrolling without modifier passes through to scroll the page naturally. When scrolling without modifier over canvas, display a subtle temporary floating toast hint: *"Use Ctrl + scroll to zoom"*.
- **D-02:** Responsive canvas height: Implement dynamic viewport-proportional height `calc(100vh - 280px)` clamped with `min-height: 560px` and `max-height: 780px` to maximize network visibility on both laptops and large desktop displays.
- **D-03:** Soft pan boundary clamping: Constrain diagram pan translation coordinates (`transform.x`, `transform.y`) so at least 25% of the graph canvas bounding box remains visible within the container at all times, preventing operators from dragging nodes completely off-screen.
- **D-04:** Dedicated Fullscreen / Expanded View mode: Add a Maximize/Fullscreen toggle button in the floating canvas toolbar (`<Maximize2 size={13} />` / `<Minimize2 size={13} />`) expanding the canvas to fixed `inset: 0` / `100vw x 100vh` with `z-index: 1000` and an Esc key listener to exit.

### Permanent High-Contrast Table Scrollbars (UI-04)
- **D-05:** Geometry and hit target: Standardize table scrollbars to 8px thickness (`width: 8px; height: 8px;`) with smooth rounded pill thumbs (`border-radius: 6px`) to ensure an easy click and drag target without visual clutter.
- **D-06:** High-contrast thumb styling: Permanently visible slate thumbs passing WCAG 3:1 non-text contrast:
  - Dark Mode: `rgba(148, 163, 184, 0.45)` (hover `rgba(148, 163, 184, 0.75)`).
  - Light Mode: `rgba(100, 116, 139, 0.4)` (hover `rgba(71, 85, 105, 0.7)`).
- **D-07:** Sunken track background: Subtle sunken track channels with smooth radius:
  - Dark Mode: `rgba(255, 255, 255, 0.04)`.
  - Light Mode: `rgba(0, 0, 0, 0.05)`.
- **D-08:** Scoped application: Target high-contrast 8px scrollbar rules via dedicated utility classes (`.table-scroll-container` / `.data-table-scroll-wrap`) applied across all data tables, matrices, and log panels (`.rank-table`, `.table-card`, `.noc-sre-table-wrap`, `.patterns-table`, `.detail-panel-body`).

### Horizontal Table Edge Gradient Masks (UI-04)
- **D-09:** Pseudo-element overlay architecture: Implement edge masking via wrapper pseudo-elements (`::before` for left edge, `::after` for right edge) with `pointer-events: none` and `z-index: 4`, ensuring table scrollbars remain fully clickable and unclipped at the bottom.
- **D-10:** Scroll-aware dynamic fade-out: Attach a lightweight scroll position handler (or custom `TableScrollWrapper`) setting classes `has-overflow-left` and `has-overflow-right`. Smoothly fade masks (`transition: opacity 0.2s ease`) so when scrolled all the way to an edge, that edge mask drops to `opacity: 0`, leaving boundary columns 100% crisp.
- **D-11:** 28px gradient falloff: Set mask width to 28px blending from `transparent` to `var(--card-bg)` in both dark and light modes for seamless card integration.
- **D-12:** Broad multi-table coverage: Apply horizontal gradient edge masks to all 5 wide tables across the dashboard: Traceability Matrix, Device Ranking Table, SRE Table View, Regional Site Matrix, and Alert Patterns Table.

### Vertical List Capping & Counters (UI-04)
- **D-13:** Explicit max-height with sticky headers and progressive toggle: Cap dense vertical tables with explicit container height limits (`max-height: 480px` or 10 rows), sticky column headers, and an optional "Show all / Show 10" expansion toggle when lists exceed the default cap.
- **D-14:** Prominent header counter chips: Render a subtle pill badge in the table/card header (e.g. `Showing {visible} of {total} {items}` / `Showing 10 of 48 alerts`) with a blue filter highlight indicator when active filtering is applied.
- **D-15:** SRE Details Drawer alert list capping: Cap active alerts list inside the SRE drawer at 5 items by default with a "Show {N - 5} more alerts" button and a `"Showing 5 of {N}"` count chip, keeping the drawer compact while retaining one-click access to the full list.
- **D-16:** Sticky table headers: Enforce sticky headers (`position: sticky; top: 0; z-index: 5; background: var(--bg-secondary); backdrop-filter: blur(8px)`) across all capped scrollable table views so column labels and sort handles remain locked in view during vertical scrolling.

### the agent's Discretion
- Micro-timing for the wheel zoom modifier toast hint animation (`0.2s fadeIn`, 2s auto-dismiss).
- Exact debounce timing (50ms) for scroll position calculation on horizontal table wrappers.
- Icon selection for expansion controls (`ChevronDown`, `ChevronUp`, `Maximize2`, `Minimize2`).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Roadmap & Requirements
- `.planning/ROADMAP.md` §Phase 20 — Phase goal, requirements UI-03 & UI-04, and success criteria.
- `.planning/REQUIREMENTS.md` §Data Visibility & Bounds — UI-03 and UI-04 requirements.

### Topology Graph Components & Styles
- `dashboard/src/components/TopologyGraphView.jsx` — SVG topology diagram canvas, zoom/pan transform handlers, wheel listener, and floating controls toolbar.
- `dashboard/src/App.css` §NOC Phase 17 — `.noc-topology-graph-container`, `.noc-topology-canvas`, toolbar, and badge styling.

### Data Tables & Matrix Views
- `dashboard/src/FalseAlertMetrics.jsx` — Device Ranking Table (`.rank-table`) and Detailed Traceability Matrix (`.data-table.resizable-table`).
- `dashboard/src/NetworkOperations.jsx` — SRE High-Density Table View (`.noc-sre-table`), Regional Site Matrix (`.noc-matrix-table`), and SRE Details Drawer (`.detail-panel-body`, `.detail-alerts-list`).
- `dashboard/src/AlertPatterns.jsx` — Alert Pattern Analysis Table (`.patterns-table`).

### Global Styling & Theme System
- `dashboard/src/index.css` — Global scrollbar rules and theme custom properties (`--card-bg`, `--bg-secondary`, `--card-border`).
- `dashboard/src/App.css` — Table card containment (`.table-card`), responsive grid rules, and drawer scroll containers.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `transform` state `{ x, y, k }` and zoom utility functions in `TopologyGraphView.jsx`.
- Existing ResizeObserver in `TopologyGraphView.jsx` tracking container width and height.
- Existing sticky table header foundations in `FalseAlertMetrics.jsx` and `NetworkOperations.jsx`.
- CSS variable token system (`--card-bg`, `--card-border`, `--text-primary`, `--text-secondary`, `--text-tertiary`) in `index.css`.

### Established Patterns
- High-contrast scrollbars developed in Phase 16 (`test_drawer_scrollbar_contract.py`) for the SRE drawer body.
- Glassmorphic floating control toolbars with active state pills.
- Counter and filter badges (`.badge`, `.noc-device-count-badge`).

### Integration Points
- `dashboard/src/components/TopologyGraphView.jsx`: Update `handleWheel` to require `e.ctrlKey || e.metaKey`, add wheel hint overlay, clamp `transform` in `handlePointerMove`, and add fullscreen toggle button.
- `dashboard/src/App.css`: Update `.noc-topology-graph-container` height to `clamp(560px, calc(100vh - 280px), 780px)`, style `.noc-topology-graph-container.fullscreen`, add 8px scrollbar rules for tables, and define `.table-scroll-wrapper` with `::before`/`::after` edge masks.
- `dashboard/src/FalseAlertMetrics.jsx`: Wrap tables in `TableScrollWrapper`, add sticky header CSS classes, and add `"Showing X of Y"` counter chips.
- `dashboard/src/NetworkOperations.jsx`: Wrap SRE Table and Site Matrix in `TableScrollWrapper`, add count chips, and cap drawer alerts list at 5 items with toggle.
- `dashboard/src/AlertPatterns.jsx`: Wrap patterns table in `TableScrollWrapper` with counter chip.

</code_context>

<specifics>
## Specific Ideas

- **Wheel Hijack Solution:** When an operator scrolls their mouse wheel over the topology canvas without holding Ctrl, do NOT zoom the canvas; instead let the page scroll naturally and show a small centered pill: *"Use Ctrl + scroll to zoom"*.
- **Edge Masks:** When a table has columns overflowing off-screen to the right, a 28px subtle gradient fade signals that more content exists horizontally. When the operator scrolls all the way to the right, the right fade vanishes cleanly.
- **Scrollbar Contrast:** 8px thickness with rounded edges makes dragging effortless on laptops and desktop mice without having to hunt for a 4px line.

</specifics>

<deferred>
## Deferred Ideas

- Drag-and-drop custom node pinning saved to localStorage (tracked in REQUIREMENTS.md as future enhancement).
- Virtualized infinite scrolling tables (future performance enhancement if alert fleet exceeds 1,000+ items; current max is <100 items).

</deferred>

---

*Phase: 20-data-visibility-bounds*  
*Context gathered: 2026-10-06*  
