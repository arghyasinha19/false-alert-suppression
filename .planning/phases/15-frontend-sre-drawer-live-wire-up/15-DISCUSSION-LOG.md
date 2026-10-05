# Phase 15: Frontend SRE Drawer Live Wire-Up - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-05  
**Phase:** 15-frontend-sre-drawer-live-wire-up  
**Areas discussed:** Telemetry Fetch Timing & Loading States, Poll DNAC Action & Fleet Sync, Source Badge Placement & Visual Styling, Offline / Missing Data Presentation  

---

## Telemetry Fetch Timing & Loading States

| Option | Description | Selected |
|--------|-------------|----------|
| Fetch immediately on drawer open | Display existing/cached values immediately with a subtle pulsing loader dot, then seamlessly upgrade when the live response resolves | ✓ |
| Lazy fetch on tab click | Only trigger API call when user clicks Assurance Telemetry or Device Inventory, showing skeleton loader | |
| Strict skeleton loading | Clear vitals on drawer open and show pulsing skeleton grid until API returns | |

**User's choice:** Fetch immediately on drawer open with seamless background upgrade.  
**Notes:** Prevents layout shift; cached numbers render immediately and upgrade to live data once fetched.

---

## Poll DNAC Action & Fleet Sync

| Option | Description | Selected |
|--------|-------------|----------|
| Full sync | Update drawer telemetry immediately AND trigger onRefresh() so main dashboard tiles, health dots, and alert counts update across all views | ✓ |
| Drawer-only sync | Update only the active drawer's telemetry and alerts, leaving background dashboard to periodic auto-refresh | |
| Prompted sync | Update drawer telemetry and display a 'Refresh Fleet' action button in the toast notification | |

**User's choice:** Full sync.  
**Notes:** Synchronously updates drawer telemetry and triggers `onRefresh()` to synchronize the fleet grid and tables.

---

## Source Badge Placement & Visual Styling

| Option | Description | Selected |
|--------|-------------|----------|
| Dual placement | Small status pill in drawer header next to device name + detailed badge with timestamp banner in Telemetry and Inventory tabs | ✓ |
| Tab-only placement | Display badge exclusively inside Assurance Telemetry and Device Inventory tab headers | |
| Header-only placement | Place badge once in top drawer header | |

**User's choice:** Dual placement.  
**Notes:** Quick provenance in drawer header + full synchronization details in tab content headers.

---

## Offline / Missing Data Presentation

| Option | Description | Selected |
|--------|-------------|----------|
| Honest null state | Render '—' / 'No Signal' with 0% muted gauge bars and an informational banner explaining DNAC is unreachable, keeping card layout intact | ✓ |
| Hybrid fallback | Display deterministic procedural numbers with explicit '(Estimated)' tag | |
| Empty state replacement | Replace entire telemetry card grid with dedicated 'DNAC Offline / No Data' notice card | |

**User's choice:** Honest null state.  
**Notes:** Avoids fabricating metrics; clearly indicates when live metrics are unavailable while keeping cards cleanly aligned.

---

## the agent's Discretion

- Choice of icons for provenance badges (Activity, CloudCheck, CloudOff).
- Duration of loading spinner and transition ease curves.

---

## Deferred Ideas

None — discussion stayed strictly within the Phase 15 frontend domain.
