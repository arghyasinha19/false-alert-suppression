# Phase 17 Context: SVG Topology Canvas & Hierarchical Links

**Milestone:** v1.8 Interactive Network Topology Graph Diagram  
**Phase:** 17  
**Requirements:** GRAPH-01, GRAPH-02, GRAPH-03, GRAPH-04  

---

## 1. Problem Statement

In the Network Operations Center, operators need to understand how network devices are physically and logically interconnected across the enterprise infrastructure. While the tiered card grid (Milestone v1.5) groups devices into Core, Distribution, and Access tiers, it lacks topological link visibility, spatial relationship rendering, and an interactive graph canvas.

The user requested:
> "Topology tab. The devices should be visible in topology diagram like a graph."

Phase 17 builds the foundational interactive SVG graph engine, hierarchical coordinate system, and animated link interconnections.

---

## 2. Technical Decisions & Boundaries

1. **Pure Native SVG Architecture (Zero npm Dependencies):**
   - Built with React 19 native SVG `<svg>`, `<g>`, `<path>`, `<circle>`, `<rect>`, and `<text>` elements.
   - Avoids React 19 peer-dependency failures associated with legacy `reactflow` packages.
   - Zero bundle bloat; fast Vite builds (<900ms).
   - 100% theme-aware using existing CSS tokens (`--bg-secondary`, `--card-border`, `--accent-blue`, `--accent-purple`, `--accent-teal`, `--health-healthy`, `--health-warning`, `--health-critical`).

2. **Deterministic 3-Tier Hierarchical Coordinates:**
   - **Tier 1 (Core & WAN Backbone):** `y ≈ 120px` (Top lane, blue accent).
   - **Tier 2 (Distribution & Security Perimeter):** `y ≈ 340px` (Middle lane, purple accent).
   - **Tier 3 (Campus & Access Edge):** `y ≈ 560px` (Bottom lane, teal accent).
   - Horizontal distribution: calculated automatically based on device count per tier with minimum spacing (240px) to prevent overlap.

3. **Interconnected Network Links (Edges):**
   - Upstream/downstream links: Core routers link to Distribution switches, Distribution switches link to Access switches.
   - Backbone trunk links: Redundant Core-to-Core transit connections.
   - Cubic bezier curve paths (`d="M x1 y1 C x1 (y1+y2)/2, x2 (y1+y2)/2, x2 y2"`).
   - Animated SVG flow particles indicating active operational traffic.
   - Health-aware stroke coloring: Teal (nominal), Amber (warning / degraded), Red (critical / packet drop).

4. **Interactive Zoom, Pan & Viewport Navigation:**
   - Smooth mouse drag to pan across the canvas with pointer capture.
   - Mouse wheel zooming with bounded scaling (0.4x to 2.2x).
   - Floating glassmorphic toolbar with Zoom In (`+`), Zoom Out (`-`), Fit to View (`⛶`), Reset 100%, and Sub-mode switcher (`Graph ↔ Cards`).

5. **Sub-Mode Toggle (`topologySubMode`):**
   - In "Topology" representation mode, operators can seamlessly toggle between **Graph View** (visual node-link canvas) and **Card Grid View** (the original tiered card list), with Graph View as the default.

---

## 3. Scope Fence

- **In Scope:** SVG canvas component (`TopologyGraphView.jsx`), pan/zoom navigation math, hierarchical tier coordinate generation, bezier link edges, animated traffic pulses, floating canvas controls, sub-mode toggle in `NetworkOperations.jsx`, CSS styling, and automated contract tests.
- **Deferred to Phase 18:** High-density node micro-cards with full metrics, active radar pulse animations, filter dimming/highlighting, and drawer wire-up.
