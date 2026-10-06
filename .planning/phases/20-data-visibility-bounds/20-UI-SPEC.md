---
phase: 20
slug: data-visibility-bounds
status: approved
shadcn_initialized: false
preset: none
created: 2026-10-06
reviewed_at: 2026-10-06
---

# Phase 20 — UI Design Contract: Data Visibility & Bounds

> Visual and interaction design contract for viewport bounding, topology canvas bounds, high-contrast table scrollbars, horizontal overflow edge masks, and vertical list capping with item counters across the Cisco DNA Center Ops Center dashboard.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (Vanilla CSS custom design tokens) |
| Preset | not applicable |
| Component library | none (custom React 19 components) |
| Icon library | lucide-react (`Maximize2`, `Minimize2`, `ZoomIn`, `ZoomOut`, `RotateCcw`, `ChevronDown`, `ChevronUp`, `Filter`, `Layers`) |
| Font | Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif |
| Monospace Font | ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace |

---

## Spacing Scale

Declared values (must be multiples of 4):

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Icon gaps, chip inline padding, badge border offsets |
| sm | 8px | Scrollbar thickness (8px width/height), thumb border-radius (6px), compact chip spacing |
| md | 16px | Card padding, toolbar margins, floating toast offsets |
| lg | 24px | Section padding, modal margins, topology lane gaps |
| xl | 32px | Major layout gaps, full-screen toolbar margins |
| 2xl | 48px | Primary view section breaks |
| 3xl | 64px | Page-level boundary padding |

**Exceptions:**
- `28px`: Horizontal table edge gradient mask width (`::before` / `::after` overlay). *Justification:* 28px provides an optimal non-intrusive gradient falloff to cue hidden off-screen columns without obscuring data in boundary columns.
- `560px` to `780px`: Topology canvas container height clamping (`clamp(560px, calc(100vh - 280px), 780px)`). *Justification:* Maintains proportional viewport responsiveness across both compact laptops and 4K displays while preventing window overflow.
- `480px`: Default vertical table max-height limit (`max-height: 480px`). *Justification:* Fits comfortably within standard viewports alongside page KPI headers and navigation controls.

---

## Typography

Constrained to exactly 4 sizes and 2 weights to maintain crisp visual hierarchy:

| Role | Size | Weight | Line Height | Usage |
|------|------|--------|-------------|-------|
| Display | 20px (1.25rem) | 600 (Semibold) | 1.25 (25px) | View titles, Fullscreen modal header |
| Heading | 16px (1.0rem) | 600 (Semibold) | 1.35 (21.6px) | Table card headers, Topology section banners, Drawer headings |
| Body | 14px (0.875rem) | 400 (Regular) | 1.50 (21px) | Table row cells, Toast instructions, Drawer alert descriptions |
| Label | 12px (0.75rem) | 600 (Semibold) | 1.20 (14.4px) | Counter chips ("Showing 5 of 12"), Toolbar buttons, Sticky column headers |

---

## Color & 60/30/10 Split

| Role | Value (Dark Theme) | Value (Light Theme) | Usage |
|------|--------------------|---------------------|-------|
| Dominant (60%) | `#0b1120` (`--bg-primary`) | `#f8fafc` (`--bg-primary`) | Main page canvas, background viewport surfaces |
| Secondary (30%) | `#151e32` (`--card-bg`, `--bg-secondary`) | `#ffffff` (`--card-bg`, `--bg-secondary`) | Card containers, sticky table headers, drawer backgrounds, sunken scrollbar tracks |
| Accent (10%) | `#3b82f6` (`--accent-blue`) | `#2563eb` (`--accent-blue`) | Reserved strictly for items listed below |
| Destructive | `#ef4444` (`--accent-red`) | `#dc2626` (`--accent-red`) | Critical alert severity badges and severed topology link warnings |

**Accent Reserved For (Explicit List — never "all interactive elements"):**
1. Active Fullscreen canvas toggle button state (`.noc-graph-control-btn.active`).
2. Active filter indicator dot inside table counter chips (`.table-counter-chip.has-filter`).
3. High-contrast slate scrollbar thumb hover highlight (`rgba(148, 163, 184, 0.75)` dark / `rgba(71, 85, 105, 0.70)` light).
4. Floating wheel-zoom instruction toast accent badge ("Ctrl + scroll").

**Scrollbar Channel & Thumb Color Contract:**
- **Scrollbar Thumb:**
  - Dark Mode: `rgba(148, 163, 184, 0.45)` (hover: `rgba(148, 163, 184, 0.75)`).
  - Light Mode: `rgba(100, 116, 139, 0.40)` (hover: `rgba(71, 85, 105, 0.70)`).
  - Contrast Ratio: Meets WCAG 2.1 AA 3:1 non-text contrast against card background.
- **Sunken Track:**
  - Dark Mode: `rgba(255, 255, 255, 0.04)`.
  - Light Mode: `rgba(0, 0, 0, 0.05)`.
- **Dimensions:** Width `8px`, Height `8px`, Border radius `6px`.

---

## Visuals & Component Contracts

### 1. Topology Canvas Bounding & Scroll Hijacking (`UI-03`)

- **Primary Visual Focal Point:** The 3-tier SVG Topology Graph (Core, Distribution, Campus) within the Network Operations view.
- **Scroll Guard:**
  - Mouse wheel over `.noc-topology-graph-container` without modifier keys (`Ctrl` / `Cmd`) passes through to allow natural page scrolling.
  - When wheel event fires without modifier keys, a floating toast pill appears centered at the bottom of the canvas:
    - Copy: *"Use Ctrl + scroll to zoom"*
    - Animation: `fadeIn 0.2s cubic-bezier(0.16, 1, 0.3, 1)`, auto-dismisses after 2.0s of inactivity.
    - Style: Background `rgba(15, 23, 42, 0.85)`, backdrop blur `12px`, border `1px solid var(--card-border)`, color `var(--text-primary)`, font size `12px` (Label).
- **Container Height & Bounding:**
  - Dynamic height: `height: clamp(560px, calc(100vh - 280px), 780px)`.
  - Container clips content: `overflow: hidden; position: relative`.
- **Soft-Boundary Pan Clamping:**
  - Pointer panning clamps `transform.x` and `transform.y` to ensure that at least 25% of the graph diagram bounding box remains visible within the canvas viewport at all times.
- **Fullscreen / Expanded Mode:**
  - Toolbar Toggle Button: `<button className="noc-graph-control-btn" aria-label="Toggle Fullscreen View" title="Toggle Fullscreen View (Esc)">` with `<Maximize2 size={13} />` (normal) or `<Minimize2 size={13} />` (fullscreen).
  - Fullscreen Styles: When active, `.noc-topology-graph-container.fullscreen` has `position: fixed; inset: 0; width: 100vw; height: 100vh; z-index: 1000; border-radius: 0;`.
  - Escape Key: Pressing `Escape` exits fullscreen mode back to inline bounded view.

---

### 2. High-Contrast Table Scrollbars (`UI-04`)

- **Scope:** Applied across all dense tabular surfaces:
  1. Detailed Traceability Matrix (`.data-table.resizable-table`)
  2. Device Ranking Table (`.rank-table`)
  3. SRE High-Density Table (`.noc-sre-table`)
  4. Regional Site Matrix (`.noc-matrix-table`)
  5. Alert Patterns Table (`.patterns-table`)
  6. SRE Details Drawer Body (`.detail-panel-body`)
- **CSS Rule Implementation:**
  ```css
  .table-scroll-container,
  .data-table-scroll-wrap,
  .table-scroll-wrapper {
    scrollbar-width: thin;
    scrollbar-color: rgba(148, 163, 184, 0.45) rgba(255, 255, 255, 0.04);
  }
  .table-scroll-container::-webkit-scrollbar,
  .data-table-scroll-wrap::-webkit-scrollbar,
  .table-scroll-wrapper::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }
  .table-scroll-container::-webkit-scrollbar-track,
  .data-table-scroll-wrap::-webkit-scrollbar-track,
  .table-scroll-wrapper::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.04);
    border-radius: 6px;
  }
  .table-scroll-container::-webkit-scrollbar-thumb,
  .data-table-scroll-wrap::-webkit-scrollbar-thumb,
  .table-scroll-wrapper::-webkit-scrollbar-thumb {
    background: rgba(148, 163, 184, 0.45);
    border-radius: 6px;
    transition: background 0.2s ease;
  }
  .table-scroll-container::-webkit-scrollbar-thumb:hover,
  .data-table-scroll-wrap::-webkit-scrollbar-thumb:hover,
  .table-scroll-wrapper::-webkit-scrollbar-thumb:hover {
    background: rgba(148, 163, 184, 0.75);
  }
  [data-theme="light"] .table-scroll-container,
  [data-theme="light"] .data-table-scroll-wrap,
  [data-theme="light"] .table-scroll-wrapper {
    scrollbar-color: rgba(100, 116, 139, 0.40) rgba(0, 0, 0, 0.05);
  }
  [data-theme="light"] .table-scroll-container::-webkit-scrollbar-track,
  [data-theme="light"] .data-table-scroll-wrap::-webkit-scrollbar-track,
  [data-theme="light"] .table-scroll-wrapper::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.05);
  }
  [data-theme="light"] .table-scroll-container::-webkit-scrollbar-thumb,
  [data-theme="light"] .data-table-scroll-wrap::-webkit-scrollbar-thumb,
  [data-theme="light"] .table-scroll-wrapper::-webkit-scrollbar-thumb {
    background: rgba(100, 116, 139, 0.40);
  }
  [data-theme="light"] .table-scroll-container::-webkit-scrollbar-thumb:hover,
  [data-theme="light"] .data-table-scroll-wrap::-webkit-scrollbar-thumb:hover,
  [data-theme="light"] .table-scroll-wrapper::-webkit-scrollbar-thumb:hover {
    background: rgba(71, 85, 105, 0.70);
  }
  ```

---

### 3. Horizontal Table Edge Gradient Masks (`UI-04`)

- **Component:** `<TableScrollWrapper>` or CSS wrapper `.table-scroll-wrapper` encapsulating wide tables.
- **Overlay Architecture:**
  - Edge masks are rendered via pseudo-elements on the wrapper (`::before` for left edge, `::after` for right edge) or overlay indicator divs.
  - Position: `position: absolute; top: 0; bottom: 8px; width: 28px; pointer-events: none; z-index: 4;`.
  - Bottom offset of `8px` ensures the horizontal scrollbar track remains unoccluded and directly clickable.
  - Left Gradient: `background: linear-gradient(to right, var(--card-bg), transparent)`.
  - Right Gradient: `background: linear-gradient(to left, var(--card-bg), transparent)`.
- **Dynamic Scroll-State Fade:**
  - A scroll listener tracks `scrollLeft` and `scrollWidth - clientWidth`.
  - Toggles classes `has-overflow-left` and `has-overflow-right`.
  - Transitions: `transition: opacity 0.2s ease`. When scrolled to the left limit, left mask has `opacity: 0`. When scrolled to the right limit, right mask has `opacity: 0`.

---

### 4. Vertical List Capping & Counters (`UI-04`)

- **Header Item Counter Chips:**
  - Displayed in card header next to table title: `<span className="table-counter-chip">Showing {visible} of {total} {noun}</span>`
  - Examples:
    - `"Showing 10 of 48 alerts"`
    - `"Showing 10 of 24 devices"`
    - `"Showing 5 of 18 alerts"` (in SRE drawer)
  - When filtering is active, a subtle blue dot indicator renders: `<span className="filter-active-dot" title="Filtered results" />`.
- **Sticky Table Headers:**
  - `position: sticky; top: 0; z-index: 5; background: var(--bg-secondary); backdrop-filter: blur(8px);`
  - Prevents column labels from disappearing during vertical inspection.
- **Vertical Capping & Toggle Controls:**
  - Dense vertical tables default to `max-height: 480px` (or 10 rows).
  - Progressive disclosure control button rendered in table footer when `total > 10`:
    - Collapsed Copy: `"Show all {total} rows"` with `<ChevronDown size={14} />`
    - Expanded Copy: `"Show 10 rows"` with `<ChevronUp size={14} />`
- **SRE Details Drawer Alert Capping:**
  - Active alerts list within the SRE Details Drawer capped at 5 items by default.
  - Progressive disclosure toggle button:
    - Collapsed Copy: `"Show {remaining} more alerts"` with `<ChevronDown size={14} />`
    - Expanded Copy: `"Show fewer alerts"` with `<ChevronUp size={14} />`
  - Drawer header counter chip: `"Showing {visible} of {total} alerts"`.

---

## Copywriting Contract

| Element | Copy | Condition / Context |
|---------|------|---------------------|
| Primary CTA (Topology) | "Expand Topology View" | Toolbar button to enter fullscreen canvas mode |
| Secondary CTA (Topology) | "Exit Fullscreen Canvas" | Toolbar button or toast action to exit fullscreen mode |
| Canvas Wheel Toast Hint | "Use Ctrl + scroll to zoom" | Appears when scrolling mouse wheel over canvas without Ctrl/Cmd |
| Table Header Counter (Unfiltered) | "Showing {visible} of {total} {items}" | e.g. "Showing 10 of 48 alerts", "Showing 10 of 25 devices" |
| Table Header Counter (Filtered) | "Showing {visible} of {total} filtered {items}" | Rendered when search query, tier, or status filter is active |
| Drawer Header Counter | "Showing {visible} of {total} active alerts" | SRE Details Drawer alert list counter chip |
| Table Vertical Expansion CTA (Collapsed) | "Show all {total} rows" | Bottom of capped table when rows exceed 10 |
| Table Vertical Expansion CTA (Expanded) | "Show 10 rows" | Bottom of table when expanded |
| Drawer Alert Expansion CTA (Collapsed) | "Show {count} more alerts" | Bottom of drawer alerts list when alerts exceed 5 |
| Drawer Alert Expansion CTA (Expanded) | "Show fewer alerts" | Bottom of drawer alerts list when expanded |
| Empty State Heading | "No matching devices found" | When topology or table filters return 0 rows |
| Empty State Body | "No network devices match the active search or tier filters. Clear your filters to view all devices." | Body text accompanying empty state with actionable guidance |
| Error State Heading | "Topology diagram unavailable" | When telemetry data cannot be plotted |
| Error State Body | "Unable to render network topology diagram. Check telemetry service status or click 'Reload Topology Data'." | Problem explanation plus concrete recovery step |
| Destructive Confirmation | Not applicable | Read-only monitoring views; no destructive actions exist in this phase |

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| none (pure custom CSS & React 19) | none | not applicable — no third-party registries used |

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS

**Approval:** Approved 2026-10-06
