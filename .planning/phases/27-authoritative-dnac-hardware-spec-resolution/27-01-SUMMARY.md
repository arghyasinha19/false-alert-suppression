# Plan 27-01 Summary: Backend Authoritative Hardware Spec Extraction & Persistence

**Execution Date:** 2026-10-07  
**Status:** Completed  
**Requirements Satisfied:** DNAC-01  

## What Was Done

1. **Raw Response Hardware Spec Harvester (`dashboard/device_service.py`)**:
   - Implemented `extract_device_info_from_raw(raw_response, fallback_info)` which parses `raw_response.network_device` and `raw_response.device_detail`.
   - Extracts real hardware attributes:
     - `model`: Prioritizes `type`, `platformId`, `series`, `nwDeviceType`, `deviceSeries`.
     - `serial`: Extracts `serialNumber` from inventory or assurance.
     - `mac`: Extracts `macAddress` from inventory or assurance.
     - `os_version`: Extracts `softwareVersion` from inventory or assurance.
     - `ip_address`: Extracts `managementIpAddress` or `managementIpAddr`.
     - `hostname`: Extracts `hostname` or `nwDeviceName`.
     - `role`: Extracts `role` or `nwDeviceRole`.
2. **Telemetry Service Enrichment & MongoDB Persistence**:
   - In `fetch_device_telemetry()`, automatically enriches `device_info` with extracted specs whenever `raw_response` is obtained from live DNAC health queries.
   - Caches the enriched `device_info` in MongoDB `device_telemetry` collection on upsert.
   - Enhanced cache fallback to re-extract specs from cached `raw_response` if offline.
   - In `get_or_resolve_device_id()`, cross-checks `device_telemetry` by `device_id` when found in `alert_results` to retrieve previously cached specs instead of returning `None`.
3. **Automated Unit & Contract Tests**:
   - Added `test_telemetry_raw_response_hardware_extraction()` in `tests/test_device_telemetry_api.py` reproducing the exact captured Cisco ISR 4331 production response.
   - Verified that all 9 tests pass with 100% assertions satisfied.
