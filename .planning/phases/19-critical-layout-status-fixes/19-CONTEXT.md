# Phase 19: Critical Layout & Status Fixes - Context

**Gathered:** 2026-10-06  
**Status:** Ready for planning  

<domain>
## Phase Boundary

Phase 19 delivers critical responsive layout fixes and authoritative API connection telemetry status handling:
1. **Responsive Flexbox Layout Below 1100px (UI-01):** Fix responsive collapse in `.content-area` by eliminating rigid viewport constraints, enforcing `min-width: 0` / flexbox scaling, auto-collapsing the sidebar to 72px rail mode below 1100px, and isolating wide tables/cards to prevent window-level horizontal overflow.
2. **Reliable Connection State & Offline Demarcation (UI-02):** Implement a tri-state connection status machine (`connected` / `stale` / `offline`), freeze refresh timestamps on failures, strictly validate API payload structures, synchronize status across the sidebar, header, and Network Operations refresh bar, and clearly demarcate mock/demo datasets from live controller telemetry.

</domain>

<decisions>
## Implementation Decisions

### Responsive Breakpoint & Container Scaling (<1100px)
- **D-01:** Auto-collapse sidebar to the 72px icon rail below 1100px viewport width while keeping manual user toggle available.
- **D-02:** Enforce flexbox sizing on `.content-area` with `min-width: 0` and `max-width: 100%`, allowing the container to fluidly shrink without shrinking to a sliver or overflowing the viewport.
- **D-03:** Introduce an explicit `@media (max-width: 1100px)` responsive block in `App.css` that compacts header padding (`1rem 1.25rem`), reflows 3-column charts (`.charts-grid-3`) cleanly, and tightens card gutters.
- **D-04:** Ensure all `.table-card` containers have `min-width: 0` and `overflow: hidden`, confining horizontal scrollbars strictly inside table wrappers without leaking to window scroll.

### Connection Status & Failure Transitions
- **D-05:** Implement a tri-state connection model:
  - `connected`: "Live" (green dot + pulse), active polling succeeding.
  - `stale`: "Stale" (amber dot), 1–2 background poll failures after having been live.
  - `offline`: "Offline" (red dot), initial connection failed or 3+ consecutive failures.
- **D-06:** Freeze `lastSuccessfulSync` to the timestamp of the last valid API response. Display "Last sync: Xm ago (Failed)" in sidebar and refresh indicators on error rather than showing false positive refresh times.
- **D-07:** Pass `connectionStatus` and `lastSync` as props to child views (`NetworkOperations`, `FalseAlertMetrics`), synchronizing sub-view indicators like `.noc-refresh-bar` so they accurately display Live / Stale / Offline.
- **D-08:** Enforce strict payload schema validation: require `Array.isArray(alertsRes?.alerts)` and `Array.isArray(devicesRes?.devices)`. If keys are missing or malformed, treat as error to avoid false Live status.

### Mock vs Live Telemetry Demarcation
- **D-09:** Render a dedicated amber chip in the header (`[Mock / Seed Data]`) plus a subtle, dismissible info banner across the top of the content area when operating on simulated/offline datasets.
- **D-10:** Align SRE Drawer data provenance: display a "Simulated Device Profile" banner and disable the "Poll DNAC" action button with tooltip "Backend API offline" when the backend is unreachable.
- **D-11:** Support seamless hot-swapping: dynamically update datasets upon connection, re-match `selectedDevice` by hostname (or safely close drawer if missing), and preserve active filter chips.
- **D-12:** Keep individual table rows and KPI cards clean and production-styled without adding noisy per-row demo watermarks, relying on global badges and banners for demarcation.

### Polling Resiliency & Manual Reconnect Flow
- **D-13:** Implement progressive retry backoff: quick 10s retry on first poll failure, scaling to 20s, and capping at 60s on persistent failures to avoid console and network spam.
- **D-14:** Provide manual "Retry / Reconnect" buttons in both the header and sidebar status row, and automatically trigger immediate reconnect checks when the window regains focus (`window.addEventListener('focus', ...)`).
- **D-15:** Treat valid responses with empty datasets (`{ alerts: [], devices: [] }`) as valid Live state (green), rendering clean empty states ("0 active alerts — network nominal") rather than false errors.
- **D-16:** Provide a diagnostic tooltip / popover on the Stale/Offline badge surfacing endpoint URL, last attempt time, error reason (e.g. connection refused vs HTTP 500), and retry countdown.

### the agent's Discretion
- Exact CSS cubic-bezier transition curves for sidebar collapse and banner dismissal.
- Micro-styling for retry spinner icon states.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Roadmap & Requirements
- `.planning/ROADMAP.md` §Phase 19 — Phase goal, requirements UI-01 & UI-02, and success criteria.
- `.planning/REQUIREMENTS.md` §Critical Layout & Status Fixes — UI-01 and UI-02 requirements.

### Core Shell & Layout
- `dashboard/src/App.jsx` — Primary shell, API polling loop, sidebar, breadcrumb header, and view router.
- `dashboard/src/App.css` — App shell flex layout, sidebar widths, content-area margin/flex rules, breakpoints, and live badge styles.

### Operational Views & Telemetry Components
- `dashboard/src/NetworkOperations.jsx` — NOC live refresh indicator bar, device fleet cards, topology view, and SRE drawer provenance banners.
- `dashboard/src/FalseAlertMetrics.jsx` — Alert metrics view, KPI cards, and Alert Trace Matrix table wrapper.
- `dashboard/src/AlertPatterns.jsx` — Pattern detail table and horizontal overflow container.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `sidebarCollapsed` state and `.sidebar.collapsed` / `.content-area.sidebar-collapsed` classes (`App.jsx`, `App.css`).
- `.live-badge` and `.sidebar-status-dot` styling primitives with pulsing keyframes (`App.css`).
- `.noc-refresh-bar` layout in `NetworkOperations.jsx` with seconds-ago calculation and progress bar.
- Provenance banner classes (`.noc-provenance-banner.live`, `.noc-provenance-banner.offline`) in `NetworkOperations.jsx` / `App.css`.

### Established Patterns
- Theme tokens in `dashboard/src/index.css` via CSS custom properties.
- LocalStorage persistence for user preferences (`sidebar_collapsed`, `app_theme`).
- Glassmorphic card styling (`.glass-card`, `.table-card`).

### Integration Points
- `dashboard/src/App.jsx`: Expand `apiConnected` into `connectionState: { status: 'connected' | 'stale' | 'offline', lastSuccessfulSync, lastAttempt, error, retryCount }`. Add window focus listener and backoff timer.
- `dashboard/src/App.css`: Modify `.content-area` flex rules (`min-width: 0`), add `@media (max-width: 1100px)` breakpoint block, style Stale/Offline states and mock banner.
- `dashboard/src/NetworkOperations.jsx`: Receive `connectionStatus` and `lastSuccessfulSync` as props, update `.noc-refresh-bar` to mirror real status, and handle offline drawer state.

</code_context>

<specifics>
## Specific Ideas

- Ensure fluid resizing: testing resizing from 1440px down to 1024px and 900px must not cause horizontal scrolling on the `body` or `.app-shell`.
- When backend is down, operators must clearly know whether they are looking at cached/mock data and see a countdown or manual button to test reconnect.

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope.

</deferred>

---

*Phase: 19-Critical Layout & Status Fixes*  
*Context gathered: 2026-10-06*
