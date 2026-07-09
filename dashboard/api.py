import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime, timezone, timedelta

# Ensure root dir in path to import MongoDBClient
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from workflow.tools.mongodb_client import MongoDBClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DashboardAPI")

app = FastAPI(title="False Alert Suppression API")

# Allow Vite React app to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mongo = MongoDBClient()


@app.get("/api/alerts")
def get_alerts():
    """Fetch all processed alerts from MongoDB."""
    collection = mongo.get_collection("alert_results")
    if collection is None:
        return {"error": "MongoDB not connected", "alerts": []}

    try:
        # Fetch all, omitting the internal MongoDB _id
        alerts = list(collection.find({}, {"_id": 0}))

        # Extract unique incident numbers
        incident_numbers = set()
        for a in alerts:
            inc = a.get("results", {}).get("agent_4", {}).get("data", {}).get("incident")
            if inc and inc != "Unknown":
                incident_numbers.add(inc)

        # Bulk fetch live statuses from ServiceNow
        snow_statuses = {}
        if incident_numbers:
            from workflow.tools.servicenow_client import ServiceNowClient
            snow_client = ServiceNowClient()
            snow_statuses = snow_client.get_incidents_by_numbers(list(incident_numbers))

        # Enrich the alerts with the live status
        for a in alerts:
            inc = a.get("results", {}).get("agent_4", {}).get("data", {}).get("incident")
            if inc in snow_statuses:
                a["live_snow_status"] = snow_statuses[inc]

        return {"alerts": alerts}
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        return {"error": str(e), "alerts": []}


@app.get("/api/devices")
def get_devices():
    """
    Return a unique list of devices with aggregated stats:
    latest status, total alert count, location (derived from name), active alerts, etc.
    """
    collection = mongo.get_collection("alert_results")
    if collection is None:
        return {"devices": []}

    try:
        alerts = list(collection.find({}, {"_id": 0}))
        device_map = {}

        for a in alerts:
            details = a.get("alert_details", {})
            name = details.get("device_name") or details.get("device") or "Unknown"

            if name not in device_map:
                device_map[name] = {
                    "device_name": name,
                    "device_id": details.get("device_id", ""),
                    "location": _derive_location(name),
                    "total_alerts": 0,
                    "backdated": 0,
                    "auto_resolving": 0,
                    "non_auto_resolving": 0,
                    "snow_incidents": 0,
                    "last_alert_time": None,
                    "active_alerts": [],
                }

            entry = device_map[name]
            entry["total_alerts"] += 1

            is_backdated = a.get("results", {}).get("agent_1", {}).get("data", {}).get("is_backdated", False)
            predicted = a.get("results", {}).get("agent_2", {}).get("data", {}).get("predicted_category", "")

            if is_backdated:
                entry["backdated"] += 1
            elif predicted == "Auto resolving":
                entry["auto_resolving"] += 1
            elif predicted == "Non-Auto Resolving":
                entry["non_auto_resolving"] += 1

            snow_action = a.get("results", {}).get("agent_4", {}).get("data", {}).get("action")
            if snow_action and "created" in str(snow_action):
                entry["snow_incidents"] += 1

            ts = details.get("timestamp") or details.get("raw_timestamp")
            if ts:
                entry["last_alert_time"] = ts

            # Collect active alerts for NOC view
            status_str = details.get("status", "")
            if str(status_str).lower() == "active" or not is_backdated:
                entry["active_alerts"].append({
                    "event_id": details.get("event_id"),
                    "severity": details.get("severity"),
                    "issue_name": details.get("issue_name"),
                    "issue_details": details.get("issue_details"),
                    "category": details.get("category"),
                    "timestamp": ts,
                    "predicted_category": predicted if not is_backdated else "Backdated",
                    "snow_incident": a.get("results", {}).get("agent_4", {}).get("data", {}).get("incident"),
                    "snow_action": snow_action,
                })

        devices = list(device_map.values())
        return {"devices": devices}
    except Exception as e:
        logger.error(f"Error fetching devices: {e}")
        return {"devices": []}


@app.get("/api/device/{device_name}/history")
def get_device_history(device_name: str):
    """Return all historical alert records for a specific device."""
    collection = mongo.get_collection("alert_results")
    if collection is None:
        return {"alerts": []}

    try:
        # Query by device_name in alert_details
        query = {
            "$or": [
                {"alert_details.device_name": device_name},
                {"alert_details.device": device_name},
            ]
        }
        alerts = list(collection.find(query, {"_id": 0}).sort("alert_details.timestamp", -1))
        return {"device_name": device_name, "alerts": alerts}
    except Exception as e:
        logger.error(f"Error fetching history for {device_name}: {e}")
        return {"device_name": device_name, "alerts": []}


@app.get("/api/kpi/summary")
def get_kpi_summary():
    """
    Pre-computed aggregate KPIs for the dashboard:
    suppression rates, category volumes, hourly distribution, etc.
    """
    collection = mongo.get_collection("alert_results")
    if collection is None:
        return {"kpi": {}}

    try:
        alerts = list(collection.find({}, {"_id": 0}))
        total = len(alerts)

        backdated = 0
        auto_resolving = 0
        non_auto_resolving = 0
        uncertain = 0
        snow_created = 0
        snow_appended = 0
        snow_reopened = 0
        delayed_resolved = 0

        hourly_buckets = {}
        daily_buckets = {}
        device_counts = {}

        for a in alerts:
            details = a.get("alert_details", {})
            results = a.get("results", {})

            is_bd = results.get("agent_1", {}).get("data", {}).get("is_backdated", False)
            predicted = results.get("agent_2", {}).get("data", {}).get("predicted_category", "")
            snow_action = results.get("agent_4", {}).get("data", {}).get("action", "")

            if is_bd:
                backdated += 1
                cat = "Backdated"
            elif predicted == "Auto resolving":
                auto_resolving += 1
                cat = "Auto Resolving"
            elif predicted == "Non-Auto Resolving":
                non_auto_resolving += 1
                cat = "Non-Auto Resolving"
            else:
                uncertain += 1
                cat = "Uncertain"

            if snow_action == "incident_created":
                snow_created += 1
            elif snow_action == "comment_appended":
                snow_appended += 1
            elif snow_action == "incident_reopened":
                snow_reopened += 1

            delayed_status = results.get("delayed_check", {}).get("status", "")
            if delayed_status == "resolved":
                delayed_resolved += 1

            # Time bucketing
            ts = details.get("timestamp") or details.get("raw_timestamp")
            if ts:
                try:
                    if isinstance(ts, (int, float)):
                        if ts > 1e12:
                            dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
                        else:
                            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                    else:
                        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))

                    hour_key = dt.strftime("%Y-%m-%d %H:00")
                    day_key = dt.strftime("%Y-%m-%d")

                    hourly_buckets.setdefault(hour_key, {"Backdated": 0, "Auto Resolving": 0, "Non-Auto Resolving": 0, "Uncertain": 0})
                    hourly_buckets[hour_key][cat] += 1

                    daily_buckets.setdefault(day_key, {"Backdated": 0, "Auto Resolving": 0, "Non-Auto Resolving": 0, "Uncertain": 0})
                    daily_buckets[day_key][cat] += 1
                except Exception:
                    pass

            device = details.get("device_name") or details.get("device") or "Unknown"
            device_counts[device] = device_counts.get(device, 0) + 1

        suppression_rate = round(((backdated + auto_resolving) / total * 100), 1) if total > 0 else 0
        tickets_avoided = backdated + auto_resolving + delayed_resolved

        # Sort and format time series
        hourly_series = [{"time": k, **v} for k, v in sorted(hourly_buckets.items())]
        daily_series = [{"date": k, **v} for k, v in sorted(daily_buckets.items())]
        top_devices = sorted(device_counts.items(), key=lambda x: x[1], reverse=True)[:20]

        return {
            "kpi": {
                "total_alerts": total,
                "backdated": backdated,
                "auto_resolving": auto_resolving,
                "non_auto_resolving": non_auto_resolving,
                "uncertain": uncertain,
                "suppression_rate": suppression_rate,
                "snow_tickets_created": snow_created,
                "snow_comments_appended": snow_appended,
                "snow_incidents_reopened": snow_reopened,
                "tickets_avoided": tickets_avoided,
                "delayed_resolved": delayed_resolved,
                "hourly_series": hourly_series,
                "daily_series": daily_series,
                "top_devices": [{"device": d, "count": c} for d, c in top_devices],
            }
        }
    except Exception as e:
        logger.error(f"Error computing KPI summary: {e}")
        return {"kpi": {}}


def _derive_location(device_name: str) -> str:
    """
    Derive a location label from the device naming convention.
    e.g. UK-LON-SW01 -> UK-LON, US-NY-RT02 -> US-NY, SG-SIN-FW01 -> SG-SIN
    """
    if not device_name or device_name == "Unknown":
        return "Unknown"

    parts = device_name.split("-")
    if len(parts) >= 2:
        return f"{parts[0]}-{parts[1]}"
    return parts[0] if parts else "Unknown"
