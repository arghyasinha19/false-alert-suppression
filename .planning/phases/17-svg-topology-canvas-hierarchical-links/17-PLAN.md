---
phase: 17
plan: 17-01
status: ready
wave: 1
depends_on: []
files_modified:
  - dashboard/src/components/TopologyGraphView.jsx
  - dashboard/src/NetworkOperations.jsx
  - dashboard/src/App.css
  - tests/test_topology_graph_contract.py
autonomous: true
requirements:
  - GRAPH-01
  - GRAPH-02
  - GRAPH-03
  - GRAPH-04
---

# Phase 17: SVG Topology Canvas & Hierarchical Links — Plan

**Phase:** 17  
**Status:** Ready  
**Milestone:** v1.8 Interactive Network Topology Graph Diagram  
**Requirements:** GRAPH-01, GRAPH-02, GRAPH-03, GRAPH-04  
**Context:** `.planning/phases/17-svg-topology-canvas-hierarchical-links/17-CONTEXT.md`  

---

## Overview

Phase 17 builds the interactive SVG network topology graph diagram:
1. **Interactive SVG Canvas (`GRAPH-01`):** Custom zoomable and pannable SVG canvas with pointer drag handling, wheel zoom clamping (`0.4x` to `2.2x`), and bounding-box fit calculations.
2. **Floating Navigation Toolbar & Sub-Mode Switcher (`GRAPH-02`):** Floating controls for Zoom In (`+`), Zoom Out (`-`), Fit to View (`⛶`), Reset 1:1, and a single-click toggle between **Graph View** (visual node-link diagram) and **Card Grid View** (the original tiered card list).
3. **Hierarchical 3-Tier Coordinate Engine (`GRAPH-03`):** Automatic layout algorithm distributing devices into 3 distinct horizontal tier lanes (Core & WAN Backbone at top, Distribution & Security Perimeter in middle, Campus & Access Edge at bottom) with subtle lane backgrounds.
4. **Interconnected Network Links & Traffic Pulses (`GRAPH-04`):** Smooth cubic bezier curves connecting upstream to downstream devices, color-coded by link operational health (teal for nominal, amber for warning, red for critical), complete with animated traveling traffic pulses.

---

## Files Changed

| Action | File | Description |
|---|---|---|
| CREATE | `dashboard/src/components/TopologyGraphView.jsx` | Standalone interactive SVG topology graph canvas with zoom/pan engine, tier coordinates, bezier edges, and controls |
| MODIFY | `dashboard/src/NetworkOperations.jsx` | Integrate `TopologyGraphView` into `viewMode === 'topology'`, manage `topologySubMode` state (`'graph'` default), and pass device data |
| MODIFY | `dashboard/src/App.css` | Canvas container styles, dot-grid background, tier lane dividers, link stroke animations, and floating toolbar styling |
| CREATE | `tests/test_topology_graph_contract.py` | Automated contract test verifying canvas properties, tier positioning, link generation, and toolbar controls |

---

## Tasks

<tasks>

### Task 1 — Build `TopologyGraphView.jsx` with SVG Pan/Zoom & Hierarchical Engine (`GRAPH-01`, `GRAPH-03`, `GRAPH-04`)

<read_first>
- `dashboard/src/NetworkOperations.jsx` (lines 14-60: `TIER_METADATA`, `deriveDeviceTier`, `getDeviceHealth`)
- `.planning/phases/17-svg-topology-canvas-hierarchical-links/17-CONTEXT.md`
- `.planning/research/ARCHITECTURE.md`
</read_first>

<action>
Create `dashboard/src/components/TopologyGraphView.jsx`:
1. Define tier vertical centers and metadata:
   - Core: `y = 120`
   - Distribution/Security: `y = 340`
   - Access: `y = 560`
2. Implement layout algorithm:
   - Group devices by tier (`deriveDeviceTier(d.device_name)`).
   - Compute horizontal coordinate `x` per tier with min-gap spacing (e.g. 240px) to prevent node overlaps.
   - Total canvas width dynamically expands to fit the widest tier plus padding.
3. Compute interconnected links (edges):
   - Core-to-Core backbone transit link.
   - Core-to-Distribution uplinks (matching location or primary transit).
   - Distribution-to-Access downlinks.
   - Link paths: Cubic bezier curves `d="M ${x1} ${y1 + 45} C ${x1} ${(y1 + y2) / 2}, ${x2} ${(y1 + y2) / 2}, ${x2} ${y2 - 45}"`.
   - Link health status: If either endpoint device is critical → link is critical (`#ef4444`); if warning → amber (`#f59e0b`); otherwise teal (`#06b6d4` / `var(--accent-teal)`).
   - Traffic particles: SVG `<circle r="3">` with `<animateMotion path="..." dur="3s" repeatCount="indefinite" />`.
4. Implement pan & zoom state:
   - `transform: { x: 40, y: 30, k: 0.95 }`.
   - Pointer handlers: `onPointerDown`, `onPointerMove`, `onPointerUp` with drag distance tracking.
   - Wheel handler: clamped scaling `[0.4, 2.2]` with `e.preventDefault()`.
   - Fit-to-screen helper: computes bounding box and centers the graph.
5. Render tier lane backgrounds:
   - Subtle background rectangles with dashed dividers and tier title labels (Core & WAN, Distribution & Security, Campus & Access).
6. Render device node representations:
   - SVG `<g>` groups positioned at `(node.x, node.y)` with role icon, hostname label, health status dot, and click handler `onSelectDevice(device)`.
7. Render floating toolbar:
   - Zoom In (`+`), Zoom Out (`-`), Fit to View (`⛶`), Reset 1:1, and Graph/Cards view toggle.
</action>

<acceptance_criteria>
- `TopologyGraphView.jsx` renders an SVG canvas with `<svg className="noc-topology-canvas">`.
- Group transform applies `translate(x, y) scale(k)`.
- Tier lanes Core, Distribution, and Access are rendered with distinct Y coordinates.
- Bezier links connect nodes with animated traffic circles.
- Floating toolbar contains zoom in, zoom out, fit, and submode toggle buttons.
</acceptance_criteria>

---

### Task 2 — Integrate `TopologyGraphView` and Sub-Mode Switcher in `NetworkOperations.jsx` (`GRAPH-02`)

<read_first>
- `dashboard/src/NetworkOperations.jsx` (lines 1360-1395, 1515-1570)
</read_first>

<action>
In `dashboard/src/NetworkOperations.jsx`:
1. Import `TopologyGraphView` from `./components/TopologyGraphView`:
   ```javascript
   import TopologyGraphView from './components/TopologyGraphView';
   ```
2. Add state for `topologySubMode`:
   ```javascript
   const [topologySubMode, setTopologySubMode] = useState('graph'); // 'graph' | 'cards'
   ```
3. Update the `viewMode === 'topology'` block (around line 1515):
   - When `topologySubMode === 'graph'`, render:
     ```jsx
     <TopologyGraphView
       devices={filteredDevices}
       selectedDevice={selectedDevice}
       onSelectDevice={openDevicePanel}
       subMode={topologySubMode}
       onToggleSubMode={() => setTopologySubMode(m => m === 'graph' ? 'cards' : 'graph')}
       searchQuery={searchQuery}
       roleFilter={roleFilter}
       healthFilter={healthFilter}
     />
     ```
   - When `topologySubMode === 'cards'`, render the existing tiered card grid view (`noc-topology-view`).
4. Add a fast sub-mode toggle chip/button in the filter bar or near the view switcher so operators can toggle between Graph View and Card Grid View at any time.
</action>

<acceptance_criteria>
- `NetworkOperations.jsx` imports `TopologyGraphView`.
- `topologySubMode` defaults to `'graph'`.
- Toggling `topologySubMode` switches between the SVG graph canvas and the tiered card grid.
- Clicking any node in `TopologyGraphView` triggers `openDevicePanel(device)`.
</acceptance_criteria>

---

### Task 3 — Implement Graph Canvas Styling & Theme Tokens in `App.css` (`GRAPH-01`, `GRAPH-02`, `GRAPH-03`, `GRAPH-04`)

<read_first>
- `dashboard/src/App.css`
- `dashboard/src/index.css`
</read_first>

<action>
In `dashboard/src/App.css`, add dedicated styles for the interactive topology graph:
1. `.noc-topology-graph-container`:
   - `position: relative; width: 100%; height: 680px; min-height: 520px; overflow: hidden; border-radius: var(--radius-lg); background: var(--bg-secondary); border: 1px solid var(--card-border); user-select: none; cursor: grab;`.
   - Active drag cursor: `cursor: grabbing;`.
2. Dot grid canvas background:
   - Radial gradient background matching dark and light mode tokens.
3. Floating controls toolbar (`.noc-graph-controls-toolbar`):
   - `position: absolute; top: 16px; right: 16px; z-index: 10; display: flex; align-items: center; gap: 6px; padding: 6px; background: rgba(15, 23, 42, 0.75); backdrop-filter: blur(12px); border: 1px solid var(--card-border); border-radius: var(--radius-md); box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);`.
   - Dark/Light mode theme-aware background (`[data-theme="light"] .noc-graph-controls-toolbar { background: rgba(255, 255, 255, 0.85); }`).
4. Control buttons (`.noc-graph-control-btn`):
   - Styling for hover, active, and tooltip affordance.
5. Tier lane dividers and labels (`.noc-graph-tier-label`):
   - Uppercase badges with blue/purple/teal accent colors.
6. Link styling (`.noc-graph-link`):
   - Smooth stroke, opacity, transition, and drop shadow.
7. Traffic particles (`.noc-traffic-particle`):
   - Glowing pulses travelling along link paths.
</action>

<acceptance_criteria>
- `.noc-topology-graph-container` is styled with glassmorphism and dot-grid background.
- Floating toolbar is positioned in the top-right corner with theme-aware styling.
- Link edges and traffic animations are defined with CSS transitions.
- Light mode overrides ensure high contrast in both themes.
</acceptance_criteria>

---

### Task 4 — Automated Contract Test & Build Verification (`GRAPH-01` - `GRAPH-04`)

<read_first>
- `tests/test_drawer_scrollbar_contract.py`
- `dashboard/src/components/TopologyGraphView.jsx`
- `dashboard/src/NetworkOperations.jsx`
</read_first>

<action>
1. Create `tests/test_topology_graph_contract.py`:
   - Test 1: Verify `TopologyGraphView.jsx` exists and contains SVG canvas with zoom/pan transforms.
   - Test 2: Verify `TopologyGraphView.jsx` defines 3-tier coordinates (Core, Distribution, Access) and bezier curve path generators.
   - Test 3: Verify floating toolbar controls (zoom in, zoom out, fit, submode toggle).
   - Test 4: Verify `NetworkOperations.jsx` imports `TopologyGraphView`, maintains `topologySubMode`, and connects node selection.
   - Test 5: Verify `App.css` defines graph container, floating toolbar, tier lanes, and traffic pulse styles.
2. Run pytest:
   ```bash
   pytest tests/test_topology_graph_contract.py -v
   ```
3. Run frontend production build:
   ```bash
   cd dashboard && npm run build
   ```
</action>

<acceptance_criteria>
- `pytest tests/test_topology_graph_contract.py -v` passes 100% of test assertions.
- `npm run build` compiles with 0 errors.
</acceptance_criteria>

</tasks>

---

## Verification Plan

### Automated Tests
- Run `pytest tests/test_topology_graph_contract.py -v` (all tests pass).
- Run `pytest tests/ -v` (full suite passes with 0 regressions).
- Run `npm run build` in `dashboard/` (clean Vite build).

### Manual / Browser Verification
- Open [http://localhost:5173/](http://localhost:5173/)
- Navigate to "Network Operations" tab and select "Topology" view
- Observe the interactive SVG Network Topology Graph Diagram
- Verify Core, Distribution, and Access nodes are arranged hierarchically
- Verify curved link edges connect nodes with animated traffic pulses
- Click and drag the canvas to test smooth panning
- Use mouse wheel and toolbar buttons (`+`, `-`, `Fit`) to test zoom
- Click the "Cards / Graph" toggle button: verify it switches smoothly between the graph canvas and the original tiered card grid
