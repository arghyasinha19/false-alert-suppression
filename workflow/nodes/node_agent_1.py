import os, sys

from workflow.state import GraphState
from workflow.tools.backdate_detector import BackdateDetector
from typing import Dict, Any
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

# Detect back dated alerts
def agent_1_logic(state: GraphState) -> Dict[str, Any]:
    """
    Agent 1 is responsible for identifying if an alert is backdated or not
    If an alert is having older dates this agent will flag it.
    """

    alerts = state["alert"]
    event_id = alerts.get("event_id", "UNKNOWN")
    logger.info(f"[{event_id}] Entering Agent 1. Input payload: {alerts}")

    detector = BackdateDetector(
        threshold_minutes=1440, # 24 hours (current day)
        allow_future_skew_seconds=60,
        max_reasonable_age_days=30,
        logger=logger
    )

    # Measure age against when the webhook RECEIVED the alert, not when this
    # job happens to run (a queue backlog would otherwise make fresh alerts
    # look backdated).
    ingestion_time = None
    received_at = alerts.get("received_at")
    if received_at:
        try:
            ingestion_time = datetime.fromisoformat(str(received_at).replace("Z", "+00:00"))
        except ValueError:
            logger.warning(f"[{event_id}] Unparseable received_at={received_at!r}; using current time.")

    decision = detector.evaluate(alerts, ingestion_time=ingestion_time)
    data = {
        "instanceId": decision.instance_id, 
        "device": decision.device_id, 
        "devicename": decision.device_name,
        "is_backdated": decision.is_backdated,
        "backdate_reason": decision.reason,
    }
    
    # We return ok=True since the agent successfully evaluated the alert
    # The actual business logic outcome is stored in data
    output = {"ok": True, "data": data, "remarks": decision.reason}
    logger.info(f"[{event_id}] Agent 1 completed. Output: {output}")
    return output
