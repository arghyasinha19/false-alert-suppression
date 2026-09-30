# Requirements: False Alert Suppression Pipeline

**Defined:** 2026-09-30  
**Milestone:** v1.2 Custom Date & Time Range Filtering  
**Core Value:** Accurately identify false or transient network alerts to prevent unnecessary ServiceNow ticket creation and reduce operational noise without missing genuine network degradation.

## Milestone v1.2 Requirements: Custom Date & Time Range Filtering

- [x] **TIME-01**: User can select "Custom Range" from the time range filter dropdown and enter start and end date & time using datetime-local input pickers.
- [x] **TIME-02**: User can filter alerts by start-only (from start time to present), end-only (from beginning to end time), or bounded start-to-end interval, correctly handling epoch ms, epoch seconds, and ISO 8601 timestamps.
- [x] **TIME-03**: System dynamically recalculates all KPI metric cards (`Total Processed`, `Tickets Avoided`, `Suppressed`, `Auto-Resolving`, `Non-Auto-Resolving`, `Uncertain`), category charts, and the traceability matrix to strictly reflect alerts inside the custom window.
- [x] **TIME-04**: User can reset or clear custom date & time inputs with a single click, smoothly returning to preset ranges (`ALL`, `24H`, `7D`, `30D`).

## Future Requirements

- Saved custom date-time presets in browser local storage.
- Quick preset buttons for 6H, 12H, 14D, and quarter-to-date.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Server-side time partitioning or query rewriting | Alert stream is buffered in client memory / MongoDB collection; frontend scope filtering delivers instant sub-millisecond filtering. |
| Multi-timezone selector override | All comparisons normalize cleanly to UTC / browser local epoch time. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TIME-01 | Phase 3 | Complete ✓ |
| TIME-02 | Phase 3 | Complete ✓ |
| TIME-03 | Phase 3 | Complete ✓ |
| TIME-04 | Phase 3 | Complete ✓ |

**Coverage:**
- v1.2 requirements: 4 total
- Mapped to phases: 4
- Complete: 4 ✓
- Unmapped: 0 ✓

---
*Requirements defined: 2026-09-30*  
*Last updated: 2026-09-30 after Milestone v1.2 Phase 3 completion*
