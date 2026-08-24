"""
Seed the MongoDB 'alert_results' collection with realistic mock data.
Data structure mirrors what node_reporter.py persists after a workflow run.
"""
import random
import uuid
import json
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "false_alert_suppression"
COLLECTION = "alert_results"

DEVICES = [
    "UK-MAL-DEV-AP02", "Core-Router-01", "Access-Switch-05",
    "Switch-12", "Dist-Router-03", "Core-Switch-02", "US-NY-HQ-AP05",
    "SG-SIN-FW01", "UK-LON-SW01", "US-CHI-RT03", "DE-FRA-AP01", "JP-TKY-SW02",
]

ISSUES = [
    ("AP has flapped", "Wireless AP experienced multiple state transitions"),
    ("BGP Peer is Down", "BGP neighbor adjacency lost"),
    ("High CPU Utilization", "CPU utilization exceeded 90% threshold"),
    ("Interface State Down", "Physical interface went down"),
    ("OSPF Neighbor Down", "OSPF adjacency lost with neighbor"),
    ("High Memory Utilization", "Memory usage exceeded 85% threshold"),
    ("Power Supply Failure", "Redundant power supply unit failure detected"),
    ("AP is Offline", "Access Point is unreachable"),
]

CATEGORIES = ["Auto resolving", "Non-Auto Resolving"]
SEVERITIES = [1, 2, 3]


def generate_alerts(count=50):
    now = datetime.now(timezone.utc)
    alerts = []

    for i in range(count):
        event_id = f"EVT-{str(i + 1).padStart(4, '0') if hasattr(str, 'padStart') else str(i+1).zfill(4)}"
        device = random.choice(DEVICES)
        issue_name, issue_details = random.choice(ISSUES)
        severity = random.choice(SEVERITIES)
        # Spread alerts over the last 7 days
        ts = now - timedelta(hours=random.randint(0, 168), minutes=random.randint(0, 59))
        timestamp_str = ts.isoformat()

        # Decide category
        roll = random.random()
        if roll < 0.15:
            # Backdated alert
            is_backdated = True
            predicted_category = None
        elif roll < 0.55:
            is_backdated = False
            predicted_category = "Auto resolving"
        elif roll < 0.90:
            is_backdated = False
            predicted_category = "Non-Auto Resolving"
        else:
            is_backdated = False
            predicted_category = None  # Uncertain

        # Build results matching safe_node wrapper output
        results = {
            "agent_1": {
                "status": "success",
                "ok": True,
                "data": {"is_backdated": is_backdated},
                "started_at": timestamp_str,
                "ended_at": timestamp_str,
            }
        }

        if not is_backdated and predicted_category:
            confidence = round(random.uniform(0.65, 0.98), 2)
            results["agent_2"] = {
                "status": "success",
                "ok": True,
                "data": {
                    "predicted_category": predicted_category,
                    "confidence": str(confidence),
                },
                "started_at": timestamp_str,
                "ended_at": timestamp_str,
            }

            if predicted_category == "Auto resolving":
                results["agent_3"] = {
                    "status": "success",
                    "ok": True,
                    "data": {"queue_status": "delayed"},
                    "started_at": timestamp_str,
                    "ended_at": timestamp_str,
                }
            elif predicted_category == "Non-Auto Resolving":
                snow_actions = ["incident_created", "comment_appended", "incident_reopened"]
                action = random.choice(snow_actions)
                inc_number = f"INC00{random.randint(10000, 99999)}"
                results["agent_4"] = {
                    "status": "success",
                    "ok": True,
                    "data": {"action": action, "incident": inc_number},
                    "started_at": timestamp_str,
                    "ended_at": timestamp_str,
                }
        elif not is_backdated:
            # Uncertain — agent_2 ran but no clear category
            results["agent_2"] = {
                "status": "success",
                "ok": True,
                "data": {
                    "predicted_category": "Uncertain",
                    "confidence": str(round(random.uniform(0.30, 0.55), 2)),
                },
                "started_at": timestamp_str,
                "ended_at": timestamp_str,
            }

        alert_details = {
            "event_id": event_id,
            "instance_id": str(uuid.uuid4()),
            "device_name": device,
            "device_id": f"dev-{DEVICES.index(device) + 1:03d}",
            "severity": severity,
            "category": "ERROR" if severity <= 1 else "WARN",
            "status": random.choice(["active", "active", "active", "resolved"]),
            "raw_timestamp": timestamp_str,
            "issue_name": issue_name,
            "issue_details": f"{issue_details} on {device}",
            "source": "DNAC",
        }

        doc = {
            "alert_id": event_id,
            "results": results,
            "runtime_error": None,
            "alert_details": alert_details,
        }
        alerts.append(doc)

    return alerts


def main():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION]

    # Clear existing mock data
    deleted = collection.delete_many({})
    print(f"Cleared {deleted.deleted_count} existing documents from '{COLLECTION}'.")

    alerts = generate_alerts(50)

    for doc in alerts:
        collection.update_one(
            {
                "alert_id": doc["alert_id"],
                "alert_details.instance_id": doc["alert_details"].get("instance_id"),
                "alert_details.device_id": doc["alert_details"].get("device_id"),
                "alert_details.raw_timestamp": doc["alert_details"].get("raw_timestamp"),
            },
            {"$set": doc},
            upsert=True,
        )

    final_count = collection.count_documents({})
    print(f"Inserted {len(alerts)} mock alerts. Collection now has {final_count} documents.")

    # Print a sample
    sample = collection.find_one({}, {"_id": 0})
    print(f"\nSample document:\n{json.dumps(sample, indent=2, default=str)}")


if __name__ == "__main__":
    main()
