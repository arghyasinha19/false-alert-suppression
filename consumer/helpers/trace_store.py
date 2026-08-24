"""
Lightweight trace event store for consumer-level traceability.

Persists structured trace events to MongoDB `consumer_traces` collection,
capturing each processing stage from RabbitMQ ingestion through Jenkins trigger.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

# Load env from project root
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_current_dir))
load_dotenv(os.path.join(_project_root, ".env"))

logger = logging.getLogger("trace_store")

COLLECTION_NAME = "consumer_traces"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TraceStore:
    """
    Emits structured trace events into MongoDB for consumer-level traceability.

    Each alert gets one document in `consumer_traces` with a `stages` array
    that is appended to via $push as the consumer progresses through stages.
    """

    def __init__(self):
        self.uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.db_name = os.getenv("MONGO_DB_NAME", "false_alert_suppression")
        self.client = None
        self.db = None
        self._connect()

    def _connect(self):
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=3000)
            self.client.admin.command("ping")
            self.db = self.client[self.db_name]
            self._ensure_indexes()
            logger.info("TraceStore connected to MongoDB: %s", self.db_name)
        except ConnectionFailure as e:
            logger.warning("TraceStore: MongoDB not available (%s). Tracing disabled.", e)
            self.db = None

    def _ensure_indexes(self):
        try:
            col = self.db[COLLECTION_NAME]
            col.create_index(
                [("event_id", ASCENDING), ("instance_id", ASCENDING)],
                name="trace_event_instance",
                background=True,
            )
            col.create_index(
                [("started_at", ASCENDING)],
                name="trace_started_at",
                background=True,
            )
        except Exception as e:
            logger.warning("TraceStore: Could not ensure indexes: %s", e)

    def _get_collection(self):
        if self.db is not None:
            return self.db[COLLECTION_NAME]
        return None

    def begin_trace(
        self,
        event_id: str,
        instance_id: Optional[str] = None,
        consumer_type: str = "main",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Create a new trace document for an alert. Returns the trace_id (event_id)
        or None if MongoDB is unavailable.
        """
        col = self._get_collection()
        if col is None:
            return None

        try:
            doc = {
                "event_id": event_id,
                "instance_id": instance_id,
                "consumer_type": consumer_type,
                "started_at": _utc_now(),
                "metadata": metadata or {},
                "stages": [],
                "final_disposition": None,
            }
            col.insert_one(doc)
            logger.debug("TraceStore: began trace for %s", event_id)
            return event_id
        except Exception as e:
            logger.warning("TraceStore: failed to begin trace for %s: %s", event_id, e)
            return None

    def emit(
        self,
        event_id: str,
        stage: str,
        status: str = "success",
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        instance_id: Optional[str] = None,
    ):
        """
        Append a trace stage event to the trace document for this event_id.
        """
        col = self._get_collection()
        if col is None:
            return

        stage_event = {
            "stage": stage,
            "status": status,
            "timestamp": _utc_now(),
            "data": data or {},
        }
        if error:
            stage_event["error"] = error

        try:
            # Match by event_id (and optionally instance_id)
            query = {"event_id": event_id}
            if instance_id:
                query["instance_id"] = instance_id

            col.update_one(
                query,
                {
                    "$push": {"stages": stage_event},
                    "$set": {"updated_at": _utc_now()},
                },
                upsert=False,
            )
            logger.debug("TraceStore: emitted %s for %s", stage, event_id)
        except Exception as e:
            logger.warning("TraceStore: failed to emit %s for %s: %s", stage, event_id, e)

    def set_disposition(
        self,
        event_id: str,
        disposition: str,
        instance_id: Optional[str] = None,
    ):
        """
        Set the final RabbitMQ disposition (acked, nacked, dlq).
        """
        col = self._get_collection()
        if col is None:
            return

        try:
            query = {"event_id": event_id}
            if instance_id:
                query["instance_id"] = instance_id

            col.update_one(
                query,
                {
                    "$set": {
                        "final_disposition": disposition,
                        "completed_at": _utc_now(),
                    }
                },
            )
        except Exception as e:
            logger.warning("TraceStore: failed to set disposition for %s: %s", event_id, e)
