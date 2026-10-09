# Milestone v2.2 Requirements

## Production Readiness & Mock Elimination
- [ ] **PROD-01**: The backend processing pipeline must not generate, load, or inject synthetic/simulated alerts (e.g., from `data/simulated_alerts.json`).
- [ ] **PROD-02**: The frontend dashboard (Network Operations, SRE Drawer) must completely remove offline simulation fallbacks (no mock procedural switches or simulated node vitals).
- [ ] **PROD-03**: The backend API endpoints (`/api/devices`, `/api/devices/{name}/telemetry`, etc.) must fail fast with appropriate error codes instead of returning mocked payloads when DNAC or MongoDB is unreachable.
- [ ] **PROD-04**: The system must enforce strict reliance on live Cisco DNA Center API data and MongoDB persistent storage for all features, including the multi-site WAN and LAN topology graphs.

## Future Requirements
- None currently scoped.

## Out of Scope
- Complete removal of the `data/` directory (static configurations or non-mock test data might be preserved if needed for CI).
- Changes to the core ML classification logic or threshold tuning.

## Traceability
*(To be populated by roadmap)*
