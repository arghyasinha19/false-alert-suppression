import os
import uuid
import time
import logging
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path=env_path)

class MongoDBClient:
    def __init__(self):
        self.uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.db_name = os.getenv("MONGO_DB_NAME", "false_alert_suppression")
        self.client = None
        self.db = None
        self._connect()
        
    def _connect(self):
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            # Verify the connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            logger.info(f"Successfully connected to MongoDB database: {self.db_name}")
            self._ensure_indexes()
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB at {self.uri}: {e}")

    def _ensure_indexes(self):
        """Ensure compound index on the composite dedup key for query performance."""
        try:
            collection = self.get_collection("alert_results")
            if collection is not None:
                # 1. Clean up legacy single-field unique index if it exists
                try:
                    existing_indexes = collection.index_information()
                    if "alert_id_1" in existing_indexes and existing_indexes["alert_id_1"].get("unique"):
                        collection.drop_index("alert_id_1")
                        logger.info("Dropped legacy unique index alert_id_1.")
                    if "dedup_composite_key" in existing_indexes and existing_indexes["dedup_composite_key"].get("unique"):
                        # If existing index is unique, drop and re-create without unique constraint
                        # to prevent DuplicateKeyError crashes on missing/null fields
                        collection.drop_index("dedup_composite_key")
                        logger.info("Dropped legacy unique dedup_composite_key index.")
                except Exception as ex:
                    logger.warning(f"Could not check/drop legacy index: {ex}")

                # 2. Ensure compound dedup index for query performance
                collection.create_index(
                    [
                        ("alert_id", 1),
                        ("alert_details.instance_id", 1),
                        ("alert_details.device_id", 1),
                        ("alert_details.raw_timestamp", 1),
                    ],
                    name="dedup_composite_key",
                    background=True,
                )
                logger.info("Ensured compound dedup index on alert_results.")
        except Exception as e:
            # Non-fatal: index may already exist or collection may not yet exist
            logger.warning(f"Could not ensure dedup index: {e}")

    def get_collection(self, collection_name: str):
        if self.db is None:
            self._connect()
        if self.db is not None:
            return self.db[collection_name]
        return None
        
    def save_alert_result(self, alert_id: str, payload: dict):
        """Save or update the final execution state of an alert.

        Uses a composite key (event_id + instance_id + device_id + raw_timestamp)
        so only truly identical alerts are deduplicated. Different occurrences
        of the same alert type (same event_id but different instance_id or
        timestamp) are stored as separate documents.
        """
        collection = self.get_collection("alert_results")
        if collection is not None:
            try:
                # Ensure top-level alert_id is set
                payload.setdefault("alert_id", alert_id)

                # Build composite dedup filter from alert_details in payload
                alert_details = payload.setdefault("alert_details", {})

                # Ensure alert has a non-null instance_id
                instance_id = alert_details.get("instance_id")
                if not instance_id:
                    instance_id = f"inst-{uuid.uuid4().hex[:12]}"
                    alert_details["instance_id"] = instance_id

                # Ensure alert has non-null timestamps
                raw_ts = alert_details.get("raw_timestamp")
                if not raw_ts:
                    raw_ts = int(time.time() * 1000)
                    alert_details["raw_timestamp"] = raw_ts

                if not alert_details.get("timestamp"):
                    alert_details["timestamp"] = datetime.now(timezone.utc).isoformat()

                device_id = alert_details.get("device_id")

                dedup_filter = {
                    "alert_id": alert_id,
                    "alert_details.instance_id": instance_id,
                    "alert_details.device_id": device_id,
                    "alert_details.raw_timestamp": raw_ts,
                }
                collection.update_one(
                    dedup_filter,
                    {"$set": payload},
                    upsert=True
                )
                logger.info(f"Saved alert {alert_id} (instance: {instance_id}) to MongoDB.")
                return True
            except Exception as e:
                logger.error(f"Failed to save alert {alert_id} to MongoDB: {e}")
                return False
        return False
