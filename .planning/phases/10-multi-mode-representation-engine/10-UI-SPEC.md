---
phase: 10
slug: multi-mode-representation-engine
status: approved
shadcn_initialized: false
preset: none
created: 2026-10-01
---

# Phase 10 — UI Design Contract: Multi-Mode Representation Engine

> Visual, structural, and interaction design contract for the 3 representation modes in the Network Operations Center: Executive Topology, SRE High-Density Table, and Regional Site Matrix.

---

## Design System & Tokens

| Property | Value |
| :--- | :--- |
| **Component Library** | Custom React + Vanilla CSS (Aligned with existing design tokens) |
| **Icons** | `lucide-react` (`Layers`, `Table`, `Globe`, `Server`, `Shield`, `Wifi`, `ArrowUpDown`, `ChevronRight`, `ExternalLink`, `Activity`) |
| **Fonts** | Inter (primary UI), SFMono-Regular / Menlo / Monaco / Consolas (monospace IDs) |
| **View Modes** | `'topology'` (Executive Topology), `'table'` (SRE Table), `'matrix'` (Regional Site Matrix) |
| **Persistence** | `localStorage.getItem('dnac_noc_view_mode') || 'topology'` |

---

## 1. Segmented View Switcher (`NOC-VIEW-01`)

### Placement & Layout
Integrated on the right side of the filter toolbar `.filter-bar`:
```css
.noc-view-switcher {
  display: flex;
  align-items: center;
  gap: 2px;
  background: var(--bg-tertiary);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-md);
  padding: 2px;
  margin-left: auto;
}

.noc-view-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0.35rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-tertiary);
  background: transparent;
  border: 1px solid transparent;
  border-radius: calc(var(--radius-md) - 2px);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.noc-view-btn:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.05);
}

.noc-view-btn.active {
  background: var(--card-bg);
  color: var(--accent-blue);
  border-color: rgba(37, 99, 235, 0.25);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

---

## 2. Executive Topology View (`NOC-VIEW-02`)

### 3-Tier Network Hierarchy
Devices are partitioned into 3 infrastructure tiers:
1. **Core & WAN Backbone** (`tier-core`): Routers, Gateways, Core switches (`RT`, `Core`, `GW`, `Router`, `Dist-Router`).
   - Icon: `<Server size={18} />`, Accent: `var(--accent-blue)`.
2. **Distribution & Security Perimeter** (`tier-dist`): Firewalls, policy switches (`FW`, `Dist`, `Firewall`, `SW01`).
   - Icon: `<Shield size={18} />`, Accent: `var(--accent-purple)`.
3. **Campus & Access Edge** (`tier-access`): Access switches, Wireless APs (`AP`, `Access`, `Switch`, `WLC`, `SW02`).
   - Icon: `<Wifi size={18} />`, Accent: `var(--accent-teal)`.

### Tier Group Header
- Left: Tier Icon in styled container, Tier Title, Subtitle (e.g. `"Backbone routing and external WAN transit"`).
- Right: Roll-up health summary badge: `<span className="noc-tier-summary">N Devices • X Critical • Y Warning</span>`.
- Body: 2–3 column responsive device card grid (`.device-grid`).

---

## 3. SRE High-Density Sortable Table (`NOC-VIEW-03`)

### Layout & Columns
Bounded table container with max height `560px` and sticky column header:
- **Columns**:
  1. `Device Name`: Monospaced font with health status dot indicator.
  2. `Location`: Clean country flag and site code badge.
  3. `Infrastructure Tier`: Badge pill (`CORE`, `DIST/SEC`, `ACCESS`).
  4. `Health Status`: Visual badge (`HEALTHY`, `WARNING`, `CRITICAL`).
  5. `Active Alerts`: Count pill with severity breakdown.
  6. `ServiceNow Incident`: Monospaced incident number (e.g. `INC0012345`) or `"None"`.
  7. `Last Seen`: Formatted time with clock icon.
  8. `Actions`: Compact "Inspect" pill button opening detail drawer.

### Interactive Sorting
- Clicking column headers toggles sort (`asc` / `desc`).
- Default sort: Criticality descending (Critical first, then Warning, then Healthy).

---

## 4. Regional Site Matrix View (`NOC-VIEW-04`)

### Layout `.noc-matrix-grid`
```css
.noc-matrix-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 1rem;
}
```

### Site Card `.noc-site-card`
- **Header**: Country flag emoji, City & Location Name (e.g. `🇬🇧 United Kingdom — London`), Status Pill (`NOMINAL`, `DEGRADED`, `CRITICAL`).
- **Telemetry Chips**:
  - Total Devices: e.g. `3 Nodes`.
  - Active Alerts: e.g. `1 Active Alert` or `0 Alerts (Clean)`.
  - Avoided Tickets: e.g. `2 Filtered`.
- **Action**: "Inspect Site Devices →" button that filters the inventory to that location and transitions to Topology view.
