"""
Device Telemetry & Live Polling Service
=======================================
Provides UUID resolution, live DNAC Assurance telemetry retrieval,
MongoDB caching in the 'device_telemetry' collection, and on-demand
live polling synchronization.

Designed for robust fault tolerance: never raises unhandled exceptions
to caller endpoints, always returning graceful offline structures.
"""

import re
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any

from app.exceptions import DNACError, DeviceNotFoundError, DNACConnectionError

logger = logging.getLogger("DeviceService")

UUID_REGEX = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def utc_now_iso() -> str:
    """Return current UTC time in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def get_empty_telemetry_dict() -> Dict[str, Any]:
    """Return a standard empty/null telemetry dictionary for offline states."""
    return {
        "cpu": None,
        "memory": None,
        "packet_drop": None,
        "health_score": None,
        "interface_error_count": None,
        "poe_status": None,
        "uptime_seconds": None,
        "reachable": False,
        "raw_response": None,
    }


def extract_site_from_location_path(location_path: Optional[str]) -> Optional[str]:
    """
    Extract a clean geographical site name from a DNAC hierarchical location path.
    Example: 'Global/EMEA/TR Istanbul/Umut Street' -> 'Istanbul'
    """
    if not location_path or not isinstance(location_path, str):
        return None
    parts = [p.strip() for p in location_path.split("/") if p.strip()]
    if not parts:
        return None

    # Often hierarchy is: Global / Region / Country City / Building
    # e.g., parts[2] = 'TR Istanbul'
    candidate = None
    if len(parts) >= 3:
        candidate = parts[2]
    elif len(parts) == 2:
        candidate = parts[1]
    else:
        candidate = parts[0]

    # Strip country code prefix (e.g. 'TR Istanbul' -> 'Istanbul', 'US New York' -> 'New York')
    candidate = re.sub(r"^[A-Z]{2}\s+", "", candidate).strip()
    return candidate or parts[-1]


def extract_device_info_from_raw(
    raw_response: Optional[Dict[str, Any]],
    fallback_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Extract authentic hardware specifications from DNAC raw_response.
    
    raw_response contains:
      - "network_device": inventory dict from GET /network-device/{id}
      - "device_detail": assurance dict from GET /device-detail?identifier=uuid&searchBy={id}
    """
    default_info = {
        "model": "Unknown",
        "serial": "Unknown",
        "mac": "Unknown",
        "os_version": "Unknown",
        "ip_address": "Unknown",
        "hostname": None,
        "role": None,
        "site_name": None,
        "location_path": None,
        "diagnostics": {
            "reachability_status": None,
            "reachability_failure_reason": None,
            "error_code": None,
            "diagnostic_message": None,
            "uptime_seconds": None,
            "is_management_plane_isolated": False,
        },
    }
    info = dict(fallback_info) if fallback_info else dict(default_info)
    if "diagnostics" not in info or not isinstance(info["diagnostics"], dict):
        info["diagnostics"] = dict(default_info["diagnostics"])
    
    if not raw_response or not isinstance(raw_response, dict):
        return info

    inv = raw_response.get("network_device") or {}
    if not isinstance(inv, dict):
        inv = {}

    det = raw_response.get("device_detail") or {}
    if not isinstance(det, dict):
        det = {}

    def _is_valid(val):
        if val is None:
            return False
        s = str(val).strip()
        return s != "" and s.lower() not in ("unknown", "none", "null", "na")

    # 1. Model / Platform ID
    model_candidates = [
        inv.get("type"),
        inv.get("platformId"),
        inv.get("series"),
        det.get("nwDeviceType"),
        det.get("platformId"),
        det.get("deviceSeries"),
    ]
    for m in model_candidates:
        if _is_valid(m) and (not _is_valid(info.get("model")) or info.get("model") == "Unknown"):
            info["model"] = str(m).strip()
            break

    # 2. Serial Number
    serial_candidates = [
        inv.get("serialNumber"),
        det.get("serialNumber"),
    ]
    for s in serial_candidates:
        if _is_valid(s) and (not _is_valid(info.get("serial")) or info.get("serial") == "Unknown"):
            info["serial"] = str(s).strip()
            break

    # 3. MAC Address
    mac_candidates = [
        inv.get("macAddress"),
        det.get("macAddress"),
    ]
    for mc in mac_candidates:
        if _is_valid(mc) and (not _is_valid(info.get("mac")) or info.get("mac") == "Unknown"):
            info["mac"] = str(mc).strip()
            break

    # 4. OS Version
    os_candidates = [
        inv.get("softwareVersion"),
        det.get("softwareVersion"),
    ]
    for o in os_candidates:
        if _is_valid(o) and (not _is_valid(info.get("os_version")) or info.get("os_version") == "Unknown"):
            info["os_version"] = str(o).strip()
            break

    # 5. Management IP
    ip_candidates = [
        inv.get("managementIpAddress"),
        det.get("managementIpAddr"),
        det.get("ip_addr_managementIpAddr"),
    ]
    for ip_c in ip_candidates:
        if _is_valid(ip_c) and (not _is_valid(info.get("ip_address")) or info.get("ip_address") == "Unknown"):
            info["ip_address"] = str(ip_c).strip()
            break

    # 6. Hostname
    hostname_candidates = [
        inv.get("hostname"),
        det.get("nwDeviceName"),
    ]
    for h in hostname_candidates:
        if _is_valid(h) and not _is_valid(info.get("hostname")):
            info["hostname"] = str(h).strip()
            break

    # 7. Device Role
    role_candidates = [
        inv.get("role"),
        det.get("nwDeviceRole"),
    ]
    for r in role_candidates:
        if _is_valid(r) and not _is_valid(info.get("role")):
            info["role"] = str(r).strip()
            break

    # 8. Location & Site Name (DNAC-05)
    location_candidates = [
        det.get("location"),
        inv.get("locationName"),
        inv.get("location"),
    ]
    for loc in location_candidates:
        if _is_valid(loc):
            loc_str = str(loc).strip()
            info["location_path"] = loc_str
            info["site_name"] = extract_site_from_location_path(loc_str)
            break

    # 9. Management Plane Diagnostics (DNAC-04)
    fail_reason = inv.get("reachabilityFailureReason") or det.get("communicationState") or None
    err_code = inv.get("errorCode") or None
    if not err_code and fail_reason and "snmp" in str(fail_reason).lower():
        err_code = "NCIM12013"

    diag_desc = None
    if (fail_reason and "snmp" in str(fail_reason).lower()) or err_code == "NCIM12013":
        err_code = err_code or "NCIM12013"
        diag_desc = (
            "SNMP request timeout. Device may be unreachable or SNMP credentials configured "
            "on device may be different from Catalyst Center credentials."
        )

    raw_uptime = inv.get("uptimeSeconds")
    uptime_secs = None
    if raw_uptime is not None:
        try:
            uptime_secs = int(float(raw_uptime))
        except (ValueError, TypeError):
            uptime_secs = None

    reach_status = str(inv.get("reachabilityStatus") or det.get("communicationState") or "").lower()
    is_unreachable = reach_status in ("unreachable", "disconnected", "false")
    is_isolated = bool(uptime_secs and uptime_secs > 300 and is_unreachable)

    info["diagnostics"] = {
        "reachability_status": inv.get("reachabilityStatus") or det.get("communicationState") or None,
        "reachability_failure_reason": inv.get("reachabilityFailureReason") or (fail_reason if is_unreachable else None),
        "error_code": err_code,
        "diagnostic_message": diag_desc,
        "uptime_seconds": uptime_secs,
        "is_management_plane_isolated": is_isolated,
    }

    return info


def get_or_resolve_device_id(
    device_name: str,
    mongo_client=None,
    dnac_client=None,
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Resolve a device name or IP to a DNAC device UUID (and hardware metadata).

    Two-tier resolution:
    1. Check MongoDB 'device_telemetry' or 'alert_results' cache.
    2. Check if device_name is already a raw UUID.
    3. Query DNACClient.get_device_by_name_or_ip(device_name).
    """
    if not device_name:
        return None, None

    # Check if device_name itself is already a 36-char UUID
    if UUID_REGEX.match(device_name.strip()):
        return device_name.strip(), None

    device_id = None
    device_info = None

    # Tier 1: Check MongoDB cache
    if mongo_client is not None:
        try:
            # Check device_telemetry collection
            telemetry_coll = mongo_client.get_collection("device_telemetry")
            if telemetry_coll is not None:
                cached = telemetry_coll.find_one({"device_name": device_name})
                if cached and cached.get("device_id"):
                    device_id = cached.get("device_id")
                    device_info = cached.get("device_info")
                    return device_id, device_info

            # Check alert_results collection
            alerts_coll = mongo_client.get_collection("alert_results")
            if alerts_coll is not None:
                query = {
                    "$or": [
                        {"alert_details.device_name": device_name},
                        {"alert_details.device": device_name},
                    ],
                    "alert_details.device_id": {"$exists": True, "$ne": ""},
                }
                match = alerts_coll.find_one(query)
                if match:
                    details = match.get("alert_details", {})
                    found_id = details.get("device_id")
                    if found_id:
                        device_id = found_id
                        # Cross-check device_telemetry for cached specs using found_id
                        if telemetry_coll is not None:
                            cached_dev = telemetry_coll.find_one({"device_id": found_id})
                            if cached_dev and cached_dev.get("device_info"):
                                device_info = cached_dev.get("device_info")
                        return device_id, device_info
        except Exception as e:
            logger.warning(f"Error checking MongoDB cache for device {device_name}: {e}")

    # Tier 2: Query DNACClient live inventory
    if dnac_client is not None:
        try:
            devices = dnac_client.get_device_by_name_or_ip(device_name)
            if devices and isinstance(devices, list) and len(devices) > 0:
                dev = devices[0]
                device_id = dev.get("device_id")
                device_info = {
                    "model": dev.get("model"),
                    "serial": dev.get("serial"),
                    "mac": dev.get("mac"),
                    "os_version": dev.get("os_version"),
                    "ip_address": dev.get("ip_address"),
                }
                return device_id, device_info
        except (DeviceNotFoundError, DNACConnectionError) as e:
            logger.info(f"DNAC inventory lookup miss or connection error for {device_name}: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error querying DNAC inventory for {device_name}: {e}")

    return device_id, device_info


def fetch_device_telemetry(
    device_name: str,
    mongo_client=None,
    dnac_client=None,
) -> Dict[str, Any]:
    """
    Fetch device telemetry vitals and hardware specifications.

    Attempts live DNAC health retrieval first. On success, caches in MongoDB.
    On failure or when offline, falls back to MongoDB cached state with
    source: 'cached_offline', or returns null vitals with source: 'offline'.
    Never raises unhandled exceptions.
    """
    now_iso = utc_now_iso()
    default_info = {
        "model": "Unknown",
        "serial": "Unknown",
        "mac": "Unknown",
        "os_version": "Unknown",
        "ip_address": "Unknown",
    }

    # 1. Resolve UUID and available device info
    device_id, device_info = get_or_resolve_device_id(device_name, mongo_client, dnac_client)

    # 2. Try live DNAC telemetry fetch
    if device_id and dnac_client is not None:
        try:
            raw_health = dnac_client.get_device_health(device_id)
            if raw_health and isinstance(raw_health, dict):
                raw_resp = raw_health.get("raw_response")
                if raw_resp and isinstance(raw_resp, dict):
                    device_info = extract_device_info_from_raw(raw_resp, fallback_info=device_info)

                telemetry = {
                    "cpu": raw_health.get("cpu"),
                    "memory": raw_health.get("memory"),
                    "packet_drop": raw_health.get("packet_drop"),
                    "health_score": raw_health.get("health_score"),
                    "interface_error_count": raw_health.get("interface_error_count"),
                    "poe_status": raw_health.get("poe_status"),
                    "uptime_seconds": raw_health.get("uptime_seconds"),
                    "reachable": raw_health.get("reachable", True),
                    "raw_response": raw_resp,
                }

                # Update / cache in MongoDB
                if mongo_client is not None:
                    try:
                        telemetry_coll = mongo_client.get_collection("device_telemetry")
                        if telemetry_coll is not None:
                            cache_doc = {
                                "device_name": device_name,
                                "device_id": device_id,
                                "telemetry": telemetry,
                                "device_info": device_info or default_info,
                                "last_updated": now_iso,
                                "source": "dnac_live",
                            }
                            telemetry_coll.update_one(
                                {"device_name": device_name},
                                {"$set": cache_doc},
                                upsert=True,
                            )
                    except Exception as e:
                        logger.warning(f"Failed to cache telemetry in MongoDB for {device_name}: {e}")

                return {
                    "device_name": device_name,
                    "device_id": device_id,
                    "source": "dnac_live",
                    "timestamp": now_iso,
                    "telemetry": telemetry,
                    "device_info": device_info or default_info,
                }
        except (DNACConnectionError, DeviceNotFoundError) as e:
            logger.info(f"DNAC telemetry retrieval failed for {device_name} ({device_id}): {e}")
        except Exception as e:
            logger.warning(f"Unexpected error retrieving DNAC telemetry for {device_name}: {e}")

    # 3. Fallback: check MongoDB for previously cached state
    if mongo_client is not None:
        try:
            telemetry_coll = mongo_client.get_collection("device_telemetry")
            if telemetry_coll is not None:
                cached = telemetry_coll.find_one({"device_name": device_name})
                if not cached and device_id:
                    cached = telemetry_coll.find_one({"device_id": device_id})
                if cached and cached.get("telemetry"):
                    cached_telemetry = cached.get("telemetry")
                    if isinstance(cached_telemetry, dict):
                        cached_telemetry["reachable"] = False
                        raw_resp = cached_telemetry.get("raw_response")
                        if raw_resp and isinstance(raw_resp, dict):
                            device_info = extract_device_info_from_raw(
                                raw_resp,
                                fallback_info=cached.get("device_info") or device_info
                            )
                    return {
                        "device_name": device_name,
                        "device_id": cached.get("device_id") or device_id,
                        "source": "cached_offline",
                        "timestamp": cached.get("last_updated") or now_iso,
                        "telemetry": cached_telemetry,
                        "device_info": device_info or cached.get("device_info") or default_info,
                    }
        except Exception as e:
            logger.warning(f"Failed to read cached telemetry for {device_name}: {e}")


    # 4. Total fallback: return null/empty vitals
    return {
        "device_name": device_name,
        "device_id": device_id,
        "source": "offline",
        "timestamp": now_iso,
        "telemetry": get_empty_telemetry_dict(),
        "device_info": device_info or default_info,
    }


def poll_device_live(
    device_name: str,
    mongo_client=None,
    dnac_client=None,
) -> Dict[str, Any]:
    """
    Perform on-demand live poll for a device:
    1. Re-verifies all active alerts for this device in MongoDB via DNAC monitor.
    2. Updates 'dnac_live_status' and 'dnac_last_checked' in MongoDB.
    3. Fetches fresh telemetry and updates 'device_telemetry' cache.
    4. Returns consolidated status dictionary without raising HTTP 500 errors.
    """
    now_iso = utc_now_iso()
    alerts_updated = 0

    # 1. Query MongoDB for active (non-RESOLVED, non-backdated) alerts on this device
    if mongo_client is not None:
        try:
            from dashboard.dnac_monitor import check_dashboard_dnac_status

            alerts_coll = mongo_client.get_collection("alert_results")
            if alerts_coll is not None:
                query = {
                    "$and": [
                        {
                            "$or": [
                                {"alert_details.device_name": device_name},
                                {"alert_details.device": device_name},
                            ]
                        },
                        {
                            "results.agent_1.data.is_backdated": {"$ne": True},
                        },
                        {
                            "dnac_live_status": {"$ne": "RESOLVED"},
                        },
                    ]
                }
                alerts = list(alerts_coll.find(query))

                for a in alerts:
                    details = a.get("alert_details", {})
                    instance_id = (
                        details.get("instance_id")
                        or details.get("event_id")
                        or details.get("issue_id")
                    )
                    event_id = details.get("event_id")
                    dev_id = details.get("device_id")
                    issue_name = details.get("issue_name")
                    issue_details = details.get("issue_details")

                    status = check_dashboard_dnac_status(
                        instance_id=instance_id,
                        device_id=dev_id,
                        device_name=device_name,
                        issue_name=issue_name,
                        issue_details=issue_details,
                        event_id=event_id,
                        issue_id=details.get("issue_id"),
                    )

                    # eventId is an event TYPE (e.g. NETWORK-DEVICES-3-506) shared by many
                    # alerts on many devices - update only this document.
                    update_filter = {"_id": a["_id"]}
                    alerts_coll.update_one(
                        update_filter,
                        {
                            "$set": {
                                "dnac_live_status": status,
                                "dnac_last_checked": now_iso,
                            }
                        },
                    )
                    alerts_updated += 1
        except Exception as e:
            logger.warning(f"Error checking active alerts during live poll for {device_name}: {e}")

    # 2. Fetch fresh telemetry
    telemetry_res = fetch_device_telemetry(device_name, mongo_client, dnac_client)
    dnac_reachable = telemetry_res.get("source") == "dnac_live"

    return {
        "status": "success" if dnac_reachable else "warning",
        "device_name": device_name,
        "device_id": telemetry_res.get("device_id"),
        "dnac_reachable": dnac_reachable,
        "alerts_updated": alerts_updated,
        "telemetry": telemetry_res.get("telemetry"),
        "device_info": telemetry_res.get("device_info"),
        "source": telemetry_res.get("source"),
        "timestamp": now_iso,
    }
