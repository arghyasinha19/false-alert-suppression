# Requirements: False Alert Suppression Pipeline

**Defined:** 2026-10-06  
**Milestone:** v2.0 Multi-Site Hierarchical Topology & WAN Observability  
**Core Value:** Accurately identify false or transient network alerts to prevent unnecessary ServiceNow ticket creation and reduce operational noise without missing genuine network degradation.

## Milestone v2.0 Requirements: Multi-Site Hierarchical Topology & WAN Observability

### Multi-Site WAN Topology — Level 1 (SITE-WAN)
- [x] **SITE-01**: User can view an interactive Global Multi-Site WAN topology map displaying all registered physical locations/sites as interactive macro nodes interconnected by WAN links.
- [x] **SITE-02**: User can view site-level health rollup badges (`nominal`, `degraded`, `critical`), active alert counts, avoided ticket totals, and blast radius indicators on each macro site node.
- [x] **SITE-03**: User can view inter-site WAN connection links with live health status, latency, and animated packet/flow indicators between interconnected sites.

### Site-Specific LAN Topology & Drill-Down — Level 2 (SITE-LAN)
- [x] **SITE-04**: User can drill down into any site from the Global WAN map (via click or site-switcher selector) to view that site's local Core ↔ Distribution ↔ Access tier topology graph.
- [x] **SITE-05**: User can navigate between the Global WAN overview and local site views using responsive breadcrumbs (`Global WAN Interconnect > UK-LON (London)`) with single-click return to global.
- [x] **SITE-06**: User can filter devices within a site's LAN topology while preserving site boundaries and context.

### Cross-View Site Synchronization & Filtering (SITE-SYNC)
- [x] **SITE-07**: Selecting a site in the Regional Site Matrix automatically filters or transitions the Topology view to that site's LAN graph.
- [x] **SITE-08**: Filtering by location in the SRE Table or multi-dimensional filter bar synchronizes with the Topology view's active site scope.

## Future Requirements

- Real-time WebSockets streaming updates for telemetry metrics instead of polling.
- Multi-tenancy support for partitioned customer network views.
- Dynamic interface flap timeline graph per port.
- User-customizable drag-and-drop node pinning with layout state persisted in localStorage.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Third-party heavy canvas libraries (`reactflow` v11) | Incompatible with React 19; native SVG delivers zero bundle bloat and 100% theme integration. |
| Manual port wiring CAD editor | Operators monitor and triage existing infrastructure; topology links are computed deterministically. |
| Altering backend API endpoints | Multi-site topology is a client-side hierarchical SVG representation consuming existing `/api/alerts` and `/api/devices`. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SITE-01 | Phase 24 | Satisfied |
| SITE-02 | Phase 24 | Satisfied |
| SITE-03 | Phase 24 | Satisfied |
| SITE-04 | Phase 25 | Satisfied |
| SITE-05 | Phase 25 | Satisfied |
| SITE-06 | Phase 25 | Satisfied |
| SITE-07 | Phase 26 | Satisfied |
| SITE-08 | Phase 26 | Satisfied |

**Coverage:**
- v2.0 requirements: 8 total
- Satisfied: 8 (100.0%)
- Pending: 0 (0.0%)

---
*Requirements defined: 2026-10-06*  
*Last updated: 2026-10-06 after Phase 26 completion and Milestone v2.0 audit*
