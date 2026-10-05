# Requirements: False Alert Suppression Pipeline

**Defined:** 2026-10-05  
**Milestone:** v1.8 Interactive Network Topology Graph Diagram  
**Core Value:** Accurately identify false or transient network alerts to prevent unnecessary ServiceNow ticket creation and reduce operational noise without missing genuine network degradation.

## Milestone v1.8 Requirements: Interactive Network Topology Graph Diagram

### Interactive Canvas & Viewport Navigation (GRAPH-CANVAS)
- [x] **GRAPH-01**: User can view network devices in an interactive, zoomable and pannable SVG canvas graph diagram with smooth mouse wheel zooming, drag-to-pan, and fit-to-screen controls.
- [x] **GRAPH-02**: Canvas provides floating navigation controls (Zoom In, Zoom Out, Fit to View, Reset 100%) and a fast sub-mode toggle between Graph View and Card Grid View.

### Hierarchical Network Topology & Edge Links (GRAPH-LINKS)
- [x] **GRAPH-03**: Devices are arranged into 3 distinct hierarchical network tiers (Core & WAN Backbone at top, Distribution & Security in middle, Campus & Access Edge at bottom) with subtle background tier lanes.
- [x] **GRAPH-04**: Interconnected network links (edges) connect upstream and downstream devices with health-aware styling (teal for nominal, amber for warning, red for critical) and subtle animated traffic pulses.

### Health-Aware Node Cards & SRE Drawer Integration (GRAPH-NODES)
- [ ] **GRAPH-05**: Device nodes render as rich micro-cards with role icons, hostnames, management IPs, health status dots (including pulsing red for critical), and active alert count badges.
- [ ] **GRAPH-06**: Clicking any device node on the graph canvas opens the 580px slide-out SRE details drawer for that device with glowing selection highlight.
- [ ] **GRAPH-07**: Node rendering reactively adapts to active Role, Health, and search query filters by highlighting matches and dimming non-matches.

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
| Altering backend API endpoints | Topology graph is purely client-side SVG representation consuming existing `/api/alerts` and `/api/devices`. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| GRAPH-01 | Phase 17 | Complete ✓ |
| GRAPH-02 | Phase 17 | Complete ✓ |
| GRAPH-03 | Phase 17 | Complete ✓ |
| GRAPH-04 | Phase 17 | Complete ✓ |
| GRAPH-05 | Phase 18 | Pending |
| GRAPH-06 | Phase 18 | Pending |
| GRAPH-07 | Phase 18 | Pending |

**Coverage:**
- v1.8 requirements: 7 total
- Mapped to phases: 7 (100%)
- Unmapped: 0 ✓

---
*Requirements defined: 2026-10-05*  
*Last updated: 2026-10-05 after Milestone v1.8 research*
