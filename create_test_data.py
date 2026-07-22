import os
from pymongo import MongoClient
from datetime import datetime, timezone

uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
db_name = os.getenv("MONGO_DB_NAME", "false_alert_suppression")

client = MongoClient(uri, serverSelectionTimeoutMS=5000)
db = client[db_name]
collection = db["alert_results"]

# Clear old entries to keep a clean customer presentation
collection.delete_many({})

now_str = datetime.now(timezone.utc).isoformat()

test_alerts = [
    # 1. Backdated Alert
    {
        "alert_id": "EVT-BACKDATED-001",
        "alert_details": {
            "instance_id": "alert-backdated-ap-flap",
            "event_id": "EVT-BACKDATED-001",
            "device_id": "dev-001",
            "device_name": "UK-MAL-DEV-AP02",
            "severity": 3,
            "category": "WARN",
            "status": "active",
            "timestamp": now_str,
            "raw_timestamp": now_str,
            "issue_name": "AP UK-MAL-DEV-AP02 has flapped",
            "issue_details": "AP UK-MAL-DEV-AP02 has flapped"
        },
        "results": {
            "agent_1": {
                "status": "success",
                "ok": True,
                "data": {
                    "is_backdated": True
                },
                "ended_at": now_str
            }
        },
        "runtime_error": None
    },
    # 2. Auto-Resolving Alert
    {
        "alert_id": "EVT-AUTORES-002",
        "alert_details": {
            "instance_id": "alert-autores-cpu",
            "event_id": "EVT-AUTORES-002",
            "device_id": "dev-003",
            "device_name": "Access-Switch-05",
            "severity": 2,
            "category": "WARN",
            "status": "active",
            "timestamp": now_str,
            "raw_timestamp": now_str,
            "issue_name": "High CPU Utilization",
            "issue_details": "Device Access-Switch-05 CPU utilization is at 95%"
        },
        "results": {
            "agent_1": {
                "status": "success",
                "ok": True,
                "data": {
                    "is_backdated": False
                },
                "ended_at": now_str
            },
            "agent_2": {
                "status": "success",
                "ok": True,
                "data": {
                    "predicted_category": "Auto resolving",
                    "confidence": 0.92
                },
                "ended_at": now_str
            },
            "agent_3": {
                "status": "success",
                "ok": True,
                "data": {
                    "queue_status": "delayed"
                },
                "ended_at": now_str
            }
        },
        "runtime_error": None
    },
    # 3. Non-Auto-Resolving Alert (escalated to ServiceNow)
    {
        "alert_id": "EVT-GENUINE-003",
        "alert_details": {
            "instance_id": "alert-genuine-bgp",
            "event_id": "EVT-GENUINE-003",
            "device_id": "dev-002",
            "device_name": "Core-Router-01",
            "severity": 1,
            "category": "ERROR",
            "status": "active",
            "timestamp": now_str,
            "raw_timestamp": now_str,
            "issue_name": "BGP Peer is Down",
            "issue_details": "BGP peer 10.0.0.1 on Core-Router-01 is down"
        },
        "results": {
            "agent_1": {
                "status": "success",
                "ok": True,
                "data": {
                    "is_backdated": False
                },
                "ended_at": now_str
            },
            "agent_2": {
                "status": "success",
                "ok": True,
                "data": {
                    "predicted_category": "Non-Auto Resolving",
                    "confidence": 0.88
                },
                "ended_at": now_str
            },
            "agent_4": {
                "status": "success",
                "ok": True,
                "data": {
                    "action": "incident_created",
                    "incident": "INC0049281"
                },
                "ended_at": now_str
            }
        },
        "runtime_error": None
    }
]

collection.insert_many(test_alerts)
print(f"Successfully inserted {len(test_alerts)} real-device test documents into MongoDB!")
