# Phase 19: Critical Layout & Status Fixes - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-06  
**Phase:** 19-Critical Layout & Status Fixes  
**Areas discussed:** Responsive Breakpoint & Container Scaling (<1100px), Connection Status & Failure Transitions, Mock vs Live Telemetry Demarcation, Polling Resiliency & Manual Reconnect Flow  

---

## Responsive Breakpoint & Container Scaling (<1100px)

### Question 1: Sidebar behavior below 1100px
| Option | Description | Selected |
|--------|-------------|:--------:|
| (Recommended) Auto-collapse sidebar to 72px icon rail below 1100px, keeping manual toggle available | Immediate horizontal room for content without hiding navigation icons | ✓ |
| Keep sidebar manual-toggle only above 900px, but compact content padding (1rem) and card spacing at 1100px | Keeps full sidebar until mobile/tablet boundary | |
| Auto-collapse to 72px icon rail only at 900px, allowing the operator full control between 900px-1100px | Defer collapse until 900px | |

**User's choice:** Auto-collapse sidebar to 72px icon rail below 1100px, keeping manual toggle available.  

### Question 2: Container bounds and overflow constraints
| Option | Description | Selected |
|--------|-------------|:--------:|
| (Recommended) Enforce flex sizing with 'min-width: 0', 'max-width: 100%', letting flexbox fluidly shrink while isolating horizontal overflow to individual cards/tables | Modern CSS flex container best practices | ✓ |
| Keep 'width: 100%' and rely on global 'overflow-x: hidden' on the app shell/body | Clips global window | |
| You decide — apply standard modern flexbox layout constraints to prevent viewport overflow | Agent discretion | |

**User's choice:** Enforce flex sizing with 'min-width: 0', 'max-width: 100%', letting flexbox fluidly shrink while isolating horizontal overflow to individual cards/tables.  

### Question 3: Dedicated 1100px media query
| Option | Description | Selected |
|--------|-------------|:--------:|
| (Recommended) Introduce an explicit @media (max-width: 1100px) block that compacts header padding (1rem 1.25rem), stacks 3-column charts to single/double columns, and tightens card gutters | Clean dedicated reflow tier | ✓ |
| Rely on the existing 1200px and 900px breakpoints, keeping CSS rules minimal without adding a 1100px-specific media query | Coarser responsive steps | |
| You decide — optimize grid columns and card padding dynamically to prevent element clipping | Agent discretion | |

**User's choice:** Introduce an explicit @media (max-width: 1100px) block that compacts header padding (1rem 1.25rem), stacks 3-column charts to single/double columns, and tightens card gutters.  

### Question 4: Wide data table containment
| Option | Description | Selected |
|--------|-------------|:--------:|
| (Recommended) Ensure all .table-card containers have 'min-width: 0' and 'overflow: hidden', confining horizontal scrollbars strictly inside table wrappers without leaking to window scroll | Complete isolation of horizontal scroll | ✓ |
| Add a subtle horizontal scroll indicator badge/tooltip ('Scroll table horizontally ↔') on cards when tables exceed container width | Visual prompt | |
| You decide — encapsulate table wrappers cleanly with zero window-level horizontal scroll leak | Agent discretion | |

**User's choice:** Ensure all .table-card containers have 'min-width: 0' and 'overflow: hidden', confining horizontal scrollbars strictly inside table wrappers without leaking to window scroll.  

---

## Connection Status & Failure Transitions

### Question 1: Connection status state machine
| Option | Description | Selected |
|--------|-------------|:--------:|
| (Recommended) Tri-state model: 'Live' (green pulse), 'Stale' (amber dot, 1–2 poll failures after being live), and 'Offline' (red dot, on initial failure or 3+ failures) | Nuanced distinction between transient blips and complete outage | ✓ |
| Dual-state model: 'Live' (green) when healthy, 'Offline' (red) immediately upon any fetch failure | Binary flip | |
| Header shows 'Live' vs 'Stale', while sidebar explicitly shows 'API Connected' vs 'Offline' | Split semantics | |

**User's choice:** Tri-state model: 'Live' (green pulse), 'Stale' (amber dot, 1–2 poll failures after being live), and 'Offline' (red dot, on initial failure or 3+ failures).  

### Question 2: Refresh timestamp behavior on failure
| Option | Description | Selected |
|--------|-------------|:--------:|
| (Recommended) Freeze lastSuccessfulSync to the time of the last successful response; display 'Last sync: Xm ago (Failed)' in sidebar and refresh bar | Eliminates false positive 'Updated 2s ago' indicators | ✓ |
| Clear the timestamp on failure and display 'Sync Paused • Offline' until reconnect | Hides last sync point | |
| Keep attempt timestamp updated but show an explicit error indicator '(Last attempt failed)' | Shows attempt time | |

**User's choice:** Freeze lastSuccessfulSync to the time of the last successful response; display 'Last sync: Xm ago (Failed)' in sidebar and refresh bar.  

### Question 3: Status propagation to views
| Option | Description | Selected |
|--------|-------------|:--------:|
| (Recommended) Pass connectionStatus and lastSync as props to views, updating the NOC refresh bar dot and label to match (Live / Stale / Offline) | Direct prop flow matching active view structure | ✓ |
| Use a lightweight React Context (ConnectionStatusContext) so all views and drawer components access live status uniformly | Context provider pattern | |
| You decide — ensure all child views mirror the parent connection status cleanly | Agent discretion | |

**User's choice:** Pass connectionStatus and lastSync as props to views, updating the NOC refresh bar dot and label to match (Live / Stale / Offline).  

### Question 4: API response validation
| Option | Description | Selected |
|--------|-------------|:--------:|
| (Recommended) Strict payload validation: Require Array.isArray(alertsRes?.alerts) and devices; if missing or malformed, treat as error, avoid false Live status | Prevents corrupted/empty JSON from masquerading as healthy | ✓ |
| Lenient check: If HTTP 200 and JSON parses, mark as Live and accept whatever keys exist | Permissive parsing | |
| You decide — validate payloads properly so empty or corrupted JSON does not produce false Live indicators | Agent discretion | |

**User's choice:** Strict payload validation: Require Array.isArray(alertsRes?.alerts) and devices; if missing or malformed, treat as error, avoid false Live status.  

---

## Mock vs Live Telemetry Demarcation

### Question 1: Mock data indicator prominence
| Option | Description | Selected |
|--------|-------------|:--------:|
| (Recommended) Dedicated amber badge in the header ('Mock / Seed Data') plus a subtle, dismissible info banner across the top of the content area | Clear demarcation without blocking operations | ✓ |
| Persistent prominent top banner across the content body ('Offline Mode — Displaying simulated test data') | Permanent large banner | |
| Header pill only — enhance the existing text into a clear high-contrast amber chip ('MOCK DATA') | Header only | |

**User's choice:** Dedicated amber badge in the header ('Mock / Seed Data') plus a subtle, dismissible info banner across the top of the content area.  

### Question 2: SRE Drawer provenance alignment
| Option | Description | Selected |
|--------|-------------|:--------:|
| (Recommended) Align drawer provenance: display 'Simulated Profile' banner and disable 'Poll DNAC' with tooltip 'API offline' when backend is unreachable | Prevents clicking buttons that will immediately fail | ✓ |
| Keep 'Poll DNAC' clickable, attempting the call and displaying the drawer-specific network error banner if it fails | Reactive error on click | |
| You decide — ensure drawer provenance seamlessly reflects global backend availability | Agent discretion | |

**User's choice:** Align drawer provenance: display 'Simulated Profile' banner and disable 'Poll DNAC' with tooltip 'API offline' when backend is unreachable.  

### Question 3: Dataset hot-swap handling
| Option | Description | Selected |
|--------|-------------|:--------:|
| (Recommended) Seamless hot-swap: update datasets dynamically, re-match selectedDevice by name (or safely close drawer if missing), preserve active filters | Smooth operator experience | ✓ |
| Reset device selection and close drawer on data source change to prevent orphaned state, maintaining filter chips | Complete drawer reset | |
| Show a subtle toast banner ('Connected to live API — telemetry synced') and transition smoothly | Toast notification | |

**User's choice:** Seamless hot-swap: update datasets dynamically, re-match selectedDevice by name (or safely close drawer if missing), preserve active filters.  

### Question 4: Table rows & KPI cards styling
| Option | Description | Selected |
|--------|-------------|:--------:|
| (Recommended) Global header chip and dismissible banner provide sufficient demarcation; keep table rows and KPI cards clean and production-styled | Avoids visual noise in dense tables | ✓ |
| Append a subtle 'Demo' tag to simulated incident numbers and device cards in offline mode | Per-row watermark | |
| You decide — ensure data provenance is clear without cluttering dense operational tables | Agent discretion | |

**User's choice:** Global header chip and dismissible banner provide sufficient demarcation; keep table rows and KPI cards clean and production-styled.  

---

## Polling Resiliency & Manual Reconnect Flow

### Question 1: Polling backoff on failure
| Option | Description | Selected |
|--------|-------------|:--------:|
| (Recommended) Progressive backoff: Quick 10s retry on first failure, then back off to 60s on persistent failures to avoid network spam | Fast recovery for blips, quiet backoff for outages | ✓ |
| Maintain constant 30s interval indefinitely regardless of success or error | Fixed interval | |
| Pause auto-polling after 3 consecutive failures until the operator clicks 'Retry' | Requires user intervention | |

**User's choice:** Progressive backoff: Quick 10s retry on first failure, then back off to 60s on persistent failures to avoid network spam.  

### Question 2: Manual reconnect controls
| Option | Description | Selected |
|--------|-------------|:--------:|
| (Recommended) Provide a manual 'Retry / Reconnect' button in the header and sidebar status row, plus automatic reconnect on window focus | Immediate testing on demand and on tab switch | ✓ |
| Manual retry only via the existing view-level refresh controls (e.g. NOC bar) | View controls only | |
| Purely automatic background retries without additional buttons | No manual trigger | |

**User's choice:** Provide a manual 'Retry / Reconnect' button in the header and sidebar status row, plus automatic reconnect on window focus.  

### Question 3: Handling empty datasets ({ alerts: [], devices: [] })
| Option | Description | Selected |
|--------|-------------|:--------:|
| (Recommended) Treat empty arrays as valid Live state (green), rendering clean empty states ('0 active alerts — network nominal') without false error states | Correct network representation | ✓ |
| Flag empty arrays with an informational warning ('Connected • No alerts returned') | Warning on empty | |
| You decide — cleanly distinguish between a healthy zero-alert network and an offline/broken endpoint | Agent discretion | |

**User's choice:** Treat empty arrays as valid Live state (green), rendering clean empty states ('0 active alerts — network nominal') without false error states.  

### Question 4: Error diagnostics
| Option | Description | Selected |
|--------|-------------|:--------:|
| (Recommended) Hover tooltip / click popover on the badge showing endpoint URL, last attempt time, error reason, and retry countdown | Actionable debugging for SREs without cluttering UI | ✓ |
| Simple tooltip only ('Backend unreachable at localhost:8000') without technical error details | Minimal tooltip | |
| Console logging only, keeping the UI badges purely visual and minimal | DevTools only | |

**User's choice:** Hover tooltip / click popover on the badge showing endpoint URL, last attempt time, error reason, and retry countdown.  

---

## the agent's Discretion

- Exact CSS cubic-bezier curves for sidebar transitions.
- Micro-interaction styling for the reconnect spin icon.

## Deferred Ideas

- None — discussion stayed strictly within the phase scope.
