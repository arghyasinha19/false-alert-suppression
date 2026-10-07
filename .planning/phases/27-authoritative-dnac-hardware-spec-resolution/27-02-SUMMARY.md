# Plan 27-02 Summary: Frontend SRE Drawer Authoritative Specs Prioritization & Honest Null States

**Execution Date:** 2026-10-07  
**Status:** Completed  
**Requirements Satisfied:** DNAC-02  

## What Was Done

1. **Frontend Spec Resolution & Gating (`dashboard/src/NetworkOperations.jsx`)**:
   - Updated SRE Drawer to extract authentic specs (`extractedModel`, `extractedSerial`, `extractedMac`, `extractedOs`, `extractedIp`, `extractedUptime`) directly from `liveDeviceInfo` or `liveTelemetry.raw_response.network_device` / `liveTelemetry.raw_response.device_detail`.
   - Gated procedural switch mock fallbacks (`proceduralVitals`) using `isDnacActive` (`telemetrySource === 'dnac_live' || telemetrySource === 'cached_offline'`). When connected or viewing cached telemetry, the UI will never fall back to synthetic Catalyst 9300 switch defaults.
   - For unreachable devices (`liveTelemetry?.reachable === false`), eliminated procedural RAM/latency mock bleed-through, setting them to `null` so honest degraded/unreachable states are reflected.
   - Updated `deriveDeviceRole` to accept live role (`liveDeviceInfo?.role` or `raw_response`) and added support for `"border"` router roles, correctly placing border routers into Core & WAN architecture tiers instead of access tier.
   - Updated device spec cards in the SRE Drawer to render honest null indicators (`—`) rather than synthetic mock placeholders.

2. **Automated Unit & Contract Tests**:
   - Added `test_network_operations_authoritative_spec_resolution_contract()` to `tests/test_frontend_sre_drawer_contract.py`.
   - Asserted that model/serial/mac/os/ip extraction from raw response is present, `isDnacActive` gating is strictly enforced, and honest null placeholders are rendered.
   - Verified that all 6 tests in `tests/test_frontend_sre_drawer_contract.py` pass.

3. **Frontend Production Build**:
   - Ran `npm run build` in `dashboard/` with Vite v8.1.0; built cleanly with 0 errors in 779ms.
