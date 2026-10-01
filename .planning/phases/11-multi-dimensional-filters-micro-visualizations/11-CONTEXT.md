# Phase 11: Multi-Dimensional Filters & Micro-Visualizations - Context

**Gathered:** 2026-10-01  
**Status:** Ready for planning  
**Milestone:** v1.5 Executive & Observability Network Operations Center (NOC) Overhaul  

---

<domain>
## Phase Boundary

Phase 11 equips the Network Operations Center with rapid multi-dimensional filtering and rich device-level micro-visualizations:
1. **Multi-Dimensional Filter Chips (`NOC-VIZ-01`, `NOC-VIZ-02`)**:
   - Filter device inventory across 3 independent operational dimensions:
     - **Device Role**: `All Roles`, `Core & WAN`, `Distribution`, `Access Edge`, `Wireless`, `Security Perimeter`.
     - **Health Status**: `All Status`, `Critical`, `Warning`, `Healthy`.
     - **ServiceNow Ticket State**: `All Tickets`, `Active Incident`, `New Incident`, `Reopened`, `Clean / No Incident`.
   - Real-time count badges on each filter chip showing matching device volume.
   - Filter state seamlessly applies across all 3 representation modes (Executive Topology, SRE High-Density Table, Regional Site Matrix).
   - "Reset Filters" pill displayed whenever any non-default filter is active.
2. **24-Hour Alert Activity Sparklines (`NOC-VIZ-03`)**:
   - Embedded micro-bar/sparkline on each device tile and table row displaying hourly event density over the preceding 24-hour window.
   - Visual color coding reflecting alert intensity (cool cyan/blue for nominal volume, orange/red for spike periods).
   - Tooltip indicating peak volume and recent activity window.
3. **Live Severity Breakdown Mini-Bars & Pulsing Indicators (`NOC-VIZ-04`)**:
   - Proportional multi-segment horizontal mini-bar on each device card depicting the breakdown between Critical (Sev 1), Warning (Sev 2), and Minor/Info (Sev 3/4) alerts.
   - Radial radar pulse animation on status indicators for devices experiencing active Critical alerts.
   - Subtle nominal green micro-bar for devices operating with 100% nominal availability.

</domain>

---

<decisions>
## Implementation Decisions

### Filter Toolbar Architecture
- **D-01 (Two-Tier Filter Structure):**
  - **Tier 1 (Top Bar - `.filter-bar`)**: Contains Search input, Clear search button, Segmented View Switcher (`Topology` | `SRE Table` | `Site Matrix`), and Total Devices counter.
  - **Tier 2 (Secondary Filter Strip - `.noc-filter-strip`)**: Positioned directly beneath Tier 1, featuring horizontally scrollable/wrapping chip groups for **Role**, **Health**, and **ServiceNow Tickets**, with count badges and an inline "Clear All Filters" button.
- **D-02 (Multi-Dimensional Combinatorial Logic):**
  - Filters combine using boolean `AND` across categories (e.g. `Role == Wireless` AND `Health == Critical` AND `Search == 'AP'`).
  - Devices matching the combined criteria are passed down to all active representation modes.

### Role Classification Taxonomy
- **D-03 (6 Role Categories):**
  - `all`: All Devices
  - `core`: Core & WAN Backbone (Routers, Gateways, DC Core)
  - `dist`: Distribution (Aggregation & Policy Switches)
  - `access`: Campus & Access (Edge Switches)
  - `wireless`: Wireless Access (WLCs, APs)
  - `security`: Security Perimeter (Firewalls, VPN Gateways)
  - Implemented via `deriveDeviceRole(device)` inspecting hostnames, categories, and tags.

### Micro-Visualizations Specification
- **D-04 (24h Activity Sparkline):**
  - High-performance SVG sparkline component (`DeviceSparkline`) rendering 12 or 24 bars or smooth SVG polyline.
  - Calculated from alert timestamps over the last 24 hours with deterministic fallback based on device alert history.
  - Height: 20px, Width: 100% (or fixed 70px in table cell).
- **D-05 (Severity Mini-Bar):**
  - Horizontal stacked bar (height 4px, border-radius 2px) showing percentage of Sev 1 (Red), Sev 2 (Orange), and Sev 3 (Blue).
  - Placed directly beneath the sparkline or meta row on device tiles.
- **D-06 (Pulsing Radar Dot):**
  - Critical devices emit a pulsing ripple animation (`noc-pulse-radar` with CSS `@keyframes` expanding outer box-shadow ring).

</decisions>

---

<canonical_refs>
## Canonical References

### Project & Roadmap Specs
- `.planning/PROJECT.md` — Core value, system architecture, and milestone goals
- `.planning/REQUIREMENTS.md` § Milestone v1.5 — `NOC-VIZ-01` through `NOC-VIZ-04`
- `.planning/ROADMAP.md` § Phase 11 — Multi-Dimensional Filters & Micro-Visualizations

### Codebase References
- `dashboard/src/NetworkOperations.jsx` — Existing device state, view renderers, and detail drawer
- `dashboard/src/App.css` — Filter styles, badges, and animations
- `dashboard/src/AnimatedCounter.jsx` — Smooth count-up utility

</canonical_refs>
