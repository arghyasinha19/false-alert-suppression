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
                        return device_id, None
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
                telemetry = {
                    "cpu": raw_health.get("cpu"),
                    "memory": raw_health.get("memory"),
                    "packet_drop": raw_health.get("packet_drop"),
                    "health_score": raw_health.get("health_score"),
                    "interface_error_count": raw_health.get("interface_error_count"),
                    "poe_status": raw_health.get("poe_status"),
                    "uptime_seconds": raw_health.get("uptime_seconds"),
                    "reachable": raw_health.get("reachable", True),
                    "raw_response": raw_health.get("raw_response"),
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
                if cached and cached.get("telemetry"):
                    cached_telemetry = cached.get("telemetry")
                    if isinstance(cached_telemetry, dict):
                        cached_telemetry["reachable"] = False
                    return {
                        "device_name": device_name,
                        "device_id": cached.get("device_id") or device_id,
                        "source": "cached_offline",
                        "timestamp": cached.get("last_updated") or now_iso,
                        "telemetry": cached_telemetry,
                        "device_info": cached.get("device_info") or device_info or default_info,
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
                    )

                    update_filter = {"alert_details.event_id": event_id} if event_id else {"_id": a["_id"]}
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
