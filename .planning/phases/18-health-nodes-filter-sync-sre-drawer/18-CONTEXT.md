# Phase 18 Context: Health Nodes, Filter Sync & SRE Drawer

**Milestone:** v1.8 Interactive Network Topology Graph Diagram  
**Phase:** 18  
**Requirements:** GRAPH-05, GRAPH-06, GRAPH-07  

---

## 1. Problem Statement

In Phase 17, the foundational interactive SVG network topology canvas was built with smooth pan/zoom controls, deterministic 3-tier coordinate mapping (Core, Distribution & Security, Campus & Access), and animated cubic bezier link edges.

Phase 18 completes the interactive graph experience by:
1. **Rendering rich micro-cards for device nodes (`GRAPH-05`):**
   - High-contrast, glassmorphic SVG cards.
   - Distinct tier/role icons (Server for Core, Shield for Distribution/Security, Wifi for Access Edge).
   - Hostname, management IP, and site location.
   - Status indicators: Health dot, tier tag pill, and active alert count badges (`⚠ N Alert(s)` vs `✓ Nominal`).
   - Animated radar ripple pulse (`@keyframes noc-radar-pulse`) expanding outwards from critical health dots.

2. **Full SRE Details Drawer Integration & Selection Glowing Highlight (`GRAPH-06`):**
   - Clicking any node card on the SVG canvas selects that device and opens the 580px slide-out SRE details drawer.
   - Glowing accent ring highlights the currently selected device on the canvas (`stroke="var(--accent-blue)"` with SVG glow filter).
   - Full drawer capabilities available: Multi-agent Decision Timeline, Cisco DNA Center Assurance Telemetry vitals, Device Inventory & Spec audit, Raw Payloads viewer, and SRE Action Bar.
   - Keyboard accessibility: Escape key deselects device and closes drawer.

3. **Reactive Filter Synchronization & Topology Dimming (`GRAPH-07`):**
   - The canvas maintains complete topological context by displaying all infrastructure nodes and interconnects, rather than destroying the graph layout when filters are applied.
   - Passing full device fleet to `TopologyGraphView` while evaluating active `searchQuery`, `roleFilter`, and `healthFilter`.
   - Matching nodes remain at 100% full brightness and contrast.
   - Non-matching nodes and non-participating link edges are smoothly dimmed to ~20% opacity (`transition: opacity 0.3s ease`).
   - Match filter summary badge indicating active filter criteria and match ratio (e.g., "Filtered: 3 of 9 devices matching").

---

## 2. Technical Decisions & Boundaries

1. **SVG Role Icons Integration:**
   - Embed scalable vector icons for each tier:
     - Core: Server rack / backbone router icon.
     - Distribution / Security: Firewall / shield perimeter icon.
     - Access: Access switch / wireless AP icon.
   - Use clean inline SVG `<path>` elements or `<g>` primitives to ensure 100% vector sharpness across all zoom levels (`0.4x` to `2.2x`) without HTML layout recalculation overhead.

2. **Complete Graph Filter Architecture:**
   - In `NetworkOperations.jsx`, pass `devices={devices}` (complete fleet) to `TopologyGraphView` instead of `filteredDevices`.
   - `TopologyGraphView` evaluates `isDimmed = !(matchesQuery && matchesRole && matchesHealth)` per node.
   - Connected edges also receive dimmed state: if both source and target are dimmed, or if either is dimmed during strict filtering, edge opacity drops to `0.15`.

3. **Drawer Wire-Up & Accessibility:**
   - `onSelectDevice(device)` directly connects to `openDevicePanel(device)` in `NetworkOperations.jsx`.
   - Node selection emits a glowing border with `feDropShadow` and `feGaussianBlur`.
   - Clicking canvas empty area deselects node (unless user is dragging to pan).

4. **Zero Third-Party Library Overhead:**
   - Continue strictly with native React 19 SVG architecture. No canvas bloat or peer dependency incompatibilities.

---

## 3. Scope Fence

- **In Scope:**
  - Rich node micro-cards with role icons, hostnames, IPs, health dots, alert badges, and radar pulses.
  - SRE drawer trigger with glowing selection ring.
  - Reactive filter syncing with smooth opacity transitions for nodes and edges.
  - Match count banner/badge.
  - Automated contract tests and Vite build verification.
- **Out of Scope / Future:**
  - Drag-and-drop manual node repositioning (persisted to localStorage).
  - Dynamic port flapping timeline graphs.
  - WebSockets telemetry streaming.
