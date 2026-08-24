"""
DNAC Background Sync Service
=============================
Runs as a standalone process alongside the dashboard API.
Every 60 seconds, queries MongoDB for alerts that may still be active,
checks their live status against DNAC, and writes the result back to MongoDB.

Usage:
    python dnac_sync.py
    python dnac_sync.py --interval 30   # Override default 60s interval
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime, timezone
from collections import defaultdict

# Ensure project root is in sys.path
dashboard_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(dashboard_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if dashboard_dir not in sys.path:
    sys.path.insert(0, dashboard_dir)

from workflow.tools.mongodb_client import MongoDBClient
from dnac_monitor import check_dashboard_dnac_status

# ── Logging ──────────────────────────────────────────────────────────
log_dir = os.path.join(project_root, "logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "dnac_sync.log")),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("DNACSync")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_sync_cycle(collection) -> dict:
    """
    Execute one sync cycle:
    1. Find alerts that are not backdated and not already marked RESOLVED.
    2. Group by instance_id to avoid redundant DNAC API calls.
    3. Check DNAC status for each unique instance.
    4. Write results back to MongoDB.

    Returns a summary dict with counts.
    """
    # 1. Query for alerts that might still be active
    query = {
        "results.agent_1.data.is_backdated": {"$ne": True},
        "$or": [
            {"dnac_live_status": {"$exists": False}},
            {"dnac_live_status": {"$nin": ["RESOLVED"]}},
        ],
    }

    try:
        alerts = list(collection.find(query, {
            "_id": 1,
            "alert_details.instance_id": 1,
            "alert_details.device_id": 1,
            "alert_details.device_name": 1,
            "alert_details.device": 1,
            "alert_details.event_id": 1,
            "alert_details.issue_name": 1,
            "alert_details.issue_details": 1,
        }))
    except Exception as e:
        logger.error(f"Failed to query MongoDB: {e}")
        return {"error": str(e), "checked": 0, "updated": 0}

    if not alerts:
        logger.info("No non-resolved alerts found. Nothing to sync.")
        return {"checked": 0, "updated": 0, "skipped": 0}

    # 2. Group by instance_id (or device_name + issue_name if no instance_id)
    instance_groups = defaultdict(list)
    for a in alerts:
        details = a.get("alert_details", {})
        instance_id = details.get("instance_id") or ""
        device_name = details.get("device_name") or details.get("device") or ""
        issue_name = details.get("issue_name") or ""
        # Create a grouping key
        group_key = instance_id if instance_id else f"{device_name}::{issue_name}"
        instance_groups[group_key].append(a)

    logger.info(
        f"Found {len(alerts)} non-resolved alerts in {len(instance_groups)} unique groups."
    )

    checked = 0
    updated = 0
    errors = 0

    # 3. For each unique group, check DNAC status
    for group_key, group_alerts in instance_groups.items():
        # Take representative alert details from the first alert in the group
        rep = group_alerts[0].get("alert_details", {})
        instance_id = rep.get("instance_id")
        device_id = rep.get("device_id")
        device_name = rep.get("device_name") or rep.get("device")
        event_id = rep.get("event_id")
        issue_name = rep.get("issue_name")
        issue_details = rep.get("issue_details")

        try:
            dnac_status = check_dashboard_dnac_status(
                instance_id=instance_id,
                device_id=device_id,
                device_name=device_name,
                issue_name=issue_name,
                issue_details=issue_details,
                event_id=event_id,
            )
            checked += 1

            logger.info(
                f"  [{group_key}] -> {dnac_status} "
                f"(device={device_name}, instance_id={instance_id})"
            )

            # 4. Update all alerts in this group
            doc_ids = [a["_id"] for a in group_alerts]
            result = collection.update_many(
                {"_id": {"$in": doc_ids}},
                {
                    "$set": {
                        "dnac_live_status": dnac_status,
                        "dnac_last_checked": utc_now_iso(),
                    }
                },
            )
            updated += result.modified_count

        except Exception as e:
            errors += 1
            logger.error(
                f"  [{group_key}] DNAC check failed: {e}"
            )

    summary = {
        "checked": checked,
        "updated": updated,
        "errors": errors,
        "total_alerts": len(alerts),
        "unique_groups": len(instance_groups),
    }
    logger.info(f"Sync cycle complete: {summary}")
    return summary


def main():
    parser = argparse.ArgumentParser(description="DNAC Background Sync Service")
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Polling interval in seconds (default: 60)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single sync cycle and exit (useful for testing)",
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("DNAC Background Sync Service starting")
    logger.info(f"  Polling interval: {args.interval}s")
    logger.info(f"  One-shot mode: {args.once}")
    logger.info("=" * 60)

    # Connect to MongoDB
    try:
        mongo = MongoDBClient()
        collection = mongo.get_collection("alert_results")
        if collection is None:
            logger.error("Failed to get MongoDB collection. Exiting.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        sys.exit(1)

    if args.once:
        run_sync_cycle(collection)
        return

    # Continuous loop
    cycle = 0
    while True:
        cycle += 1
        logger.info(f"--- Sync cycle #{cycle} ---")
        try:
            run_sync_cycle(collection)
        except Exception as e:
            logger.error(f"Unexpected error in sync cycle: {e}", exc_info=True)

        logger.info(f"Sleeping {args.interval}s until next cycle...")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
