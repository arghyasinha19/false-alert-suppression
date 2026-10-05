---
phase: 15
slug: frontend-sre-drawer-live-wire-up
status: approved
shadcn_initialized: false
preset: none
created: 2026-10-05
reviewed_at: 2026-10-05
---

# Phase 15 — UI Design Contract: Frontend SRE Drawer Live Wire-Up

> Visual and interaction design contract for wiring the slide-out SRE triage drawer in `NetworkOperations.jsx` to live Cisco DNA Center telemetry and live polling endpoints (`GET /api/devices/{name}/telemetry` and `POST /api/devices/{name}/live-poll`).

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
| xs | 4px | Icon gaps, status dot margins, inline badge padding (`0.15rem 0.45rem`) |
| sm | 8px | Compact element gaps, drawer tab gaps, toast text spacing, badge padding |
| md | 16px | Default element spacing, telemetry grid gap, inventory card padding, drawer action bar padding |
| lg | 24px | Section padding, drawer header horizontal padding, tab group margins |
| xl | 32px | Drawer panel margin offsets, modal spacing |
| 2xl | 48px | Empty state vertical container padding |
| 3xl | 64px | Maximum viewport edge padding |

Exceptions: none.

---

## Typography

Constrained type scale declaring exactly 4 sizes and exactly 2 weights:

| Role | Size | Weight | Line Height | Usage |
|------|------|--------|-------------|-------|
| Body | 14px | 400 | 1.5 | Drawer body text, alert descriptions, inventory spec values |
| Label | 12px | 600 | 1.3 | Telemetry card titles, spec labels, status badges, timestamp meta |
| Heading | 18px | 600 | 1.2 | Drawer header device title, tab titles, card subheadings |
| Display | 24px | 600 | 1.2 | Telemetry KPI numerical readouts (e.g., "24%", "46ms") |

Weights declared: 400 (Regular), 600 (Semibold).  
Line heights: 1.5 for body readability, 1.2-1.3 for dense headings/labels.

---

## Color

60/30/10 Split and Semantic State Palette:

| Role | Dark Theme | Light Theme | Usage |
|------|------------|-------------|-------|
| Dominant (60%) | `#0a0e17` | `#f0f2f5` | Main viewport canvas, drawer backdrop overlay |
| Secondary (30%) | `#111827` | `#ffffff` | Slide-out drawer container, telemetry cards, inventory panels, action bar |
| Accent (10%) | `#3b82f6` | `#2563eb` | Reserved for specific elements only (see below) |
| Destructive / Critical | `#ef4444` | `#dc2626` | Health critical status dot, high-severity alert badges, CPU overload gauge (>85%) |
| Warning / Degradation | `#f59e0b` | `#d97706` | Warning status dot, medium-severity badges, cached provenance pill |
| Healthy / Live | `#10b981` | `#059669` | Live DNAC provenance pill, healthy status dot, normal gauge meters |
| Offline / Neutral | `#64748b` | `#94a3b8` | Offline provenance pill, muted 0% gauge meters, null signal placeholder (`"—"`) |

**Accent (10%) Reserved For:**
1. `Poll DNAC` active spinner icon and button hover glow
2. Active drawer tab underline and active icon color (`.noc-drawer-tab-btn.active`)
3. System RAM percentage gauge meter fill bar
4. Informational toast accent border (`.noc-toast.info`)
5. Manual retry button in the offline telemetry banner

---

## Visual Hierarchy & Component Contracts

### 1. Primary Screen Focal Point
The slide-out SRE drawer header is the primary anchor:
- **Device Title:** 18px / 600 semibold with pulsating health status dot (8px diameter).
- **Header Provenance Pill:** Small pill badge directly beside the title displaying live status:
  - `● DNAC LIVE` (`#10b981` background tint, green text, subtle glow)
  - `⟳ CACHED` (`#f59e0b` background tint, amber text)
  - `○ OFFLINE` (`#64748b` background tint, slate text)
- **Top Actions:** Poll DNAC quick-refresh icon button (with `title="Poll Cisco DNA Center Assurance"`) and Close drawer button (`title="Close drawer"`).

### 2. Tab Provenance Banner
At the top of the **Assurance Telemetry** and **Device Inventory** tabs, render an information strip:
- **Live State:** Icon `<Activity size={13} />` with text: `Live telemetry from Cisco DNA Center • Synced at {HH:MM:SS}`
- **Cached State:** Icon `<Clock size={13} />` with text: `Cached telemetry from MongoDB • Synced {relative_time}`
- **Offline State:** Icon `<AlertTriangle size={13} />` with text: `DNAC Unreachable • Displaying offline baseline record` + inline `<button>` `Retry Poll`

### 3. Assurance Telemetry Cards (2x3 Grid)
Each card in `.noc-telemetry-grid` displays:
- **Title (12px / 600):** Icon + Metric name in uppercase letter-spaced font (`CPU UTILIZATION`, `SYSTEM RAM`, `PACKET DROPS & CRC`, `REACHABILITY & LATENCY`, `POE & POWER`, `OPERATING TEMP`).
- **KPI Value (24px / 600):** Display numerical value or honest null state (`"—"` or `"No Signal"`).
- **Gauge Bar:** 6px height with smooth 500ms CSS transition. If value is null, width is 0% with muted track.
- **Subtext (12px / 400):** Contextual plane information (e.g., `"Core Processing Plane"`, `"Dual Redundant (OK)"`).

### 4. SRE Sticky Action Bar
Pinned to drawer bottom with 16px padding and border-top:
- `Copy Incident`: Primary CTA (blue accent background `#3b82f6`, white text)
- `Poll DNAC`: Secondary CTA with `<RefreshCw size={13} />` (spins during active request)
- `Simulate Alert`: Testing tool with `<Zap size={13} />`
- `Export`: Diagnostic report downloader with `<Download size={13} />`

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Primary Action CTA | `Poll DNAC Assurance` (Button label: `Poll DNAC`) |
| Secondary Action CTA | `Copy Incident Summary` (Button label: `Copy Incident`) |
| Empty state heading | `No Telemetry Available` |
| Empty state body | `No historical vitals found for this device in the local cache. Click 'Poll DNAC' below to query the controller.` |
| Offline state heading | `Assurance Telemetry Offline` |
| Offline state body | `Cisco DNA Center is currently unreachable. Displaying cached records from MongoDB or re-attempt live polling.` |
| Error state copy | `Telemetry Synchronization Failed: Unable to contact the backend polling service at /api/devices/{name}/live-poll. Verify backend service health.` |
| Destructive confirmation | `None — Phase 15 introduces no destructive actions.` |

### Dynamic Toast Notification Copy

| Event Trigger | Toast Title | Toast Description | Variant |
|---------------|-------------|-------------------|---------|
| Live Poll Success | `DNAC Live Synchronized` | `Synchronized {N} alerts and refreshed telemetry for {device_name}.` | `success` |
| Live Poll Warning (Offline) | `DNAC Controller Unreachable` | `Cisco DNA Center Assurance returned offline status. Retaining cached telemetry.` | `warning` |
| Live Poll Network Error | `Assurance Polling Failed` | `Network error connecting to /api/devices/{device_name}/live-poll.` | `error` |
| Drawer Telemetry Refreshed | `Live Vitals Updated` | `Telemetry for {device_name} refreshed from live controller.` | `info` |

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none | not applicable |
| third-party | none | not applicable (vanilla CSS + local React components) |

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS — Specific, actionable CTAs (`Poll DNAC Assurance`, `Copy Incident Summary`), non-generic empty/error states, structured dynamic toasts.
- [x] Dimension 2 Visuals: PASS — Distinct focal point in drawer header, 2x3 telemetry KPI grid, dual-placement provenance indicators, honest null states, accessible icon titles.
- [x] Dimension 3 Color: PASS — 60/30/10 ratio declared with light/dark tokens, semantic status colors for live/cached/offline, accent strictly limited to 5 specific elements.
- [x] Dimension 4 Typography: PASS — Exactly 4 font sizes declared (12px, 14px, 18px, 24px) with exactly 2 weights (400, 600) and defined line heights (1.2, 1.3, 1.5).
- [x] Dimension 5 Spacing: PASS — Strictly multiples of 4 (4, 8, 16, 24, 32, 48, 64), zero exceptions.
- [x] Dimension 6 Registry Safety: PASS — No external component registries or third-party blocks required.

**Approval:** approved 2026-10-05
