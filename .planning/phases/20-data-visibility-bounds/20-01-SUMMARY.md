# Plan 20-01 Summary: Topology Canvas Viewport Bounds, Wheel Zoom Guard & Fullscreen Mode

**Phase:** 20 — Data Visibility & Bounds  
**Plan:** 20-01  
**Wave:** 1  
**Status:** Completed  
**Requirements Covered:** UI-03  
**Decisions Covered:** D-01, D-02, D-03, D-04  

---

## What Changed

1. **Wheel Zoom Guarding with Modifier & Floating Toast Hint (`D-01`)**:
   - Modified `handleWheel` in `dashboard/src/components/TopologyGraphView.jsx` to verify `e.ctrlKey || e.metaKey`.
   - When scrolling without `Ctrl`/`Cmd`, `e.preventDefault()` is not called, allowing the page to scroll naturally, and a floating toast hint pill appears: *"Use Ctrl + scroll to zoom"*.
   - Added auto-dismiss timer (2.0s) and styled `.noc-wheel-zoom-hint` in `dashboard/src/App.css` with smooth toast animation (`fadeInToast 0.2s`).

2. **Responsive Viewport Height Clamping (`D-02`)**:
   - Updated `.noc-topology-graph-container` in `dashboard/src/App.css` to use fluid viewport-proportional height:
     `height: clamp(560px, calc(100vh - 280px), 780px); min-height: 560px; max-height: 780px; overflow: hidden; position: relative;`.
   - Prevents the canvas from blowing out the main viewport on both compact laptops and 4K displays.

3. **Soft-Boundary Pan Clamping (`D-03`)**:
   - Updated `handlePointerMove` in `dashboard/src/components/TopologyGraphView.jsx` to clamp `transform.x` and `transform.y`.
   - Guarantees at least 25% of the graph diagram bounding box remains visible within the container at all times, preventing operators from dragging nodes completely off-screen.

4. **Dedicated Fullscreen / Expanded View Mode (`D-04`)**:
   - Added `isFullscreen` state in `TopologyGraphView.jsx` and added an Expand/Exit toggle button in the floating canvas toolbar (`<Maximize2 size={13} />` / `<Minimize2 size={13} />`).
   - Attached an `Escape` key event listener to cleanly exit fullscreen mode.
   - Styled `.noc-topology-graph-container.fullscreen` in `dashboard/src/App.css` (`position: fixed; inset: 0; width: 100vw; height: 100vh; z-index: 1000;`).

5. **Automated Verification Contract Tests**:
   - Created `tests/test_topology_bounds_contract.py` asserting container height clamping, fullscreen styles, wheel modifier guard logic, toast hint copy, pan clamping, and toolbar toggle button.
   - All 5 tests passed in 0.25s.

---

## Verification

- `pytest tests/test_topology_bounds_contract.py`: 5 passed in 0.25s.
- `npm run build`: Production bundle built cleanly in 825ms without errors.
