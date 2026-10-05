# Requirements: False Alert Suppression Pipeline

**Defined:** 2026-10-05  
**Milestone:** v1.6 Live DNAC Assurance Telemetry & Asset Integration  
**Core Value:** Accurately identify false or transient network alerts to prevent unnecessary ServiceNow ticket creation and reduce operational noise without missing genuine network degradation.

## Milestone v1.6 Requirements: Live DNAC Assurance Telemetry & Asset Integration

### DNAC API Client Extensions (DNAC-CLIENT)
- [x] **DNAC-01**: `DNACClient` provides `get_device_by_name_or_ip(device_name_or_ip)` querying `/dna/intent/api/v1/network-device` to retrieve hardware model, serial number, MAC address, OS version, and reachability.
- [x] **DNAC-02**: `DNACClient` provides `get_device_health(device_id_or_name)` querying `/dna/intent/api/v1/device-health` to retrieve real CPU utilization %, memory %, packet drop %, and health score.

### Backend Endpoints & Live Polling (DNAC-API)
- [x] **DNAC-03**: Backend endpoint `GET /api/devices/{device_name}/telemetry` returns structured live DNAC vitals with `source: "dnac_live" | "cached_simulated"` and timestamp.
- [x] **DNAC-04**: Backend endpoint `POST /api/devices/{device_name}/live-poll` triggers an immediate on-demand DNAC issue and telemetry refresh, returning updated device state.

### Frontend SRE Drawer Live Integration (DNAC-UI)
- [x] **DNAC-05**: Clicking "Poll DNAC" in `NetworkOperations.jsx` triggers `POST /api/devices/{device_name}/live-poll` with visual spinner and toast notification displaying actual response.
- [x] **DNAC-06**: Assurance Telemetry and Device Inventory tabs in the SRE drawer render live vitals fetched from `/api/devices/{device_name}/telemetry` with live/offline source badges.

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
| Daemon supervisor bundling & standalone CLI diagnostic script | Removed per user decision; existing independent `dnac_sync.py` and pytest integration test suites cover operational and testing needs. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DNAC-01 | Phase 13 | Complete ✓ |
| DNAC-02 | Phase 13 | Complete ✓ |
| DNAC-03 | Phase 14 | Complete ✓ |
| DNAC-04 | Phase 14 | Complete ✓ |
| DNAC-05 | Phase 15 | Complete ✓ |
| DNAC-06 | Phase 15 | Complete ✓ |

**Coverage:**
- v1.6 requirements: 6 total
- Mapped to phases: 6 (100%)
- Completed: 6 (100%) ✓
- Unmapped: 0 ✓

---
*Requirements defined: 2026-10-05*  
*Last updated: 2026-10-05 after Milestone v1.6 completion*
