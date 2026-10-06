---
phase: 19
slug: critical-layout-status-fixes
status: approved
shadcn_initialized: false
preset: none
created: 2026-10-06
reviewed_at: 2026-10-06
---

# Phase 19 — UI Design Contract: Critical Layout & Status Fixes

> Visual and interaction design contract for responsive layout stabilization below 1100px and authoritative API connection telemetry status handling across the shell and operational views.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none |
| Preset | not applicable |
| Component library | none (custom vanilla CSS + React 19) |
| Icon library | lucide-react (v1.22+) |
| Font | 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif |

---

## Spacing Scale

Declared values (strictly multiples of 4):

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Icon gaps, status dot diameter, inline badge gaps (`gap: 4px`), border radii accents |
| sm | 8px | Status badge padding (`padding: 4px 8px`), chip spacing, button internal gaps |
| md | 16px | Card padding, header action bar gap, compact content padding at 1100px (`1rem = 16px`) |
| lg | 24px | Default content body padding (`1.5rem = 24px`), section breaks, table card margins |
| xl | 32px | Layout gutters, major component spacing, compact header heights |
| 2xl | 48px | Empty state vertical container padding, modal vertical rhythm |
| 3xl | 64px | Page boundary spacing |

Exceptions: none. (Sidebar collapsed width 72px is exactly $4 \times 18$).

---

## Typography

Constrained type scale declaring exactly 4 sizes and exactly 2 weights:

| Role | Size | Weight | Line Height | Usage |
|------|------|--------|-------------|-------|
| Body | 14px | 400 | 1.5 | General descriptions, banner notices, tooltip text, table cell values |
| Label | 12px | 600 | 1.3 | Status badges (`LIVE`, `STALE`, `OFFLINE`), table column headers, metadata chips |
| Heading | 18px | 600 | 1.2 | Card titles, view subheadings, banner alert titles |
| Display | 24px | 600 | 1.2 | Operations Center header title, major status counters |

Weights declared: 400 (Regular), 600 (Semibold).  
Line heights: 1.5 for body readability, 1.2–1.3 for headings, labels, and badges.

---

## Color

60/30/10 Split and Semantic State Palette:

| Role | Dark Theme | Light Theme | Usage |
|------|------------|-------------|-------|
| Dominant (60%) | `#0a0e17` | `#f8fafc` | Viewport canvas background, main shell container |
| Secondary (30%) | `#111827` | `#ffffff` | Content cards, sidebar rail, top header, status panels |
| Accent (10%) | `#3b82f6` | `#2563eb` | Reserved for specific elements only (see below) |
| Live / Nominal | `#10b981` | `#059669` | `Live` status badge, pulsing green dot, healthy telemetry indicators |
| Stale / Warning | `#f59e0b` | `#d97706` | `Stale` status badge, amber dot, Mock Data pill, offline warning banner border |
| Offline / Error | `#ef4444` | `#dc2626` | `Offline` status badge, red dot, connection error badge, failed poll indicator |
| Text Tertiary | `#94a3b8` | `#64748b` | Muted metadata, last sync timestamps, breadcrumb separators |

**Accent (10%) Reserved For:**
1. Active navigation item indicator and breadcrumb current view highlight
2. Manual "Reconnect API" button hover state and active spinning refresh icon
3. Focus-visible outline rings on interactive controls (`outline: 2px solid var(--accent-blue)`)
4. Progress bar fill on polling retry timer countdown

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Primary CTA | `Reconnect API` (manual retry button in header and sidebar status row) |
| Secondary CTA | `Dismiss Notice` (action button to close the offline mock data banner) |
| Live Status Badge | `Live` with tooltip: `API Connected • Real-time telemetry synchronized` |
| Stale Status Badge | `Stale` with tooltip: `Sync Degraded • Last successful response {relative_time}. Retrying in {N}s...` |
| Offline Status Badge | `Offline` with tooltip: `Backend Unreachable • Connection failed. Operating on simulated seed data.` |
| Mock Data Pill | `Mock / Seed Data` with tooltip: `Simulated controller dataset active. Connect backend at localhost:8000 for live data.` |
| Empty State Heading | `Zero Active Network Alerts` |
| Empty State Body | `All monitored Cisco DNA Center devices report nominal health with zero open anomalies. Polling engine continues background checks.` |
| Connection Error State | `Backend API Unreachable at localhost:8000. Verify the FastAPI server is active with 'python start_dashboard.py' or check network logs.` |
| Destructive Confirmation | None (no destructive actions in this phase — all telemetry and reconnect actions are idempotent and read-only) |

---

## Visual Hierarchy & Component Contracts

### 1. Primary Screen Focal Point
The **Header Status & Telemetry Cluster** in the top navigation bar is the primary visual anchor:
- **Connection Badge:** Pill element displaying status dot + label:
  - `Live`: Background `#10b9811a`, border `#10b9814d`, text `#10b981`, with pulsing dot (`animation: pulse-dot 1.5s infinite`).
  - `Stale`: Background `#f59e0b1a`, border `#f59e0b4d`, text `#f59e0b`, with solid amber dot.
  - `Offline`: Background `#ef44441a`, border `#ef44444d`, text `#ef4444`, with solid red dot.
- **Reconnect Trigger:** Embedded circular button beside the status badge with `<RefreshCw size={13} />` icon, showing hover tooltip `Test API connection now`.
- **Mock Data Demarcation Chip:** When offline/stale, renders `[Mock / Seed Data]` chip in amber tint directly adjacent to the status badge.

### 2. Dismissible Offline Info Banner
When `connectionStatus !== 'connected'`, render a clean dismissible notification at the top of `.content-body`:
- **Icon:** `<AlertTriangle size={16} color="var(--accent-amber)" />`
- **Headline (14px / 600):** `Operating in Demo / Offline Mode`
- **Body Text (14px / 400):** `Displaying simulated test telemetry. Real-time Cisco DNA Center updates will resume automatically once backend connection is restored.`
- **Action Group:**
  - `<button className="reconnect-banner-btn">Reconnect API</button>`
  - `<button className="dismiss-banner-btn" aria-label="Dismiss Notice"><X size={14} /></button>`

### 3. Responsive 1100px Layout Contract
- **Sidebar Auto-Collapse:**
  - At viewport width $\le 1100\text{px}$, the sidebar transitions to the 72px icon rail mode (`width: 72px`), giving immediate horizontal breathing room to operational dashboards.
  - The manual toggle button remains functional, allowing operators to expand the sidebar over the content or collapse it at will.
- **Content Area Flexbox Boundary:**
  - `.content-area`: `flex: 1`, `min-width: 0`, `max-width: 100%`, `box-sizing: border-box`.
  - Margin offset strictly tracks sidebar state: `margin-left: 260px` (expanded) or `margin-left: 72px` (collapsed).
  - Eliminates all `calc(100vw - ...)` rigid constraints that caused collapse below 1100px.
- **Grid & Chart Reflow (`@media (max-width: 1100px)`):**
  - Content header padding reduces to `1rem 1.25rem` (`16px 20px`).
  - `.charts-grid-3`: Reflows to single or 2-column layout to prevent chart legend and SVG canvas clipping.
  - `.kpi-grid`: Maintains 2-column minimum with tightened gutters (`12px`).
- **Table Card Containment:**
  - All `.table-card` elements specify `min-width: 0` and `overflow: hidden`.
  - Table wrappers specify `overflow-x: auto` with custom visible scrollbars, guaranteeing that 1100px–1410px wide tables never trigger window-level horizontal scrollbars.

### 4. SRE Drawer Provenance Alignment
- When backend is offline (`connectionStatus === 'offline'`):
  - Telemetry tab displays `Simulated Device Profile` banner with amber tint.
  - "Poll DNAC" action button is disabled with tooltip: `Backend API offline • Live controller polling unavailable`.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none | not required |
| third-party | none | not required |

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS

**Approval:** approved 2026-10-06
