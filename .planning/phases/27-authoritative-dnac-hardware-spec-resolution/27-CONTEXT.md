# Phase 27: Authoritative DNAC Hardware & Spec Resolution - Context

**Gathered:** 2026-10-07  
**Status:** Ready for planning  
**Mode:** Smart Plan (Phase 27 Execution)  
**Requirements:** DNAC-01, DNAC-02  

<domain>
## Phase Boundary

Eliminate procedural mock bleed-through and ensure genuine Cisco DNA Center device specifications (model, serial, MAC, OS version, management IP) are extracted from raw DNAC responses, persisted in MongoDB telemetry cache, and prioritized in the frontend SRE drawer over synthetic switch placeholders.
</domain>

<decisions>
## Implementation Decisions

### Area 1: Backend Authoritative Spec Extraction (`DNAC-01`)
- **Raw Response Spec Harvester in `dashboard/device_service.py`**:
  - Implement `extract_device_info_from_raw(raw_response, fallback_info=None)` that inspects both `raw_response.network_device` (inventory from `/network-device/{id}`) and `raw_response.device_detail` (assurance from `/device-detail`):
    - `model`: `inventory.get("type") or inventory.get("platformId") or detail.get("nwDeviceType") or detail.get("platformId")`
    - `serial`: `inventory.get("serialNumber") or detail.get("serialNumber")`
    - `mac`: `inventory.get("macAddress") or detail.get("macAddress")`
    - `os_version`: `inventory.get("softwareVersion") or detail.get("softwareVersion")`
    - `ip_address`: `inventory.get("managementIpAddress") or detail.get("managementIpAddr") or detail.get("ip_addr_managementIpAddr")`
    - `hostname`: `inventory.get("hostname") or detail.get("nwDeviceName")`
    - `role`: `inventory.get("role") or detail.get("nwDeviceRole")`
- **Cache Persistence & Enrichment**:
  - In `fetch_device_telemetry()`: If `raw_health` contains `raw_response`, automatically merge extracted specs into `device_info`.
  - Cache the enriched `device_info` in MongoDB `device_telemetry` so subsequent reads retain full hardware identity even if offline.
- **Cache Resolution Optimization**:
  - In `get_or_resolve_device_id()`: When `device_id` is found in `alert_results`, cross-check `device_telemetry` to retrieve previously cached `device_info` rather than returning `None`.

### Area 2: Frontend Honest Spec Prioritization (`DNAC-02`)
- **Eliminate Procedural Bleed-Through in `dashboard/src/NetworkOperations.jsx`**:
  - In `vitals` computation, when `telemetrySource === 'dnac_live'` or `telemetrySource === 'cached_offline'`:
    - Prioritize `liveDeviceInfo` and direct extraction from `deviceTelemetry.telemetry.raw_response`.
    - If a spec is not reported by DNAC, display honest unknown/null (`null` / `"—"`) instead of falling back to `proceduralVitals(device)` (which hashes the IP and hallucinates a `Cisco Catalyst 9300-48UXM Switch`, fake serial `FCW2530646`, and fake IP `10.14.76.67`).
  - For unreachable devices (`liveTelemetry.reachable === false`), do NOT inherit synthetic RAM (`7.1 / 8.0`) or latency (`48ms`) from procedural vitals.
  - In Tab 4 (Raw Payloads), ensure `telemetry_vitals` reflects honest live vitals without procedural switch mock overrides.
</decisions>

<code_context>
## Existing Code Insights

- `dashboard/device_service.py` defines `get_or_resolve_device_id` and `fetch_device_telemetry`.
- `app/dnac_client.py` packs `{"device_detail": detail, "network_device": inventory}` into `raw_response`.
- `dashboard/src/NetworkOperations.jsx` lines 500-556 define `getDeviceTelemetryVitals()`, and lines 2000-2045 compute `displayModel`, `displayOs`, `displaySerial`, `displayMac`, `displayIp`, and `vitals`.
- `tests/test_device_telemetry_api.py` and `tests/test_frontend_sre_drawer_contract.py` test the telemetry contract.
</code_context>
