# Phase 26: Cross-View Site Synchronization & Filter Alignment - Context

**Gathered:** 2026-10-06  
**Status:** Ready for planning  
**Mode:** Smart Discuss (Autonomous Mode)

<domain>
## Phase Boundary

Synchronize site selection and location filtering bi-directionally across Regional Site Matrix, SRE High-Density Table, and Multi-Site Topology views (`SITE-07`, `SITE-08`).
</domain>

<decisions>
## Implementation Decisions

### Area 1: Regional Site Matrix to Topology LAN Synchronization (`SITE-07`)
- **Site Card Interaction**:
  - In `viewMode === 'matrix'`, each site card (`.noc-site-card`) supports single-click selection and includes an explicit "Inspect Site Topology" drilldown button (`.noc-site-drilldown-btn`).
  - Clicking a site card or drilldown button sets `selectedSite(site.code)`, transitions `topologyLevel` to `'lan'`, switches `viewMode` to `'topology'`, and displays a toast confirmation.
  - Active site card displays a glowing border highlight and `.active-site` badge when `selectedSite === site.code`.

### Area 2: SRE Table & Filter Bar Location Alignment (`SITE-08`)
- **Multi-Dimensional Filter Bar**:
  - Adds a dedicated `Site:` filter cluster (`.noc-filter-cluster`) with an `All Sites (Global)` pill plus individual site pills (`UK-LON`, `DE-FRA`, etc.) displaying registered device counts.
  - Clicking a site pill synchronizes `selectedSite` and switches `topologyLevel` to `'lan'`. Clicking `All Sites (Global)` clears `selectedSite` and switches `topologyLevel` to `'wan'`.
- **SRE High-Density Table**:
  - Location table cells (`.noc-table-loc-btn`) are rendered as accessible interactive buttons.
  - Clicking any device's location in the table filters the active site scope to that location and synchronizes the active site across Topology and Matrix views.
- **Global Reset**:
  - The `Reset Filters` button clears all active search queries, role, health, and ticket filters, and resets `selectedSite` to `null` (`topologyLevel: 'wan'`).
</decisions>

<code_context>
## Existing Code Insights

- `NetworkOperations.jsx` has `selectedSite` and `topologyLevel` state hooks.
- `siteMatrix` already groups devices by location with health aggregates.
- `TopologyGraphView.jsx` accepts `selectedSite`, `topologyLevel`, `onSelectSite`, and `onReturnToWan`.
- `App.css` styles `.noc-filter-chip`, `.noc-filter-cluster`, and `.noc-site-card`.
</code_context>
