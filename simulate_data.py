"""
Simulate realistic alert data for the False Alert Suppression pipeline.
Generates alert records matching the exact LangGraph pipeline schema
and saves them to data/simulated_alerts.json.
Also attempts to seed MongoDB if available.
"""
import os
import sys
import json
import random
import uuid
from datetime import datetime, timezone, timedelta

# Ensure root dir is in path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

DATA_DIR = os.path.join(project_root, "data")
SIMULATED_FILE = os.path.join(DATA_DIR, "simulated_alerts.json")

DEVICES = [
    {"name": "UK-MAL-DEV-AP02", "id": "dev-001", "location": "UK-MAL"},
    {"name": "Core-Router-01", "id": "dev-002", "location": "US-NY"},
    {"name": "Access-Switch-05", "id": "dev-003", "location": "UK-LON"},
    {"name": "Switch-12", "id": "dev-004", "location": "SG-SIN"},
    {"name": "Dist-Router-03", "id": "dev-005", "location": "DE-FRA"},
    {"name": "Core-Switch-02", "id": "dev-006", "location": "US-CHI"},
    {"name": "US-NY-HQ-AP05", "id": "dev-007", "location": "US-NY"},
    {"name": "SG-SIN-FW01", "id": "dev-008", "location": "SG-SIN"},
    {"name": "UK-LON-SW01", "id": "dev-009", "location": "UK-LON"},
    {"name": "US-CHI-RT03", "id": "dev-010", "location": "US-CHI"},
    {"name": "DE-FRA-AP01", "id": "dev-011", "location": "DE-FRA"},
    {"name": "JP-TKY-SW02", "id": "dev-012", "location": "JP-TKY"},
]

ISSUES = [
    ("AP has flapped", "Wireless AP experienced multiple rapid state transitions", 3, "WARN"),
    ("BGP Peer is Down", "BGP neighbor adjacency lost on interface GigabitEthernet0/0/1", 1, "ERROR"),
    ("High CPU Utilization", "Device CPU utilization exceeded 92% sustained threshold", 2, "WARN"),
    ("Interface State Down", "Physical link down on TenGigabitEthernet1/1/2", 1, "ERROR"),
    ("OSPF Neighbor Down", "OSPF adjacency lost with neighbor router 10.200.1.5", 2, "WARN"),
    ("High Memory Utilization", "System memory usage reached 88% capacity", 2, "WARN"),
    ("Power Supply Failure", "Redundant power supply unit 2 reported hardware fault", 1, "ERROR"),
    ("AP is Offline", "Access Point unreachable via CAPWAP tunnel", 3, "WARN"),
    ("Fan Tray Warning", "Chassis cooling fan tray operating at degraded RPM", 3, "WARN"),
    ("CRC Error Threshold Exceeded", "Input CRC errors exceeded 100 per minute on Gi0/1/4", 3, "WARN"),
]

def generate_simulated_alerts(count=60):
    now = datetime.now(timezone.utc)
    alerts = []

    for i in range(count):
        evt_id = f"EVT-{i + 1:04d}"
        inst_id = f"inst-{uuid.uuid4().hex[:12]}"
        device = random.choice(DEVICES)
        issue_name, issue_desc, severity, category = random.choice(ISSUES)

        # Spread timestamps over the last 7 days with recency weighting
        hours_ago = random.choices(
            [random.uniform(0, 12), random.uniform(12, 48), random.uniform(48, 168)],
            weights=[0.5, 0.3, 0.2]
        )[0]
        alert_time = now - timedelta(hours=hours_ago)
        alert_time_str = alert_time.isoformat()
        alert_time_ms = int(alert_time.timestamp() * 1000)

        # Categorization probabilities:
        # ~18% Backdated (Agent 1 suppresses)
        # ~42% Auto-Resolving (Agent 2 predicts Auto-resolving, Agent 3 suppresses to DLX)
        # ~32% Non-Auto-Resolving (Agent 2 predicts Non-Auto, Agent 4 creates/updates SNOW incident)
        # ~8% Uncertain
        roll = random.random()
        if roll < 0.18:
            is_backdated = True
            predicted_cat = None
            action = None
            snow_inc = None
            live_status = None
            overall_status = "suppressed"
            status_desc = "Suppressed by Agent 1 (Backdated)"
        elif roll < 0.60:
            is_backdated = False
            predicted_cat = "Auto resolving"
            action = None
            snow_inc = None
            live_status = None
            overall_status = "suppressed"
            status_desc = "Suppressed by Agent 2 & 3 (Auto-Resolving / DLX Queue)"
        elif roll < 0.92:
            is_backdated = False
            predicted_cat = "Non-Auto Resolving"
            action = random.choice(["incident_created", "comment_appended", "incident_reopened"])
            snow_inc = f"INC00{random.randint(12000, 99000)}"
            live_status = random.choice(["New", "In Progress", "In Progress", "Awaiting Info", "Resolved"])
            overall_status = "escalated"
            status_desc = f"Escalated by Agent 4 -> ServiceNow {snow_inc}"
        else:
            is_backdated = False
            predicted_cat = "Uncertain"
            action = None
            snow_inc = None
            live_status = None
            overall_status = "uncertain"
            status_desc = "Flagged by Agent 2 as Uncertain (<60% confidence)"

        results = {
            "agent_1": {
                "status": "success",
                "ok": True,
                "data": {"is_backdated": is_backdated},
                "started_at": alert_time_str,
                "ended_at": alert_time_str,
            }
        }

        if not is_backdated and predicted_cat != "Uncertain":
            confidence = round(random.uniform(0.72, 0.99), 2)
            results["agent_2"] = {
                "status": "success",
                "ok": True,
                "data": {
                    "predicted_category": predicted_cat,
                    "confidence": str(confidence),
                },
                "started_at": alert_time_str,
                "ended_at": alert_time_str,
            }

            if predicted_cat == "Auto resolving":
                results["agent_3"] = {
                    "status": "success",
                    "ok": True,
                    "data": {
                        "queue_status": "delayed",
                        "wait_queue": "dnac.alerts.wait.q",
                        "delay_ms": 900000,
                    },
                    "started_at": alert_time_str,
                    "ended_at": alert_time_str,
                }
            elif predicted_cat == "Non-Auto Resolving":
                results["agent_4"] = {
                    "status": "success",
                    "ok": True,
                    "data": {
                        "action": action,
                        "incident": snow_inc,
                        "assigned_group": "Network-Ops-L2",
                    },
                    "started_at": alert_time_str,
                    "ended_at": alert_time_str,
                }
        elif not is_backdated:
            confidence = round(random.uniform(0.35, 0.58), 2)
            results["agent_2"] = {
                "status": "success",
                "ok": True,
                "data": {
                    "predicted_category": "Uncertain",
                    "confidence": str(confidence),
                },
                "started_at": alert_time_str,
                "ended_at": alert_time_str,
            }

        # DNAC live check status
        dnac_live_status = "RESOLVED" if (is_backdated or predicted_cat == "Auto resolving" or random.random() < 0.25) else "ACTIVE"

        alert_details = {
            "event_id": evt_id,
            "instance_id": inst_id,
            "device_name": device["name"],
            "device_id": device["id"],
            "severity": severity,
            "category": category,
            "status": "resolved" if dnac_live_status == "RESOLVED" else "active",
            "timestamp": alert_time_str,
            "raw_timestamp": alert_time_ms,
            "issue_name": issue_name,
            "issue_details": f"{issue_desc} on {device['name']}",
            "source": "DNAC",
            "location": device["location"],
        }

        doc = {
            "alert_id": evt_id,
            "results": results,
            "runtime_error": None,
            "alert_details": alert_details,
            "dnac_live_status": dnac_live_status,
            "dnac_last_checked": alert_time_str,
            "live_snow_status": live_status,
            "overall_status": overall_status,
            "status_description": status_desc,
        }
        alerts.append(doc)

    # Sort descending by timestamp
    alerts.sort(key=lambda a: a["alert_details"]["raw_timestamp"], reverse=True)
    return alerts


def save_simulated_alerts(alerts, append=False):
    os.makedirs(DATA_DIR, exist_ok=True)
    existing = []
    if append and os.path.exists(SIMULATED_FILE):
        try:
            with open(SIMULATED_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []

    combined = alerts + existing
    # Deduplicate by alert_id
    seen = set()
    deduped = []
    for a in combined:
        aid = a.get("alert_id")
        if aid not in seen:
            seen.add(aid)
            deduped.append(a)

    with open(SIMULATED_FILE, "w", encoding="utf-8") as f:
        json.dump(deduped, f, indent=2, default=str)

    print(f"Saved {len(deduped)} simulated alerts to {SIMULATED_FILE}")

    # Also try to insert into MongoDB if MongoDB is running
    try:
        from workflow.tools.mongodb_client import MongoDBClient
        client = MongoDBClient()
        collection = client.get_collection("alert_results")
        if collection is not None:
            for doc in alerts:
                collection.update_one(
                    {"alert_id": doc["alert_id"]},
                    {"$set": doc},
                    upsert=True,
                )
            print(f"Also synchronized {len(alerts)} alerts to MongoDB 'alert_results' collection.")
    except Exception as e:
        # MongoDB unavailable, that's completely fine
        pass

    return deduped


if __name__ == "__main__":
    count = 60
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        count = int(sys.argv[1])
    print(f"Generating {count} simulated alerts...")
    alerts = generate_simulated_alerts(count)
    save_simulated_alerts(alerts)
