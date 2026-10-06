---
phase: 24
slug: global-multi-site-wan-interconnect-canvas
status: approved
shadcn_initialized: false
preset: none
created: 2026-10-06
reviewed_at: 2026-10-06
---

# Phase 24 — UI Design Contract: Global Multi-Site WAN Interconnect Canvas

> Visual and interaction design contract for Level 1 Global Multi-Site WAN Topology (`SITE-01`, `SITE-02`, `SITE-03`). Establishes the macro site node geometry, health status badges, blast radius halos, curved WAN transit interconnects with dynamic latency badges, and level indicator header banner.

---

## Design System Tokens & Properties

| Property | Value |
|----------|-------|
| Framework | React 19 + Native SVG (Vanilla CSS) |
| Typography Tokens | `--font-xs` (12px), `--font-sm` (13px), `--font-md` (15px), `--font-lg` (18px), `--font-xl` (24px), `--font-2xl` (34px) |
| Color Tokens | `--card-bg`, `--card-border`, `--text-primary`, `--text-secondary`, `--text-tertiary`, `--accent-blue`, `--accent-emerald`, `--accent-amber`, `--accent-rose` |
| Icons (`lucide-react`) | `Globe`, `Radio`, `Activity`, `AlertTriangle`, `CheckCircle`, `Zap`, `ChevronRight`, `Maximize2`, `Minimize2`, `RotateCcw`, `Compass`, `ShieldAlert` |

---

## 1. Canvas Architecture & Header Banner (`SITE-01`)

The topology graph container features a dedicated Level 1 WAN presentation state:

```
┌────────────────────────────────────────────────────────────────────────┐
│ [● GLOBAL WAN TOPOLOGY]   8 Connected Sites   •   Fleet Resilience 92% │
│                                         [100%] [Fit] [Reset] [⛶ Full]  │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│         [🇬🇧 UK-LON] <======= 24ms =======> [🇩🇪 DE-FRA]                │
│              ║                                   ║                     │
│            115ms                               128ms                   │
│              ║                                   ║                     │
│         [🇺🇸 US-NY]  <======= 195ms ======> [🇸🇬 SG-SIN]                │
│                                                  ║                     │
│                                                42ms                    │
│                                                  ║                     │
│                                             [🇮🇳 IN-MUM]               │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Level 1 Banner Specifications
- **Badge Element**: `.noc-topology-level-badge`
  - Background: `rgba(59, 130, 246, 0.12)` (dark: `rgba(96, 165, 250, 0.18)`)
  - Border: `1px solid var(--accent-blue)`
  - Text: `--font-xs` (12px), `font-weight: 700`, uppercase letter-spacing `0.06em`
  - Content: `<Globe size={13} /> GLOBAL WAN TOPOLOGY (LEVEL 1)`
- **WAN Stats Pill**: Shows registered site count (`N Connected Sites`) and fleet resilience score.

---

## 2. Macro Site Node Geometry & Health Rollup (`SITE-01`, `SITE-02`)

Each registered geographic site is rendered as an interactive SVG/HTML macro node:

```
┌───────────────────────────────────────────────┐
│ 🇬🇧 UK-LON (London)         [ NOMINAL ● ]      │
│ 14 Devices Registered                         │
├───────────────────────────────────────────────┤
│ Active Alerts: 0         Avoided Tickets: 12  │
│ Blast Radius: 0%         [ Drill Down → ]     │
└───────────────────────────────────────────────┘
```

### Node Dimensions & Attributes
- **Dimensions**: Width `240px`, Height `110px`, Corner Radius `12px` (`rx="12"`).
- **Background**:
  - Dark mode: `rgba(17, 24, 39, 0.75)` with backdrop-filter blur `12px`
  - Light mode: `rgba(255, 255, 255, 0.85)` with box-shadow `0 8px 24px rgba(0, 0, 0, 0.06)`
- **Border**:
  - Nominal: `1px solid var(--card-border)`
  - Degraded: `1.5px solid var(--accent-amber)`
  - Critical: `2px solid var(--accent-rose)`
- **Typography**:
  - Site Title: `--font-md` (15px), weight `700`, `--text-primary`
  - Subtitle / Device Count: `--font-xs` (12px), weight `500`, `--text-secondary`
  - Metrics: `--font-xs` (12px), mono figures `font-variant-numeric: tabular-nums`

### Blast Radius Perimeter Halo
- When a site has critical/warning alerts, an animated SVG perimeter halo pulse is rendered:
  - Critical: Red stroke `#ef4444`, `stroke-width: 3px`, opacity cycling `0.2` to `0.7` via `@keyframes blastRadiusPulse`
  - Degraded: Amber stroke `#f59e0b`, `stroke-width: 2px`
- Badge chip inside card: Displays `Blast Radius: N%` calculated as `(degraded_devices / total_site_devices) * 100`.

---

## 3. Inter-Site WAN Interconnect Links & Telemetry (`SITE-03`)

### Link Topology & Coordinates
- **Primary Transit Backbone**: Connects Core Tier Data Center Hubs:
  - `UK-LON (London)` ↔ `DE-FRA (Frankfurt)` (24ms, 100G Backbone)
  - `UK-LON (London)` ↔ `US-NY (New York)` (115ms, Transatlantic Subsea)
  - `DE-FRA (Frankfurt)` ↔ `SG-SIN (Singapore)` (128ms, Eurasia Terrestrial)
  - `SG-SIN (Singapore)` ↔ `IN-MUM (Mumbai)` (42ms, APAC Subsea)
  - `SG-SIN (Singapore)` ↔ `AU-SYD (Sydney)` (92ms, Oceanic Link)
  - `US-NY (New York)` ↔ `US-CHI (Chicago)` (18ms, Inter-City Metro)
  - `UK-LON (London)` ↔ `UK-MAL (Maldon)` (6ms, Regional Metro)

### Visual Styling & Flow Animations
- **Curve**: Cubic Bezier SVG path (`M ... C ...`) with smoothed curvature.
- **Stroke Width**: `3px` for primary backbone, `2px` for branch uplinks.
- **Stroke Dash Flow**:
  ```css
  @keyframes wanFlow {
    from { stroke-dashoffset: 40; }
    to { stroke-dashoffset: 0; }
  }
  .noc-wan-link.active-flow {
    stroke-dasharray: 6 6;
    animation: wanFlow 1.8s linear infinite;
  }
  ```
- **Status Colors**:
  - Nominal: `var(--accent-blue)` / `#3b82f6` (flow: `#60a5fa`)
  - Degraded: `var(--accent-amber)` / `#f59e0b`
  - Critical: `var(--accent-rose)` / `#ef4444`

### Dynamic Latency Badge Markers
- At the midpoint `(midX, midY)` of each WAN link:
  - Circular or rounded pill badge: Width `54px`, Height `22px`, `rx="11"`
  - Background: `var(--card-bg)` with `1px solid var(--card-border)`
  - Text: `--font-xs` (11-12px), mono font, weight `600` (e.g. `24ms`, `115ms`)
  - Tooltip: Full details on hover (Link ID, Bandwidth, Connected Sites, Packet Loss %).

---

## 4. Accessibility & Interaction Contracts

1. **Touch & Click Targets**: Macro site cards have a 240x110px clickable area and the "Drill Down" button has a minimum 32px hit height.
2. **Keyboard Navigation**: Macro site nodes support `tabindex="0"`, `aria-label="Site [Name], Health: [Status]"`, and trigger on `Enter`/`Space`.
3. **Responsive Scaling**: Adapts smoothly to viewport pan and zoom from `k = 0.5` to `k = 1.8`.
4. **Theme Contrast**: All node titles, badges, and latency labels maintain >= 4.5:1 contrast in both light and dark themes.
