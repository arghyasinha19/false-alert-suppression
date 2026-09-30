# Requirements: False Alert Suppression Pipeline

**Defined:** 2026-09-30  
**Core Value:** Accurately identify false or transient network alerts to prevent unnecessary ServiceNow ticket creation and reduce operational noise without missing genuine network degradation.

## v1 Requirements

Requirements for Milestone v1.0.

### Metric Calculations & Consistency

- [x] **METRIC-01**: "Total Processed" field in False Alert Metrics calculates the total alerts processed by the system as the exact sum of `Suppressed + Auto-Resolving + Non-Auto-Resolving + Uncertain`.
- [x] **METRIC-02**: "Tickets Avoided" is verified as a derived metric representing alerts where ticket creation was suppressed (`Suppressed + Auto-Resolving`) without double-counting in Total Processed.
- [x] **METRIC-03**: "Total Processed" KPI card retains the total alert volume in the active device/time scope when category filters are selected, displaying a sub-value with the filtered count and category name.
- [x] **METRIC-04**: Category KPI cards (Backdated/Suppressed, Auto-Resolving, Non-Auto-Resolving, Uncertain) toggle on and off when clicked, show an active border/highlight state, and maintain their respective category volume.
- [x] **METRIC-05**: Backend `/api/kpi/summary` in `dashboard/api.py` and `dashboard/chat_agent.py` verify that `total_alerts` matches the category breakdown sum.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Modifying ML training pipelines | Milestone is focused on UI metric fidelity and dashboard aggregation accuracy. |
| Altering ServiceNow API authentication | Core ServiceNow client logic is already established and functioning. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| METRIC-01 | Phase 1 | Complete |
| METRIC-02 | Phase 1 | Complete |
| METRIC-03 | Phase 1 | Complete |
| METRIC-04 | Phase 1 | Complete |
| METRIC-05 | Phase 1 | Complete |

**Coverage:**
- v1 requirements: 5 total
- Mapped to phases: 5
- Complete: 5 ✓
- Unmapped: 0 ✓

---
*Requirements defined: 2026-09-30*  
*Last updated: 2026-09-30 after Phase 1 completion*
