---
phase: 10
plan: 1
type: implementation
prefix: NOC-VIEW
wave: 1
depends_on: []
files_modified:
  - dashboard/src/NetworkOperations.jsx
  - dashboard/src/App.css
---

# Plan 10-01: Multi-Mode Representation Engine

> Implement 3 distinct operational view modes for Network Operations: Executive Topology (3-Tier infrastructure hierarchy), SRE High-Density Sortable Table (rapid tabular triage), and Regional Site Matrix (interactive geo-health cards), controlled via a consolidated segmented toolbar switcher.

---

## Requirements Covered

- **NOC-VIEW-01**: User can toggle between 3 presentation modes: "Executive Topology", "SRE High-Density Table", and "Regional Site Matrix" with seamless animated state switching.
- **NOC-VIEW-02**: In Executive Topology view, devices are organized by network infrastructure tier (Core & WAN, Distribution & Security, Campus & Access) with roll-up health indicators.
- **NOC-VIEW-03**: In SRE High-Density Table view, user can sort by device name, active alerts, severity, last seen, and health with inline status chips and sticky headers.
- **NOC-VIEW-04**: In Regional Site Matrix view, user can view site-level health status cards with quick-click filtering by site.

---

## Tasks

### Task 1: Implement Tier Classification and Site Matrix Memos in `NetworkOperations.jsx`
- **File:** `dashboard/src/NetworkOperations.jsx`
- **Action:**
  - Import Lucide icons: `Layers`, `Table`, `Globe`, `ArrowUpDown`, `ChevronRight`, `Cpu`, `ExternalLink`.
  - Add helper function `deriveDeviceTier(deviceName)`:
    - Tier 1: `CORE`: matches `core`, `router`, `rt`, `gw`, `dist-router`
    - Tier 2: `DIST_SEC`: matches `fw`, `dist`, `firewall`, `sw01`
    - Tier 3: `ACCESS`: matches `ap`, `access`, `switch`, `wlc`, `sw02`, and fallbacks
  - Define `tierGroups` memo organizing `filteredDevices` into Core, Distribution/Security, and Access tiers with roll-up device and health counts.
  - Define `siteMatrix` memo organizing `filteredDevices` into regional site cards with health status, device counts, and active alert summaries.
  - Initialize `viewMode` state with `localStorage` persistence:
    ```javascript
    const [viewMode, setViewMode] = useState(() => localStorage.getItem('dnac_noc_view_mode') || 'topology');
    ```

### Task 2: Implement Segmented View Switcher in Filter Toolbar
- **File:** `dashboard/src/NetworkOperations.jsx`
- **Action:**
  - Place `.noc-view-switcher` inside `.filter-bar` on the right side.
  - Render 3 buttons:
    - `Topology`: `<Layers size={14} /> Topology`
    - `Table`: `<Table size={14} /> SRE Table`
    - `Matrix`: `<Globe size={14} /> Site Matrix`
  - On click, update `viewMode` and persist to `localStorage`.

### Task 3: Build View Renderers in `NetworkOperations.jsx`
- **File:** `dashboard/src/NetworkOperations.jsx`
- **Action:**
  - **Topology View (`viewMode === 'topology'`)**:
    - Render 3 tier sections with distinct tier icons, titles, descriptive subtitles, and roll-up health summary badges.
    - Inside each tier, render responsive multi-column device grid.
  - **SRE Table View (`viewMode === 'table'`)**:
    - Render `.noc-sre-table-wrap` containing table with sticky header.
    - Interactive sorting on: `Device Name`, `Location`, `Tier`, `Health`, `Alerts`, `SNOW Incident`, `Last Seen`.
    - Compact rows with monospaced device names, incident badges, and "Inspect" action button opening device detail drawer.
  - **Regional Site Matrix View (`viewMode === 'matrix'`)**:
    - Render `.noc-matrix-grid` with interactive cards for each site.
    - Site cards display flag, site label, status pill (`NOMINAL`, `DEGRADED`, `CRITICAL`), total devices, active alerts, and "Inspect Site Devices →" button.
    - Clicking the button sets `searchQuery` to the site location and switches view to `topology` or `table`.

### Task 4: Add CSS Styles in `dashboard/src/App.css`
- **File:** `dashboard/src/App.css`
- **Action:**
  - Define `.noc-view-switcher` and `.noc-view-btn` styles with active state and hover effects.
  - Define `.noc-tier-section`, `.noc-tier-header`, `.noc-tier-summary` styles.
  - Define `.noc-sre-table-wrap`, `.noc-sre-table`, sort header indicators, and inspect action button.
  - Define `.noc-matrix-grid`, `.noc-site-card`, and hover transitions.
  - Ensure full responsiveness and dark/light theme token compliance.

### Task 5: Verification & Health Checks
- **Action:**
  - Run `npm run lint` and `npm run build` in `dashboard/` to confirm 0 errors.
  - Test mode switching between Topology, Table, and Matrix in live browser.
  - Verify sorting in SRE table and click-to-filter drilldown in Site Matrix.

---

## Verification Checklist

- [ ] `npm run build` passes with 0 errors.
- [ ] `oxlint` passes with 0 warnings.
- [ ] Segmented view switcher allows toggling between Topology, SRE Table, and Site Matrix.
- [ ] Selected view mode persists across page refreshes via `localStorage`.
- [ ] Topology view groups devices by 3 infrastructure tiers with accurate roll-up badges.
- [ ] SRE Table view displays sortable columns with sticky headers and inspect buttons.
- [ ] Site Matrix view displays regional site health cards with click-to-filter drilldowns.
- [ ] Dark and light themes render beautifully across all 3 view modes.
