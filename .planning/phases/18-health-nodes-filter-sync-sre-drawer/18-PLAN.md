---
phase: 18
plan: 18-01
status: ready
wave: 1
depends_on: []
files_modified:
  - dashboard/src/components/TopologyGraphView.jsx
  - dashboard/src/NetworkOperations.jsx
  - dashboard/src/App.css
  - tests/test_topology_nodes_contract.py
autonomous: true
requirements:
  - GRAPH-05
  - GRAPH-06
  - GRAPH-07
---

# Phase 18: Health Nodes, Filter Sync & SRE Drawer — Plan

**Phase:** 18  
**Status:** Ready  
**Milestone:** v1.8 Interactive Network Topology Graph Diagram  
**Requirements:** GRAPH-05, GRAPH-06, GRAPH-07  
**Context:** `.planning/phases/18-health-nodes-filter-sync-sre-drawer/18-CONTEXT.md`  

---

## Overview

Phase 18 completes the interactive network topology graph by enriching device node cards, connecting the SRE triage workflow, and enabling reactive filter synchronization across the entire topology:

1. **Rich Node Micro-Cards & Role Icons (`GRAPH-05`):**
   - High-contrast, glassmorphic node cards with role icons (Core Server, Distribution Shield, Access Wifi/Switch).
   - Hostname, management IP, site location, tier tag badge, and health status dot.
   - Active alert count badges (`⚠ N Alert(s)` vs `✓ Nominal`).
   - Animated expanding radar pulse ring for nodes experiencing critical operational degradation.

2. **SRE Details Drawer Integration & Selection Glowing Highlight (`GRAPH-06`):**
   - Clicking any node card on the canvas triggers `openDevicePanel(device)`, opening the 580px slide-out SRE details drawer.
   - Selected node displays a glowing accent highlight ring (`stroke="var(--accent-blue)"` with glow drop-shadow filter).
   - Full drawer capabilities available: Multi-agent Decision Timeline, Live DNAC Telemetry vitals, Inventory specs, Raw Payloads viewer, and SRE Action Bar.

3. **Full Topology Fleet & Reactive Filter Sync Dimming (`GRAPH-07`):**
   - Pass the full `devices` fleet to `TopologyGraphView` so the complete network infrastructure topology remains visually intact when filters are applied.
   - Matching nodes remain at 100% full brightness and contrast.
   - Non-matching nodes and inactive connection links are smoothly dimmed to 20% opacity (`transition: opacity 0.3s ease`).
   - Active filter summary badge showing matching device counts with a quick "Reset Filters" action.

---

## Files Changed

| Action | File | Description |
|---|---|---|
| MODIFY | `dashboard/src/components/TopologyGraphView.jsx` | Add vector role icons, alert badges, critical radar pulses, selection highlight glow, edge dimming, and filter match banner |
| MODIFY | `dashboard/src/NetworkOperations.jsx` | Pass full `devices` fleet to `TopologyGraphView` while keeping `searchQuery`, `roleFilter`, and `healthFilter` reactive |
| MODIFY | `dashboard/src/App.css` | Styles for role icon badges, selected glowing borders, dimmed nodes/links transitions, and filter match badge |
| CREATE | `tests/test_topology_nodes_contract.py` | Automated contract test suite asserting node card structure, role icons, selection highlights, and filter dimming |

---

## Tasks

<tasks>

### Task 1 — Enrich Device Node Micro-Cards with Vector Role Icons, Health Badges & Radar Ripple (`GRAPH-05`)

<read_first>
- `dashboard/src/components/TopologyGraphView.jsx` (lines 580-745)
- `dashboard/src/App.css` (lines 4235-4286)
- `.planning/phases/18-health-nodes-filter-sync-sre-drawer/18-CONTEXT.md`
</read_first>

<action>
In `dashboard/src/components/TopologyGraphView.jsx`:
1. Define crisp vector SVG paths for each role/tier icon:
   - **Core (Server Rack / Backbone Router):** SVG path rendering a server stack with status LED dots.
   - **Distribution & Security (Firewall / Shield):** SVG path rendering a security shield with central dividing line.
   - **Campus & Access (Switch / Wireless AP):** SVG path rendering an access switch with RJ45 port matrix or wireless antenna waves.
2. Embed the vector role icon inside each node micro-card next to the tier pill or hostname:
   - Positioned in an icon badge box at `x="12", y="14"` with tier-accented background fill.
3. Align Hostname and Subtitle:
   - `x="42", y="23"`: Device hostname in bold 12px with `<title>{node.device.device_name}</title>` for native SVG hover tooltip.
   - `x="42", y="38"`: Management IP (`node.device.ip_address`) and Location (`node.device.location`).
4. Status & Alert Badges:
   - At `y="52"`: Tier pill tag (`CORE`, `DIST / SEC`, `ACCESS`) with accent color.
   - Alert Pill:
     - If `node.activeAlertCount > 0`: `⚠ {node.activeAlertCount} Alert{s}` with red/amber styling.
     - If nominal: `✓ Nominal` with green styling.
5. Critical Health Pulse:
   - Ensure `<circle className="noc-radar-pulse-ring" />` is rendered around the health dot when `node.health === 'critical'`.
   - In `dashboard/src/App.css`, ensure `.noc-radar-pulse-ring` and `@keyframes noc-radar-pulse` expand `r` and fade opacity smoothly from 0.8 to 0.
</action>

<acceptance_criteria>
- Each node card displays a distinct vector role icon for Core, Distribution, and Access tiers.
- Hostname, management IP, and location are clearly legible within the node card.
- Tier tag pill and active alert status badge are rendered.
- Nodes with critical health render the animated radar pulse ring.
</acceptance_criteria>

---

### Task 2 — Wire SRE Details Drawer Integration & Selection Glowing Highlight (`GRAPH-06`)

<read_first>
- `dashboard/src/components/TopologyGraphView.jsx` (lines 580-630, 275-312)
- `dashboard/src/NetworkOperations.jsx` (lines 200-260: `openDevicePanel`, `selectedDevice`, `isDrawerOpen`)
</read_first>

<action>
1. In `dashboard/src/components/TopologyGraphView.jsx`:
   - Enhance the selected node visual treatment:
     - Render a rounded highlight rect with `x="-4" y="-4" width={NODE_WIDTH + 8} height={NODE_HEIGHT + 8} rx="14"`.
     - Apply glowing stroke `stroke="var(--accent-blue)"` with `strokeWidth="2.5"` and `filter="url(#glow-blue)"`.
   - Ensure clicking anywhere on the node card invokes `onSelectDevice(node.device)`.
   - Clicking on the canvas background deselects the device (`onSelectDevice(null)`) if the pointer did not drag/pan (drag threshold < 5px).
2. In `dashboard/src/NetworkOperations.jsx`:
   - Verify `onSelectDevice={openDevicePanel}` sets `selectedDevice` and opens `isDrawerOpen = true`.
   - Add keyboard listener: pressing `Escape` while the drawer is open or a node is selected closes the drawer and resets selection.
3. In `dashboard/src/App.css`:
   - Add `.noc-graph-node-card.selected` styles with subtle elevation and glowing border.
</action>

<acceptance_criteria>
- Clicking any node card on the SVG canvas triggers `openDevicePanel(device)`.
- The selected node displays a distinct glowing blue selection border.
- The 580px slide-out SRE details drawer opens with complete device data (Alerts, DNAC Telemetry, Inventory, Timeline, Action Bar).
</acceptance_criteria>

---

### Task 3 — Full-Fleet Topology Display & Reactive Filter Sync Dimming (`GRAPH-07`)

<read_first>
- `dashboard/src/NetworkOperations.jsx` (lines 1540-1555)
- `dashboard/src/components/TopologyGraphView.jsx` (lines 107-175, 520-580)
</read_first>

<action>
1. In `dashboard/src/NetworkOperations.jsx`:
   - Update `<TopologyGraphView>` props:
     - Change `devices={filteredDevices}` to `devices={devices}`.
     - Keep passing `searchQuery={searchQuery}`, `roleFilter={roleFilter}`, and `healthFilter={healthFilter}`.
     - This preserves the entire network infrastructure topology on canvas while filtering.
2. In `dashboard/src/components/TopologyGraphView.jsx`:
   - In the layout computation:
     - Check node match against `searchQuery`, `roleFilter`, and `healthFilter`.
     - Set `node.isDimmed = !(matchesQuery && matchesRole && matchesHealth)`.
   - In edge rendering:
     - If both source and target are dimmed, or if filtering is active and either node is dimmed, set `edge.isDimmed = true`.
     - In CSS/SVG, apply `opacity: 0.12` to dimmed edges.
   - When filters are active (any of `searchQuery`, `roleFilter !== 'all'`, or `healthFilter !== 'all'`):
     - Display a floating filter match badge in the top-left area:
       - e.g., `Filtered: ${matchCount} of ${totalCount} devices` with a "Clear" button.
3. In `dashboard/src/App.css`:
   - Add `.noc-graph-node-card.dimmed { opacity: 0.18; filter: grayscale(40%); }`.
   - Add `.noc-link-path.dimmed { opacity: 0.12 !important; }`.
   - Add smooth transitions (`transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1), filter 0.3s ease;`).
</action>

<acceptance_criteria>
- `TopologyGraphView` receives the full device fleet, preventing topology graph fragmentation.
- When a filter is selected (e.g. Critical health, Core role, or search query), non-matching nodes are smoothly dimmed to ~18% opacity.
- Non-participating connection links are dimmed to 12% opacity.
- An active filter count badge indicates how many devices match the current filters with a quick clear option.
</acceptance_criteria>

---

### Task 4 — Automated Contract Testing & Build Verification (`GRAPH-05`, `GRAPH-06`, `GRAPH-07`)

<read_first>
- `tests/test_topology_graph_contract.py`
- `dashboard/src/components/TopologyGraphView.jsx`
- `dashboard/src/NetworkOperations.jsx`
</read_first>

<action>
1. Create `tests/test_topology_nodes_contract.py`:
   - Test 1: Verify `TopologyGraphView.jsx` renders role icons (Core server, Distribution shield, Access switch/wifi).
   - Test 2: Verify `TopologyGraphView.jsx` renders hostnames, IPs, health indicators, alert counts, and radar pulse rings.
   - Test 3: Verify node selection renders glowing highlight ring and connects to `openDevicePanel`.
   - Test 4: Verify `NetworkOperations.jsx` passes full `devices` fleet to `TopologyGraphView`.
   - Test 5: Verify `TopologyGraphView.jsx` and `App.css` define reactive filter dimming for non-matching nodes and edges.
2. Run pytest:
   ```bash
   pytest tests/test_topology_nodes_contract.py -v
   ```
3. Run frontend production build:
   ```bash
   cd dashboard && npm run build
   ```
</action>

<acceptance_criteria>
- `pytest tests/test_topology_nodes_contract.py -v` passes 100% of test assertions.
- `npm run build` compiles with 0 errors and 0 warnings.
- Full test suite `pytest tests/ -v` passes with 0 regressions.
</acceptance_criteria>

</tasks>

---

## Verification Plan

### Automated Tests
- Run `pytest tests/test_topology_nodes_contract.py -v` (all tests pass).
- Run `pytest tests/ -v` (full suite passes with 0 regressions).
- Run `npm run build` in `dashboard/` (clean Vite build).

### Manual / Browser Verification
- Open [http://localhost:5173/](http://localhost:5173/)
- In Network Operations, navigate to "Topology" (Graph View).
- Inspect device nodes:
  - Verify vector role icons appear on each node card (Core server, Distribution shield, Access switch).
  - Verify hostname, IP, and location are displayed clearly.
  - Verify alert count badges (`⚠ N Alert(s)` or `✓ Nominal`).
  - Verify critical nodes have an animated radar pulse ring.
- Click a node card:
  - Verify glowing blue highlight ring appears around the node.
  - Verify the 580px slide-out SRE details drawer opens with live telemetry, alert triage, inventory, and action bar.
- Test Filter Reactivity:
  - Click "Critical" health filter chip: verify critical nodes stay bright while nominal/warning nodes dim to ~18% opacity.
  - Click "Core" role filter chip: verify core nodes stay bright while distribution and access nodes dim.
  - Type in the search box: verify matching hostnames stay illuminated while non-matches dim.
  - Click "Clear Filters": verify all nodes return to full brightness.
