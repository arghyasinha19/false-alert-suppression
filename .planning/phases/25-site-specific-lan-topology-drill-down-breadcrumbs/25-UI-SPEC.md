---
phase: 25
slug: site-specific-lan-topology-drill-down-breadcrumbs
status: approved
shadcn_initialized: false
preset: none
created: 2026-10-06
reviewed_at: 2026-10-06
---

# Phase 25 — UI Design Contract: Site-Specific LAN Topology Drill-Down & Breadcrumbs

> Visual and interaction design contract for Level 2 Site LAN Drill-Down, Breadcrumb Navigation, Site-Switcher Selector, and Scoped Device Filtering (`SITE-04`, `SITE-05`, `SITE-06`).

---

## Design System Tokens & Properties

| Property | Value |
|----------|-------|
| Framework | React 19 + Native SVG (Vanilla CSS) |
| Typography Tokens | `--font-xs` (12px), `--font-sm` (13px), `--font-md` (15px), `--font-lg` (18px), `--font-xl` (24px), `--font-2xl` (34px) |
| Color Tokens | `--card-bg`, `--card-border`, `--text-primary`, `--text-secondary`, `--text-tertiary`, `--accent-blue`, `--accent-emerald`, `--accent-amber`, `--accent-rose` |
| Touch Target Min | `32px` interactive element visible height, `44px` minimum hit area |
| Contrast Ratio | WCAG AAA compliant (>= 7:1 for normal text, >= 4.5:1 for badges/accents) |
| Icons (`lucide-react`) | `Globe`, `ChevronRight`, `ChevronDown`, `Layers`, `ArrowLeft`, `Filter`, `RotateCcw`, `Maximize2`, `Minimize2`, `ZoomIn`, `ZoomOut`, `Zap` |

---

## 1. Responsive Breadcrumb Bar & Navigation (`SITE-05`)

In Level 2 (Site LAN View), the top toolbar contains a responsive breadcrumb navigation bar `.noc-topology-breadcrumbs` with direct parent navigation and current context:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [← Back to Global WAN] │ [Globe] Global WAN  ›  [🇬🇧 UK-LON (London DC)] [▼ Switch Site] │ Filtered: 4/12 │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Component Breakdown
1. **Back Button (`.noc-wan-back-btn`)**:
   - Icon: `<ArrowLeft size={13} />`
   - Label: `Back to Global WAN`
   - Min-height: `32px`, padding: `4px 12px`, border-radius: `6px`
   - Background: `var(--card-bg)`, Border: `1px solid var(--card-border)`
   - Hover state: background `rgba(59, 130, 246, 0.12)`, border `var(--accent-blue)`
   - Accessible keyboard trigger: `Enter` / `Space`
2. **Breadcrumb Trail (`.noc-topology-breadcrumb-trail`)**:
   - Root Node: `<button type="button" className="noc-breadcrumb-item clickable">`
     - Icon: `<Globe size={13} />`
     - Text: `Global WAN Interconnect`
   - Separator: `<ChevronRight size={13} className="noc-breadcrumb-separator" />`
   - Leaf Node: `<span className="noc-breadcrumb-item active" aria-current="location">`
     - Flag emoji + Site Code + Site Label (e.g. `🇬🇧 UK-LON (London Core DC)`)
3. **Site Switcher Selector (`.noc-site-switcher-select`, `SITE-04`)**:
   - Positioned immediately alongside the breadcrumbs leaf.
   - Native accessible `<select>` or custom dropdown allowing instant switching between sites without returning to Level 1.
   - Options include: `UK-LON (London)`, `DE-FRA (Frankfurt)`, `US-NY (New York)`, `US-CHI (Chicago)`, `SG-SIN (Singapore)`, `IN-MUM (Mumbai)`, `AU-SYD (Sydney)`, `UK-MAL (Malmesbury)`.
   - Option values indicate site status: `[● NOMINAL]`, `[⚠ DEGRADED]`, `[✖ CRITICAL]`.

---

## 2. Level 2 Site LAN Tier Architecture (`SITE-04`)

When drilled into a site, the SVG canvas strictly displays the selected site's hardware fleet organized across the 3 deterministic hierarchical lanes:

### Tier Layout Specifications
- **Canvas Header Banner**:
  - Badge: `<Layers size={13} /> SITE LAN TOPOLOGY (LEVEL 2)`
  - Sub-label: Displays total devices in site, active alerts, avoided tickets, and uptime summary.
- **Lane 1: Core & WAN Backbone**:
  - `y = 130`, Blue border / header accent.
  - Houses site border routers (`lon-core-01`, `lon-core-02`, etc.) connecting the site to the WAN mesh.
- **Lane 2: Distribution & Security Perimeter**:
  - `y = 350`, Purple border / header accent.
  - Houses site firewalls and aggregation switches (`lon-fw-01`, `lon-dist-01`).
- **Lane 3: Campus & Access Edge**:
  - `y = 570`, Teal border / header accent.
  - Houses site access switches and PoE endpoints (`lon-acc-01`, `lon-acc-02`, `lon-ap-01`).

### Link Routing & Interconnects
- Renders hierarchical S-curves between Core ↔ Distribution and Distribution ↔ Access.
- Downlinks and redundant cross-links animate with live packet flow pulses (`noc-traffic-pulse`).

---

## 3. Site-Scoped Device Filtering (`SITE-06`)

Filtering controls (Search input, Role dropdown, Health pill chips) reactively filter only within the current site's device fleet:

- **Filter Scoping**:
  - If user searches `"fw"`, only matching devices in the current site remain bright; non-matches are dimmed (`opacity: 0.22`).
- **Filter Count Badge**:
  - Displays `Filtered: X of Y devices in [Site Code]`.
  - Includes a quick `Clear Filters` button (`<RotateCcw size={11} />`) with touch target >= 32px.
- **Context Preservation**:
  - Resetting filters maintains `selectedSite` and `topologyLevel === 'lan'` — never resets or navigates away from the active site view.

---

## 4. Interaction & Accessibility Requirements

1. **Keyboard Accessibility**:
   - `Escape`: If SRE drawer is closed and operator is in Level 2, pressing `Escape` or clicking `Back to Global WAN` returns to Level 1 Global WAN view.
   - Focus outline: All interactive buttons and selectors have `2px solid var(--accent-blue)` outline on `:focus-visible`.
2. **Hit Area**:
   - Breadcrumb buttons, site switcher, and back button have minimum touch targets of 32px height.
3. **Typography**:
   - All text tokens strictly use `--font-xs` through `--font-2xl`. Zero sub-12px styles.
