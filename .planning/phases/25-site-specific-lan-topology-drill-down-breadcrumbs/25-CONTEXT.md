# Phase 25: Site-Specific LAN Topology Drill-Down & Breadcrumbs - Context

**Gathered:** 2026-10-06  
**Status:** Ready for planning  
**Mode:** Smart Discuss (Autonomous Mode)

<domain>
## Phase Boundary

Implement Level 2 Site LAN tier graph drill-down with responsive breadcrumb navigation, interactive site-switcher dropdown, and site-scoped device filtering (`SITE-04`, `SITE-05`, `SITE-06`).
</domain>

<decisions>
## Implementation Decisions

### Area 1: Level 2 Site LAN Drill-Down & Tier Presentation (`SITE-04`)
- **Site Drill-Down Entrypoints**:
  - Clicking any macro site node or its "Drill Down" button on the Level 1 WAN canvas.
  - Selecting any site from the persistent site-switcher dropdown in the canvas toolbar.
- **LAN Tier Layout**:
  - Scopes node rendering strictly to the selected site's hardware fleet (`scopedDevices`).
  - Lays out devices across 3 hierarchical horizontal tiers:
    - `Core & WAN Backbone` (top tier)
    - `Distribution & Security Perimeter` (middle tier)
    - `Campus & Access Edge` (bottom tier)
  - Displays localized tier statistics badge showing device count, criticals, warnings, and nominal devices for that specific site.
- **Site Header Banner**:
  - Renders site flag, site code, site descriptive name, device count, active alarm pill, and avoided tickets counter.

### Area 2: Responsive Breadcrumb Navigation & Site Switcher (`SITE-05`)
- **Breadcrumb Structure**:
  - Container `.noc-topology-breadcrumbs`:
    `[Globe] Global WAN Interconnect` (clickable button, returns to Level 1)
    `>` (ChevronRight divider)
    `[Site Flag] [Site Code] — [Site Label]` (active site badge)
- **Inline Site Switcher**:
  - Next to the breadcrumbs, an interactive site dropdown selector `.noc-site-switcher-select` allowing direct site-to-site hopping (e.g. jumping from `UK-LON` directly to `SG-SIN` without returning to global overview).
  - Lists each registered site with its status indicator (`● Nominal`, `⚠ Degraded`, `✖ Critical`) and device count.
- **Single-Click Global Return**:
  - Clicking the root breadcrumb or the "Back to Global WAN" button smoothly resets zoom and returns to Level 1 WAN view.

### Area 3: Site-Scoped Filtering & Context Preservation (`SITE-06`)
- **Scoped Filter Evaluation**:
  - Device search query, role filter, and health filter evaluate only against the selected site's devices.
  - The match badge displays `Filtered: X of Y devices in [Site Code]` with a single-click "Clear" action.
  - Resetting filters preserves the current site view without resetting the `selectedSite` or `topologyLevel`.
- **Keyboard Navigation**:
  - Pressing `Backspace` or `Alt+Left` when no input is focused, or clicking the breadcrumb root, navigates back to Global WAN.
</decisions>

<code_context>
## Existing Code Insights

- `TopologyGraphView.jsx` currently accepts `topologyLevel = 'wan'`, `selectedSite`, `onSelectSite`, and `onReturnToWan`.
- `NetworkOperations.jsx` maintains `topologyLevel` and `selectedSite` state.
- `LOCATION_LABELS` and `FLAG_MAP` provide regional names and emojis.
- `tests/test_multi_site_wan_contract.py` already verifies Phase 24 baseline.
</code_context>

<deferred>
## Deferred Ideas

- Cross-view synchronization between Regional Site Matrix table selection and Topology graph is handled in Phase 26 (`SITE-07`, `SITE-08`).
</deferred>
