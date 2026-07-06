import os, sys

from workflow.state import GraphState
from workflow.tools.backdate_detector import BackdateDetector
from typing import Dict, Any
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

    decision = detector.evaluate(alerts)
    data = {
        "instanceId": decision.instance_id, 
        "device": decision.device_id, 
        "devicename": decision.device_name,
        "is_backdated": decision.is_backdated
    }
    
    # We return ok=True since the agent successfully evaluated the alert
    # The actual business logic outcome is stored in data
    output = {"ok": True, "data": data, "remarks": decision.reason}
    logger.info(f"[{event_id}] Agent 1 completed. Output: {output}")
    return output
