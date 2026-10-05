# Phase 15: Frontend SRE Drawer Live Wire-Up - Context

**Gathered:** 2026-10-05  
**Status:** Ready for planning  

<domain>
## Phase Boundary

Phase 15 connects the slide-out SRE triage drawer in `dashboard/src/NetworkOperations.jsx` (and associated components/CSS) to the live backend endpoints created in Phase 14:
1. `GET /api/devices/{device_name}/telemetry` — powers the Assurance Telemetry and Device Inventory tabs with live hardware vitals and specs.
2. `POST /api/devices/{device_name}/live-poll` — powers the "Poll DNAC" action button in the sticky SRE Action Bar and drawer header.

This replaces procedural mock calculations and artificial `setTimeout` polling with real HTTP integration, reactive loading feedback, dynamic toast notifications, live/offline source badges, and honest null states.

No backend API changes in this phase (completed in Phase 14).  
No daemon startup or launcher changes in this phase (those belong to Phase 16).
</domain>

<decisions>
## Implementation Decisions

### Telemetry Fetch Timing & Loading States
- **D-01 (Fetch on drawer open):** When a device is selected (`openDevicePanel(device)`), immediately initiate `GET /api/devices/${encodeURIComponent(device.device_name)}/telemetry`.
- **D-02 (Seamless upgrade):** Display existing/cached device values immediately to avoid layout pop-in, showing a subtle pulsing loader dot, then seamlessly upgrade to live telemetry when the API response resolves.

### "Poll DNAC" Action & Fleet Synchronization
- **D-03 (Real HTTP call):** Replace `setTimeout` in `handlePollDNAC` with an HTTP `POST` to `/api/devices/${encodeURIComponent(selectedDevice.device_name)}/live-poll`.
- **D-04 (Fleet-wide refresh):** When `live-poll` succeeds, update the local drawer's telemetry state immediately AND invoke `onRefresh()` (the parent refresh callback) so background device tiles, health dots, active alert counts, and SRE tables update across all presentation modes (Executive Topology, SRE High-Density Table, Regional Site Matrix).
- **D-05 (Dynamic toast feedback):** Display toast notifications matching the actual response:
  - On `status === 'success'`: `addToast('DNAC Live Synchronized', `Synchronized ${data.alerts_updated} alerts and refreshed telemetry for ${selectedDevice.device_name}.`, 'success')`
  - On `status === 'warning'`: `addToast('DNAC Offline', `DNAC is currently unreachable. Displaying cached/offline state.`, 'warning')`
  - On network/HTTP error: `addToast('Poll Failed', `Unable to contact backend polling service.`, 'error')`

### Source Badge Placement & Visual Styling
- **D-06 (Dual placement):** Display provenance in two complementary locations:
  1. Header status pill: Small badge next to device title in the top drawer header (`● DNAC LIVE` in green, `⟳ CACHED` in amber, or `○ OFFLINE` in muted slate).
  2. Tab banner: Detailed provenance strip at the top of the Assurance Telemetry and Device Inventory tabs showing data source and formatted timestamp (`Live telemetry from Cisco DNA Center • Synced at HH:MM:SS` or `Offline cached record from MongoDB`).

### Offline / Missing Data Presentation
- **D-07 (Honest null state):** When telemetry vitals are null or unreachable (`source: 'offline'` with null metrics), render clean `" — "` / `"No Signal"` text and 0% muted gauge bars with an informational notice banner explaining DNAC is unreachable, preserving card layout without fabricating numbers.
- **D-08 (CSS tokens & responsiveness):** Adhere to existing dark/light CSS variables, ensuring all new badges, banners, and loading pulses seamlessly adapt to theme changes and mobile/desktop widths.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Frontend Components
- `dashboard/src/NetworkOperations.jsx` — Slide-out drawer, tab rendering (`telemetry`, `inventory`), and sticky SRE Action Bar (`handlePollDNAC`).
- `dashboard/src/NetworkOperations.css` — Styling for `.noc-telemetry-grid`, `.noc-inventory-card`, `.noc-drawer-action-bar`, and badges.

### Backend Endpoint Contracts (from Phase 14)
- `dashboard/api.py` — `GET /api/devices/{name}/telemetry` and `POST /api/devices/{name}/live-poll`.
- `dashboard/device_service.py` — Schema definition of `telemetry`, `device_info`, and `source` (`"dnac_live"`, `"cached_offline"`, `"offline"`).

### Requirements & Roadmap
- `.planning/REQUIREMENTS.md` — Requirements DNAC-05 and DNAC-06.
- `.planning/ROADMAP.md` — Phase 15 goals and success criteria.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `addToast(title, message, type)` in `NetworkOperations.jsx` — Floating animated toast feedback system.
- `pollingHealth` state in `NetworkOperations.jsx` — Boolean controlling the spinning icon on the Poll DNAC button.
- CSS classes: `.spin`, `.badge`, `.glass-card` for fluid animations and micro-interactions.

### Established Patterns
- Fetch pattern: `fetch(url).then(r => r.json()).catch(...)` with abort controller or unmounted checks.
- Date formatting: `formatTimestamp(ts)` helper for user-friendly date-time display.

### Integration Points
- `NetworkOperations.jsx`:
  - Hook `openDevicePanel` to trigger `fetchTelemetry(device.device_name)`.
  - Hook `handlePollDNAC` to trigger `POST /api/devices/{device_name}/live-poll`.
  - Replace procedural `getDeviceTelemetryVitals` calls in the drawer with state-driven telemetry object.

</code_context>

<specifics>
## Specific Ideas

- Provide a retry button in the offline notice banner inside the telemetry tab so SREs can re-attempt live polling directly from the tab.
- Format `uptime_seconds` into days/hours/minutes (e.g. `142 days, 6 hours`).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed strictly within the Phase 15 frontend wire-up domain.

</deferred>

---

*Phase: 15-frontend-sre-drawer-live-wire-up*  
*Context gathered: 2026-10-05*  
