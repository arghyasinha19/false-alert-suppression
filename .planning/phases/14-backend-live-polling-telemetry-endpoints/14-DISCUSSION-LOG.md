# Phase 14: Backend Live Polling & Telemetry Endpoints - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-05  
**Phase:** 14-backend-live-polling-telemetry-endpoints  
**Areas discussed:** Telemetry Fallback & Offline Cache, Device Identifier & UUID Resolution, Live Poll Execution Scope, API Response Contract & Route Aliasing  

---

## Telemetry Fallback & Offline Cache

| Option | Description | Selected |
|--------|-------------|----------|
| Return empty/null telemetry vitals dict and source: 'offline' | When DNAC is unreachable or device is missing, return HTTP 200 with an empty/null telemetry vitals dict and source: 'offline' | ✓ |
| Return HTTP 200 with last-known cached telemetry or realistic simulation tagged source: 'cached_simulated' and reachable: false | Prevent SRE UI disruption | |
| Return HTTP 404/503 | Return error details | |

| Storage Option | Description | Selected |
|----------------|-------------|----------|
| Cache in MongoDB collection (e.g. 'device_telemetry') | Preserve last-known hardware vitals with timestamp | ✓ |
| In-memory cache with short TTL | Reduce load on DNAC during frequent polling | |
| Purely stateless | Query DNAC live on every request without caching | |

**User's choice:** Return HTTP 200 with empty/null vitals and source: 'offline' on total failure; cache successful live telemetry in MongoDB collection 'device_telemetry'.  
**Notes:** If a cached record exists from a prior successful fetch, return with `source: 'cached_offline'`.

---

## Device Identifier & UUID Resolution

| Option | Description | Selected |
|--------|-------------|----------|
| Two-tier resolution | Check MongoDB cache for device UUID first, falling back to DNACClient.get_device_by_name_or_ip(device_name) to look up the UUID | ✓ |
| Always query DNACClient.get_device_by_name_or_ip dynamically | Ensure fresh UUID and hardware inventory | |
| Strict resolution | Only resolve via DNACClient.get_device_by_name_or_ip and raise DeviceNotFoundError | |

**User's choice:** Two-tier resolution.  
**Notes:** Check MongoDB first, query DNAC on miss, cache resolved UUID for future queries. Raw 36-character UUID strings are supported directly.

---

## Live Poll Execution Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Full live sync | Synchronously re-poll active alert issue statuses in MongoDB + fetch fresh telemetry vitals and return consolidated device state | ✓ |
| Telemetry-only poll | Only re-fetch and cache live health vitals, leaving alert issue statuses to background sync daemon | |
| Async background task | Trigger background sync and return 202 Accepted immediately | |

**User's choice:** Full live sync.  
**Notes:** Synchronously update active alerts for this device in MongoDB and fetch fresh health vitals.

---

## API Response Contract & Route Aliasing

| Option | Description | Selected |
|--------|-------------|----------|
| Unified payload + dual route aliases | Return device_name, device_id, source, timestamp, telemetry (9 vitals), and device_info (model, serial, MAC, OS, IP) + dual-register both /api/devices/ and /api/device/ routes | ✓ |
| Telemetry-only payload | Return only telemetry vitals dict without device_info, register only /api/devices/ | |
| Separate endpoints | Keep telemetry and hardware inventory on separate endpoints | |

**User's choice:** Unified payload with dual route registration.  
**Notes:** Provides both telemetry and device_info in one response to power both SRE drawer tabs simultaneously; registers both singular `/api/device/` and plural `/api/devices/` paths.

---

## the agent's Discretion

- Choice of database indexes on `device_telemetry` (`device_name`, `device_id`).
- Specific timeout values for DNAC calls within endpoint request lifecycle.

---

## Deferred Ideas

None — discussion stayed within phase scope.
