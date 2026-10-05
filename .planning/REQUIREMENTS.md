# Requirements: False Alert Suppression Pipeline

**Defined:** 2026-10-05  
**Milestone:** v1.6 Live DNAC Assurance Telemetry & Asset Integration  
**Core Value:** Accurately identify false or transient network alerts to prevent unnecessary ServiceNow ticket creation and reduce operational noise without missing genuine network degradation.

## Milestone v1.6 Requirements: Live DNAC Assurance Telemetry & Asset Integration

### DNAC API Client Extensions (DNAC-CLIENT)
- [ ] **DNAC-01**: `DNACClient` provides `get_device_by_name_or_ip(device_name_or_ip)` querying `/dna/intent/api/v1/network-device` to retrieve hardware model, serial number, MAC address, OS version, and reachability.
- [ ] **DNAC-02**: `DNACClient` provides `get_device_health(device_id_or_name)` querying `/dna/intent/api/v1/device-health` to retrieve real CPU utilization %, memory %, packet drop %, and health score.

### Backend Endpoints & Live Polling (DNAC-API)
- [ ] **DNAC-03**: Backend endpoint `GET /api/devices/{device_name}/telemetry` returns structured live DNAC vitals with `source: "dnac_live" | "cached_simulated"` and timestamp.
- [ ] **DNAC-04**: Backend endpoint `POST /api/devices/{device_name}/live-poll` triggers an immediate on-demand DNAC issue and telemetry refresh, returning updated device state.

### Frontend SRE Drawer Live Integration (DNAC-UI)
- [ ] **DNAC-05**: Clicking "Poll DNAC" in `NetworkOperations.jsx` triggers `POST /api/devices/{device_name}/live-poll` with visual spinner and toast notification displaying actual response.
- [ ] **DNAC-06**: Assurance Telemetry and Device Inventory tabs in the SRE drawer render live vitals fetched from `/api/devices/{device_name}/telemetry` with live/offline source badges.

### Service Orchestration (DNAC-OPS)
- [ ] **DNAC-07**: `start_dashboard.py` auto-starts `dashboard/dnac_sync.py` background daemon alongside FastAPI and Vite, handling unified process supervision and graceful SIGINT/SIGTERM termination.

### Testing & Diagnostics Harness (DNAC-TEST)
- [ ] **DNAC-08**: Provide standalone interactive CLI test tool `test_dnac_integration.py` with step-by-step verification of credentials, auth token, issue lookup, device inventory, and telemetry vitals (with `--mock` switch for offline verification).

## Future Requirements

- Real-time WebSockets streaming updates for telemetry metrics instead of polling.
- Multi-tenancy support for partitioned customer network views.
- Dynamic interface flap timeline graph per port.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Bypassing DNAC RBAC or making unauthenticated calls | All calls must authenticate with basic auth credentials to obtain temporary tokens. |
| Hardcoding cleartext passwords | Passwords must load from environment variables (`DNAC_PASSWORD`) or `config.yaml`. |
| Modifying ML training checkpoints | ML models operate independently downstream from DNAC ingestion. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DNAC-01 | Phase 13 | Pending |
| DNAC-02 | Phase 13 | Pending |
| DNAC-03 | Phase 14 | Pending |
| DNAC-04 | Phase 14 | Pending |
| DNAC-05 | Phase 15 | Pending |
| DNAC-06 | Phase 15 | Pending |
| DNAC-07 | Phase 16 | Pending |
| DNAC-08 | Phase 16 | Pending |

**Coverage:**
- v1.6 requirements: 8 total
- Mapped to phases: 8 (100%)
- Unmapped: 0 ✓

---
*Requirements defined: 2026-10-05*  
*Last updated: 2026-10-05 after Milestone v1.6 requirements definition*
