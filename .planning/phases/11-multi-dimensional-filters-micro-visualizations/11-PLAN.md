---
phase: 11
plan: 1
type: implementation
prefix: NOC-VIZ
wave: 1
depends_on: []
files_modified:
  - dashboard/src/NetworkOperations.jsx
  - dashboard/src/App.css
---

# Plan 11-01: Multi-Dimensional Filters & Micro-Visualizations

> Equip Network Operations with rapid multi-dimensional filtering across Device Roles, Health states, and ServiceNow tickets, and augment device representations with 24-hour alert activity sparklines, severity breakdown mini-bars, and pulsing critical indicators.

---

## Requirements Covered

- **NOC-VIZ-01**: User can filter device inventory by Role chips (All, Core, Distribution, Access, Wireless, Security).
- **NOC-VIZ-02**: User can filter by Health status chips (All, Healthy, Warning, Critical) and ServiceNow ticket state.
- **NOC-VIZ-03**: User can see a 24-hour alert distribution micro-bar/sparkline on each device card showing activity volume over time.
- **NOC-VIZ-04**: User can see live severity distribution mini-bars and pulsing status indicators for active alerts.

---

## Tasks

### Task 1: Role Classification & Filter State in `NetworkOperations.jsx`
- **File:** `dashboard/src/NetworkOperations.jsx`
- **Action:**
  - Define `deriveDeviceRole(device)` helper identifying 5 roles: `core`, `distribution`, `access`, `wireless`, `security`.
  - Add filter states:
    - `roleFilter` (default `'all'`)
    - `healthFilter` (default `'all'`)
    - `snowFilter` (default `'all'`)
  - Update `filteredDevices` memo to apply search query AND `roleFilter` AND `healthFilter` AND `snowFilter`.
  - Compute dynamic count badges for each filter option based on current inventory.

### Task 2: Build Micro-Visualization Helpers & Components
- **File:** `dashboard/src/NetworkOperations.jsx`
- **Action:**
  - Build `getDeviceSparklineData(device)` helper generating 12/24 hourly activity buckets from alert timestamps.
  - Build `DeviceSparkline` SVG micro-component:
    - Renders 12 or 24 miniature bars or gradient polygon curve with intensity color coding.
    - Title/tooltip displaying 24h event count.
  - Build `SeverityMiniBar` micro-component:
    - Calculates active alert counts by severity (Sev 1, Sev 2, Sev 3).
    - Renders stacked horizontal bar (4px height) with red/orange/blue segments, or clean green bar if healthy.

### Task 3: Build Multi-Dimensional Filter Strip UI
- **File:** `dashboard/src/NetworkOperations.jsx`
- **Action:**
  - Render `.noc-filter-strip` directly below `.filter-bar`.
  - Group 1: **Role Chips** (`All`, `Core & WAN`, `Distribution`, `Access Edge`, `Wireless`, `Security`) with role icon and matching count badge.
  - Group 2: **Health Chips** (`All`, `Critical`, `Warning`, `Healthy`) with health color dots and counts.
  - Group 3: **ServiceNow Chips** (`All`, `Has Incident`, `Clean`) with ticket count badge.
  - Render "Reset All Filters" button (`<RotateCcw size={11} />`) when any filter is active.

### Task 4: Integrate Micro-Visualizations into Device Tiles & SRE Table
- **File:** `dashboard/src/NetworkOperations.jsx`
- **Action:**
  - In `renderDeviceTile(device)`:
    - Insert `DeviceSparkline` in the middle section of the tile.
    - Insert `SeverityMiniBar` below the alert count / status indicators.
  - In SRE High-Density Table (`viewMode === 'table'`):
    - Add a "24h Activity & Severity" column between `Active Alerts` and `ServiceNow`.
    - Render compact inline sparkline + mini-bar in each row.

### Task 5: CSS Styles & Pulsing Animations in `App.css`
- **File:** `dashboard/src/App.css`
- **Action:**
  - Add `.noc-filter-strip`, `.noc-filter-row`, `.noc-chip-group`, `.noc-filter-chip` (and `.active` state).
  - Add `.noc-filter-reset-btn` with hover transition.
  - Add `.noc-sparkline-wrap`, `.noc-sparkline-svg`, `.noc-sparkline-bar`.
  - Add `.noc-sev-bar-wrap`, `.noc-sev-bar`, `.noc-sev-seg`.
  - Implement `@keyframes noc-radar-pulse` for critical status indicators.

---

## Verification Plan

### Automated Checks
- Run `npm run lint` (`oxlint`) — must pass with 0 errors and 0 warnings.
- Run `npm run build` (`vite build`) — must compile cleanly without errors.

### Browser Visual & Functional Verification
- Navigate to `http://localhost:5173/` Network Operations tab.
- Click each Role filter chip (`Core`, `Distribution`, `Access`, `Wireless`, `Security`) and verify devices filter accurately in all 3 views.
- Click Health chips (`Critical`, `Warning`, `Healthy`) and verify instantaneous filtering.
- Click ServiceNow chips (`Has Incident`, `Clean`) and verify ticket state filtering.
- Click "Reset All Filters" and verify all filters reset to default.
- Verify 24h Activity sparkline and Severity mini-bar render crisply on device tiles and SRE table rows.
- Verify pulsing radar animation on Critical status indicators.
