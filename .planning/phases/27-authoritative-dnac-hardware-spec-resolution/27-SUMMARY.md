---
phase: 27-authoritative-dnac-hardware-spec-resolution
requirements_completed:
  - DNAC-01
  - DNAC-02
---

# Phase 27 Summary: Authoritative DNAC Hardware & Spec Resolution

**Completed:** 2026-10-07  
**Milestone:** v2.1 Real DNAC Telemetry & Production Hardening  
**Phase Status:** Complete  

---

## 1. Overview & Objectives

Phase 27 eliminated synthetic hardware and specification mock bleed-through across the backend telemetry resolution pipeline and frontend SRE drawer. Previously, when alerts were matched via `alert_results`, `get_or_resolve_device_id()` returned `(device_id, None)`, leaving `device_info` empty. The frontend SRE drawer then hashed the IP (`10.254.0.93`) using `proceduralVitals()` into a synthetic `Cisco Catalyst 9300-48UXM Switch` with serial `FCW2530646` and fake RAM/latency metrics.

In Phase 27, we implemented authoritative extraction from live Cisco DNA Center (Catalyst Center) REST responses (`network_device` and `device_detail`), enriched MongoDB persistence caching, gated procedural vitals strictly to offline/disconnected mode, supported border router classification, and enforced honest null/degraded metrics for unreachable devices.

---

## 2. Requirements Delivered

| Requirement | Description | Status | Implementation Details |
|---|---|---|---|
| **DNAC-01** | Backend raw response hardware spec harvester & persistence caching | **Complete** | Implemented `extract_device_info_from_raw()` in `dashboard/device_service.py` to harvest `model`, `serial`, `mac`, `os_version`, `ip_address`, `hostname`, and `role` from DNAC `network_device` and `device_detail`. Enriched MongoDB `device_telemetry` cache. |
| **DNAC-02** | Frontend SRE Drawer authoritative spec prioritization & honest null states | **Complete** | Updated `dashboard/src/NetworkOperations.jsx` to resolve live specs from `liveDeviceInfo` or `liveTelemetry.raw_response`. Gated `proceduralVitals` to offline mode only (`isDnacActive`). Updated `deriveDeviceRole` to accept live border router roles. Rendered honest nulls (`—`) in drawer cards. |

---

## 3. Key Changes & Verified Components

### 3.1 Backend: `dashboard/device_service.py`
- Added `extract_device_info_from_raw(raw_response, fallback_info)`:
  - Extracts model from `type`, `platformId`, `nwDeviceType`, etc. (resolving `Cisco 4331 Integrated Services Router` / `ISR4331/K9`).
  - Extracts serial number (`FDO2517M1EG`), MAC address (`6C:13:D5:BE:91:F0`), OS version (`17.12.8`), and hostname (`tr-ist-rtr01`).
- Enriched `fetch_device_telemetry()` to populate `device_info` directly from `raw_response` and upsert into MongoDB.
- Enhanced cache fallback in `get_or_resolve_device_id()` to query `device_telemetry` by `device_id` when found in alert results.

### 3.2 Frontend: `dashboard/src/NetworkOperations.jsx`
- Added `extractedModel`, `extractedSerial`, `extractedMac`, `extractedOs`, `extractedIp`, and `extractedUptime` prioritizing live response data.
- Added `isDnacActive = telemetrySource === 'dnac_live' || telemetrySource === 'cached_offline'` guard to prevent procedural switch mocks from ever displaying when connected or viewing cached telemetry.
- Cleared procedural RAM and latency when `liveTelemetry.reachable === false`.
- Updated `deriveDeviceRole` to recognize `"border"` router roles as Core & WAN tier.
- SRE Drawer inventory cards display honest nulls (`—`) instead of procedural switch placeholders.

### 3.3 Automated Contract & Unit Testing
- `tests/test_device_telemetry_api.py`: Added `test_telemetry_raw_response_hardware_extraction` mirroring exact production DNAC response for Cisco 4331 ISR (`10.254.0.93`). 9 of 9 tests pass.
- `tests/test_frontend_sre_drawer_contract.py`: Added `test_network_operations_authoritative_spec_resolution_contract` testing extraction presence, `isDnacActive` gating, border router role detection, and honest null rendering. 6 of 6 tests pass.
- `npm run build`: Production bundle compiled cleanly in 779ms.

---

## 4. Verification Results

```bash
pytest tests/test_device_telemetry_api.py tests/test_frontend_sre_drawer_contract.py
============================= 15 passed in 6.01s ==============================

npm run build (dashboard/)
✓ built in 779ms
```
