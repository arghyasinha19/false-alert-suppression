# Features Research: Interactive Network Topology Graph

**Milestone:** v1.8 Interactive Network Topology Graph Diagram  
**Scope:** Table stakes, differentiators, interactive controls, and operator experience.

---

## 1. Table Stakes (Must-Have Capabilities)

1. **Deterministic Hierarchical Tier Layout:**
   - Visual tiers clearly labeled: Core & WAN Backbone (Top), Distribution & Security (Middle), Campus & Access Edge (Bottom).
   - Clear visual containment zones or subtle background tier lanes.
2. **Interconnected Network Links (Edges):**
   - Visible links connecting upstream and downstream network equipment.
   - Distinct link line styling based on connection health:
     - Solid teal/cyan: Nominal link with active heartbeat.
     - Pulsing amber: Warning / elevated link utilization or interface errors.
     - Broken / red dashed: Critical alert or unreachable link.
3. **Rich Custom Node Cards:**
   - Device hostname, role badge (`CORE`, `DIST / SEC`, `ACCESS`), and management IP.
   - Status indicators: Green nominal dot, amber warning dot, pulsing red radar dot for critical alerts.
   - Active alert count pill and ServiceNow incident indicator.
4. **Interactive Navigation Canvas:**
   - Pan by dragging the canvas background.
   - Zoom with mouse wheel or toolbar buttons (`+`, `-`, `Fit`).
   - Minimap in the corner indicating current viewport position.
5. **SRE Details Drawer Integration:**
   - Clicking any node opens the 580px slide-out triage drawer with Alert Triage, Telemetry vitals, Device Inventory, and SRE action bar.
   - Selected node highlights with an illuminated accent border/glow.

---

## 2. Differentiators (Enterprise Polish)

1. **Subtle Flow Particles / Traffic Pulses:**
   - Small glowing packet dots traveling along links to convey live operational pulse without overwhelming the UI.
2. **Search & Filter Dimming:**
   - When filtering by Role, Health, or search query in the top toolbar, matching nodes remain bright while non-matching nodes smoothly drop to 20% opacity.
3. **Link Tooltips:**
   - Hovering over a link edge displays connection endpoints and metrics (e.g. `10 Gbps Trunk | CRC: 0`).
4. **View Switcher Sub-Toggle:**
   - In "Topology" mode, provide a fast toggle between **Graph View** (visual node-link diagram) and **Card Grid View** (the original tiered card list), giving operators choice between spatial graph and compact card triage.

---

## 3. Anti-Features (What NOT to Build)

- **Manual Node Edge Wiring / Drag-and-Drop Port Editing:** Operators are triaging and monitoring, not building a CAD schema editor from scratch. Topology links must be computed deterministically from device tiers and network location.
- **Unconstrained Bouncing Physics / 3D Force Simulations:** Nodes wandering across the canvas induce motion sickness and prevent rapid spatial memory retrieval.
