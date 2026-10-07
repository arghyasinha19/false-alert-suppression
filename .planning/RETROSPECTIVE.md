# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v2.1 — Real DNAC Telemetry & Production Hardening

**Shipped:** 2026-10-07  
**Phases:** 3 | **Plans:** 5 | **Tasks:** 13

### What Was Built
- Real Cisco DNA Center hardware specification harvester (`extract_device_info_from_raw()`) and MongoDB `device_telemetry` persistence caching.
- SRE Drawer authoritative spec prioritization (`extractedModel`, `extractedSerial`, etc.), procedural switch mock gating (`isDnacActive`), and honest null states (`—`).
- Live reachability alert status verification (`dnac_status.py`) recognizing `UNREACHABLE` states and acknowledging `ACTIVE` instead of falling back to `UNCERTAIN`.
- Deep management-plane root-cause diagnostics card in SRE Drawer with error code `NCIM12013`, `SNMP Connectivity Failed`, and operating state isolation indicator (`Node Active (Uptime 7d 18h) • Management Plane Isolated`).
- Authoritative hostname propagation (`tr-ist-rtr01`) and geographical site extraction (`Istanbul` from `Global/EMEA/TR Istanbul/Umut Street`).

### What Worked
- Analyzing real Cisco Catalyst Center REST payloads upfront eliminated assumptions about data schemas and hierarchy paths.
- Distinguishing management plane timeouts (SNMP `NCIM12013`) on running routers (`uptime > 7d`) from physical device outages directly targeted the core user pain point.
- Hardening test isolation in `tests/test_prod_hardening.py` eliminated cross-file fixture pollution and ordering flakiness.
- Automated AST and JSX contract tests in `tests/test_frontend_sre_drawer_contract.py` enabled regression testing without headless browser overhead.

### What Was Inefficient
- Having to reconcile test fixtures across multiple test files when credentials leaked in global environments; resolved decisively with explicit mock fixture sets.

### Patterns Established
- Direct harvesting from nested `raw_response` objects with fallback preservation across both backend and frontend layers.
- Operating state isolation detection: comparing controller reachability with device uptime to differentiate data-plane health from management-plane polling failures.
- Geographical site token parsing with country code prefix trimming.

### Key Lessons
1. Real controller payloads often contain conflicting states (e.g. `reachabilityStatus: Unreachable` while `uptimeSeconds: 692019`); surfacing both clarifies reality for SREs rather than making binary assumptions.
2. In alert verification pipelines, cross-referencing device-level health when issue-level Assurance records do not match prevents spurious `UNCERTAIN` escalations.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Tests | Key Change |
|-----------|--------|-------|-------|------------|
| v2.0 | 3 | 5 | 106 | 2-level hierarchical WAN/LAN SVG topology canvas |
| v2.1 | 3 | 5 | 57 | Real DNAC payload harvesting & management plane diagnostic observability |

### Cumulative Quality

| Milestone | Tests | Regressions | Build Time |
|-----------|-------|-------------|------------|
| v2.0 | 106 | 0 | 894ms |
| v2.1 | 57 | 0 | 870ms |

### Top Lessons (Verified Across Milestones)

1. Contract-driven testing against AST/tokens guarantees UI and API structural stability with sub-second test execution.
2. Honest null states (`—`) and provenance indicators build SRE trust much more effectively than simulated procedural placeholder values.
