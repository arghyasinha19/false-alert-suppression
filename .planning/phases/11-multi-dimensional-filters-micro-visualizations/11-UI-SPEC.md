# Phase 11: Multi-Dimensional Filters & Micro-Visualizations - UI Design Contract

**Phase:** 11  
**Milestone:** v1.5 Executive & Observability Network Operations Center (NOC) Overhaul  
**Status:** Approved Specification  

---

## 1. Visual Hierarchy & Layout Architecture

Phase 11 introduces a two-tier filter controls layout and dynamic card micro-visualizations:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Filter Bar (Tier 1)                                                                    │
│ [ 🔍 Search devices, locations... ]   [ Clear ]   [ Topology | SRE Table | Site Matrix ]│
└────────────────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Filter Strip (Tier 2 - Multi-Dimensional Chips)                                        │
│  Role:   [ All 12 ] [ Core 4 ] [ Dist 2 ] [ Access 3 ] [ Wireless 2 ] [ Security 1 ]   │
│  Health: [ All 12 ] [ 🔴 Critical 3 ] [ 🟡 Warning 4 ] [ 🟢 Healthy 5 ]                │
│  Ticket: [ All ] [ 🎫 Has Incident 4 ] [ 🛡️ Clean 8 ]     [ ⟲ Reset All Filters ]      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Specifications

### 2.1 Filter Strip (`.noc-filter-strip`)
- **Container**:
  - `background: var(--bg-secondary)`
  - `border: 1px solid var(--card-border)`
  - `border-radius: var(--radius-md)`
  - `padding: 0.65rem 1rem`
  - `display: flex; flex-direction: column; gap: 0.6rem; margin-bottom: 1.25rem;`
  - Horizontal grouping with label, chip pills, and counts.
- **Chip Groups**:
  - **Role Filter (`roleFilter`)**:
    - Chips: `All`, `Core`, `Distribution`, `Access`, `Wireless`, `Security`
    - Each chip has an icon (e.g. `Server`, `GitFork`, `Wifi`, `ShieldCheck`) and a small count badge `(N)`.
  - **Health Filter (`healthFilter`)**:
    - Chips: `All`, `Critical`, `Warning`, `Healthy`
    - Indicator dots: Red for Critical, Yellow for Warning, Green for Healthy.
  - **ServiceNow Filter (`snowFilter`)**:
    - Chips: `All`, `Has Incident`, `New`, `Reopened`, `Clean`
    - Icon: `Ticket` or `Shield`.
  - **Reset Pill (`.noc-filter-reset-btn`)**:
    - Appears when any filter differs from default (`role !== 'all' || health !== 'all' || snow !== 'all' || searchQuery !== ''`).
    - Icon `<RotateCcw size={11} />`, clickable to restore defaults.

### 2.2 24-Hour Alert Activity Sparkline (`DeviceSparkline`)
- **SVG Micro-Component**:
  - Width: 100%, Height: 22px
  - 12 or 24 hourly time buckets.
  - Rendered as rounded vertical mini-bars (width: 3px, gap: 2px) or a smooth gradient filled area curve.
  - Fill gradient:
    - Nominal: cyan to blue (`#06b6d4` to `#3b82f6`)
    - Alerting: amber to red (`#f59e0b` to `#ef4444`)
  - Subtitle or label: `"24h Activity: N alerts"`.

### 2.3 Live Severity Distribution Mini-Bar (`SeverityMiniBar`)
- **Segmented Stacked Bar**:
  - Width: 100%, Height: 4px, `border-radius: 999px`, `overflow: hidden`, `display: flex`.
  - Segments:
    - Critical (Sev 1): `#ef4444`
    - Warning (Sev 2): `#f59e0b`
    - Minor/Info (Sev 3): `#3b82f6`
  - Nominal device with 0 active alerts:
    - Single soft green track (`rgba(16, 185, 129, 0.4)`) indicating 100% nominal state.

### 2.4 Status Radar Pulse Animation
- **Critical Status Pulse**:
  ```css
  @keyframes noc-radar-pulse {
    0% {
      box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
    }
    70% {
      box-shadow: 0 0 0 7px rgba(239, 68, 68, 0);
    }
    100% {
      box-shadow: 0 0 0 0 rgba(239, 68, 68, 0);
    }
  }
  ```
  Applied to `.device-tile-status-dot.critical` and table critical status badges.

---

## 3. SRE Table Integration

In the SRE High-Density Table (`viewMode === 'table'`):
- Add a new column: **"24h Activity & Severity"** between `Active Alerts` and `ServiceNow`.
- Displays an inline micro-sparkline (width: 70px, height: 16px) paired with the mini severity bar.
- Enables SREs to evaluate temporal alert density at a single glance during emergency triaging.

---

## 4. Theme & Design Token Compatibility

| Token | Light Theme | Dark Theme | Purpose |
| :--- | :--- | :--- | :--- |
| `var(--bg-secondary)` | `#ffffff` | `#1e293b` | Filter strip background |
| `var(--bg-tertiary)` | `#f8fafc` | `#0f172a` | Inactive chip background |
| `var(--card-border)` | `rgba(226, 232, 240, 0.8)` | `rgba(255, 255, 255, 0.08)` | Chip border |
| `var(--accent-blue)` | `#3b82f6` | `#60a5fa` | Active chip fill |
| `var(--health-critical)`| `#ef4444` | `#f87171` | Critical chip & sparkline peak |
| `var(--health-warning)` | `#f59e0b` | `#fbbf24` | Warning chip & sparkline mid |
| `var(--health-healthy)` | `#10b981` | `#34d399` | Healthy chip & sparkline low |

---

## 5. Responsive Behavior

- **Desktop (> 1200px)**: Filter rows display side-by-side or stacked in 2 clean rows with chips aligned left and Reset button aligned right.
- **Tablet (768px - 1199px)**: Chip rows wrap smoothly with flex wrapping, preserving touch target minimums of 32px height.
- **Mobile (< 768px)**: Chip groups scroll horizontally with custom minimal scrollbars (`.noc-chip-scroll`).
