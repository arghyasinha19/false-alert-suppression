# Phase 24: Global Multi-Site WAN Interconnect Canvas - Context

**Gathered:** 2026-10-06  
**Status:** Ready for planning  
**Mode:** Smart Discuss (Autonomous Mode)

<domain>
## Phase Boundary

Implement Level 1 Global Multi-Site WAN topology map rendering interactive macro site nodes, aggregated site health badges, blast radius indicators, and inter-site WAN links (`SITE-01`, `SITE-02`, `SITE-03`).
</domain>

<decisions>
## Implementation Decisions

### Area 1: Global WAN Macro Node Layout & Geometry
- **Layout Model**: Geographic / regional layout (EMEA west, APAC east, Americas central) with deterministic coordinate offsets on the SVG canvas.
- **Node Geometry**: 220x100px rounded glassmorphism macro cards (`.noc-wan-site-node`) displaying regional flag, site code, site label, health status badge (`nominal`, `degraded`, `critical`), registered device count, and active alert pill.
- **Blast Radius Indicator**: Glowing circular perimeter halo around degraded/critical sites (`.blast-radius-halo`) scaled by affected devices with blast radius percentage chip.
- **Single-Site Fallback**: When only one site is registered, displays as an authoritative central DC hub.

### Area 2: Inter-Site WAN Interconnect Links & Telemetry
- **Topology Architecture**: Hierarchical WAN transit mesh connecting primary transit hubs (UK-LON and SG-SIN) with regional branch spokes.
- **Visual Styling**: Curved SVG bezier interconnects with animated SVG dash-flow (`stroke-dasharray`, `@keyframes wanFlow`) representing real-time telemetry transit.
- **Link Telemetry**: Interconnect badges along links displaying round-trip latency (`24ms`, `115ms`), packet loss (0.00% vs 0.14%), and status coloring (green nominal, amber warning, red critical).
- **Interactive Tooltips**: Hovering any WAN link highlights connected site pair and displays link bandwidth and connected border core routers.

### Area 3: Level 1 Canvas Controls & State
- **View Integration**: Managed inside `TopologyGraphView.jsx` via `topologyLevel: 'wan' | 'lan'`.
- **Canvas Controls**: Header indicator badge displaying `"GLOBAL WAN TOPOLOGY"` with total site count and overall WAN health score.
- **Drill-Down Trigger**: Macro site nodes feature an interactive "Drill Down" button / click action triggering site selection callback to prepare for Phase 25.
</decisions>

<code_context>
## Existing Code Insights

- `TopologyGraphView.jsx` contains the pan/zoom SVG canvas, transform state machine, ResizeObserver, and fullscreen mode.
- `NetworkOperations.jsx` computes `siteMatrix` using `LOCATION_LABELS` and device health summaries.
- `App.css` contains `.noc-topology-graph-container`, `.noc-topology-canvas`, and theme CSS variables.
</code_context>

<specifics>
## Specific Ideas

- Reuse existing D3 zoom / mouse pan machinery in `TopologyGraphView.jsx` for the WAN canvas.
- Compute WAN links deterministically between sites based on geographic proximity and core router capabilities.
</specifics>

<deferred>
## Deferred Ideas

- Level 2 Local Site LAN drill-down (Core ↔ Dist ↔ Access) and breadcrumb routing deferred to Phase 25.
- Cross-view synchronization with SRE Table and Site Matrix deferred to Phase 26.
</deferred>
