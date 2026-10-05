# Architecture Research: Interactive Network Topology Graph

**Milestone:** v1.8 Interactive Network Topology Graph Diagram  
**Scope:** Component hierarchy, data transformation, state management, and CSS design system.

---

## 1. Component Hierarchy

```
NetworkOperations.jsx
 ├── Executive KPI Observability Strip
 ├── Filter & Search Control Bar
 │    └── View Switcher (Topology / SRE Table / Site Matrix)
 │         └── [If Topology]: Sub-mode toggle (Graph ↔ Cards)
 ├── TopologyGraphView.jsx (NEW)
 │    ├── TopologyCanvasToolbar (Zoom In/Out, Fit, Legend, Reset)
 │    ├── TopologyMinimap (Corner navigation radar)
 │    ├── SVG Graph Surface
 │    │    ├── <defs> (Gradients, filters, marker arrows)
 │    │    ├── Tier Lane Backgrounds (Core, Dist, Access lanes)
 │    │    ├── Link Edges (<path> bezier curves + animated traffic markers)
 │    │    └── Device Nodes (<g> node cards with icons, labels, health dots)
 │    └── TopologyLegend (Collapsible tier & link status guide)
 └── Slide-Out SRE Details Drawer (.detail-panel)
```

---

## 2. Node & Link Topology Generator

In `TopologyGraphView.jsx`:
- **Input:** `devices` array from parent (includes `device_name`, `device_id`, `ip_address`, `location`, `active_alerts`, etc.).
- **Node Positioning:**
  ```javascript
  const TIER_Y = { core: 110, dist_sec: 320, access: 530 };
  ```
  Nodes in each tier are distributed horizontally across the canvas width with generous padding (e.g. 220px card width, 40px gap).
- **Edge Derivation:**
  Deterministic rules:
  1. Each `dist_sec` device connects to the primary upstream `core` router in the same region or DC backbone.
  2. Each `access` switch connects to its respective `dist_sec` aggregation layer.
  3. Redundant links: Core routers are cross-linked (`core-01 <-> core-02`) representing the high-speed IBGP/OSPF backbone mesh.

---

## 3. Zoom & Pan State Contract

```javascript
const [transform, setTransform] = useState({ x: 40, y: 30, k: 1.0 });
const [isDragging, setIsDragging] = useState(false);
const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
const [hoveredNode, setHoveredNode] = useState(null);
const [hoveredEdge, setHoveredEdge] = useState(null);
```

- When zoom is 1.0, the canvas provides a crisp 1:1 view of all devices.
- Zoom limits: `0.4x` (overview) to `2.2x` (high inspection).
- Bounding box calculation centers the network on load or when `Fit` is clicked.

---

## 4. Theme & Styling Tokens

Nodes and edges consume the app's existing CSS design tokens:
- Tier accents: `--accent-blue` (Core), `--accent-purple` (Dist), `--accent-teal` (Access).
- Status colors: `--health-healthy` (`#10b981`), `--health-warning` (`#f59e0b`), `--health-critical` (`#ef4444`).
- Canvas background: Subtle dot grid (`radial-gradient(rgba(255, 255, 255, 0.08) 1px, transparent 1px)` in dark mode, dark dots in light mode).
- Glassmorphic card styling: `backdrop-filter: blur(12px); border: 1px solid var(--card-border); background: var(--bg-secondary);`.
