# Phase 10: Multi-Mode Representation Engine - Context

**Gathered:** 2026-10-01  
**Status:** Ready for planning  

<domain>
## Phase Boundary

Phase 10 delivers a 3-mode Representation Engine for the Network Operations Center, enabling operators and executives to view the device fleet across three distinct operational lenses:
1. **Executive Topology View**: Tiered network hierarchy grouping (Core & WAN > Distribution & Security > Campus & Access) with roll-up health indicators.
2. **SRE High-Density Table View**: Compact, sortable telemetry table with sticky headers for rapid bulk triage.
3. **Regional Site Health Matrix**: Interactive site-by-site status cards displaying regional health, device counts, and click-to-filter drilldowns.

</domain>

<decisions>
## Implementation Decisions

### View Switcher Placement & Controls
- **D-01 (Toolbar Placement):** Consolidated directly inside the main filter toolbar on the right side, maintaining all filter and view controls in a unified control strip.
- **D-02 (Segmented Pill Styling):** The switcher uses a 3-button segmented pill group with iconography and text:
  - `<Layers size={14} /> Topology` (Executive Tier view)
  - `<Table size={14} /> SRE Table` (High-density sortable table)
  - `<Globe size={14} /> Site Matrix` (Regional geographic cards)
- **D-03 (State Persistence):** Selected view mode persists across page reloads in `localStorage` under key `'dnac_noc_view_mode'`.

### Infrastructure Tier Grouping Logic (Executive Topology)
- **D-04 (3-Tier Model):** Devices are categorized into three logical tiers based on naming semantics and roles:
  - **Tier 1: Core & WAN Backbone** (`RT`, `Core`, `GW`, `Router`, `Dist-Router`) — High-criticality infrastructure.
  - **Tier 2: Distribution & Security Perimeter** (`FW`, `Dist`, `Firewall`, `SW01`) — Routing & policy enforcement.
  - **Tier 3: Campus & Access Edge** (`AP`, `Access`, `Switch`, `WLC`, `SW02`) — End-user wireless and wired access.
- **D-05 (Tier Roll-Up Summary):** Each tier header features a telemetry summary badge showing device count and health distribution (e.g. `4 Devices • 1 Critical • 1 Warning • 2 Healthy`).

### SRE High-Density Table Specifications
- **D-06 (Columns):** Device Name, Location, Infrastructure Tier, Operational Health, Active Alerts, ServiceNow Incident, Last Alert Time, and Actions (`Inspect`).
- **D-07 (Default Sort):** Sorted by alert criticality descending (Critical devices on top, then Warning, then Healthy), with interactive column sorting on click.
- **D-08 (Sticky Headers):** Standardized sticky table header with glassmorphism blur matching Phase 7 table standards.

### Regional Site Matrix Specifications
- **D-09 (Site Cards):** Grid of cards representing each physical site/location displaying country flag, city name, site health status badge (`NOMINAL` / `DEGRADED` / `CRITICAL`), device count, and active alerts.
- **D-10 (Click-to-Drilldown):** Clicking any site card filters the device list to that site and provides quick navigation into the detailed device view.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project & Roadmap Specs
- `.planning/PROJECT.md` — Core value, system architecture, and milestone goals
- `.planning/REQUIREMENTS.md` § Milestone v1.5 — `NOC-VIEW-01` through `NOC-VIEW-04`
- `.planning/ROADMAP.md` § Phase 10 — Multi-Mode Representation Engine deliverables

### Codebase References
- `dashboard/src/NetworkOperations.jsx` — Existing device grid, location grouping, and detail panel
- `dashboard/src/App.css` — Table styles, badge styles, and segmented controls

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `deriveLocation` and `LOCATION_LABELS` in `NetworkOperations.jsx`: maps device names to geographic codes.
- `getDeviceHealth`: evaluates device health (`critical`, `warning`, `healthy`).
- Lucide React icons: `Layers`, `Table`, `Globe`, `Server`, `Shield`, `ArrowUpDown`, `ExternalLink`.

### Established Patterns
- Table scrolling with sticky headers and `backdrop-filter: blur(8px)`.
- Detail slide-out panel triggered by `openDevicePanel(device)`.

### Integration Points
- `NetworkOperations.jsx`: Introduce `viewMode` state (`'topology' | 'table' | 'matrix'`).
- Conditionally render view bodies based on `viewMode`.
- Add segmented switcher to the filter bar.
- Add CSS classes in `App.css` for `.noc-view-switcher`, `.noc-tier-group`, `.noc-matrix-grid`, `.noc-site-card`.

</code_context>

<specifics>
## Specific Ideas

- The segmented view switcher should feel smooth and tactile with micro-transitions on hover and active selection.
- SRE Table view allows enterprise operators with 50+ devices to scan through rows rapidly with monospace device and incident numbers.

</specifics>

<deferred>
## Deferred Ideas

- Interactive vector geographical map — Deferred to future milestone.

</deferred>

---

*Phase: 10-multi-mode-representation-engine*  
*Context gathered: 2026-10-01*
