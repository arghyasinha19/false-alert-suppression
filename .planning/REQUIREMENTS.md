# Requirements: False Alert Suppression Pipeline

**Defined:** 2026-10-05  
**Milestone:** v1.7 NOC Details Drawer Scrollbar & Usability Polish  
**Core Value:** Accurately identify false or transient network alerts to prevent unnecessary ServiceNow ticket creation and reduce operational noise without missing genuine network degradation.

## Milestone v1.7 Requirements: NOC Details Drawer Scrollbar & Usability Polish

### Drawer Scrollbar Accessibility & Styling (DRAWER-STYLE)
- [ ] **DRAWER-01**: Detail drawer body features dedicated, visible, theme-aware custom scrollbar styling in both dark and light modes, eliminating invisible/transparent scrollbars so users always see scroll position and affordance.

### Drawer Flex Layout Architecture (DRAWER-LAYOUT)
- [ ] **DRAWER-02**: Detail drawer flex layout cleanly anchors the header and tab navigation at the top, pins the sticky SRE action bar at the bottom, and isolates scrolling strictly to `.detail-panel-body` (`flex: 1; overflow-y: auto; min-height: 0;`), preventing full-panel jitter.

### Cross-Tab Viewport & Scrolling Verification (DRAWER-TABS)
- [ ] **DRAWER-03**: All 4 drawer tabs (Alert Triage multi-agent timeline, Assurance Telemetry vitals grid, Device Inventory hardware table, and Raw Payloads JSON viewer) support smooth, unclipped vertical scrolling across varying viewport heights.

## Future Requirements

- Real-time WebSockets streaming updates for telemetry metrics instead of polling.
- Multi-tenancy support for partitioned customer network views.
- Dynamic interface flap timeline graph per port.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Redesigning the entire dashboard layout | Only the device details drawer panel and its scrollable content areas are in scope. |
| Altering backend API endpoints | The bug is purely client-side CSS/layout styling and flex container sizing. |
| Changing multi-agent timeline logic | Timeline steps and metrics render unchanged within the scrollable body. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DRAWER-01 | Phase 16 | Pending |
| DRAWER-02 | Phase 16 | Pending |
| DRAWER-03 | Phase 16 | Pending |

**Coverage:**
- v1.7 requirements: 3 total
- Mapped to phases: 3 (100%)
- Unmapped: 0 ✓

---
*Requirements defined: 2026-10-05*  
*Last updated: 2026-10-05 after Milestone v1.7 initialization*
