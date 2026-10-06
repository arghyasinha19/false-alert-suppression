import os
import yaml
import logging
from typing import Dict, Any
from workflow.state import GraphState
from workflow.tools.message_broker import RabbitMQBroker
from workflow.utils.helpers import result_data

logger = logging.getLogger(__name__)


def agent_3_scheduler(state: GraphState) -> Dict[str, Any]:
    """
    Agent 3 (Scheduler): pushes 'Auto resolving' alerts to the delayed queue
    so they are re-checked against DNAC after the wait period.

    If scheduling fails this returns ok=False with
    ``data.queue_status == "failed"``; Agent 4 then escalates the alert to
    ServiceNow immediately instead of dropping it.
    """
    alert = state.get("alert", {})
    event_id = alert.get("event_id", "UNKNOWN")
    logger.info(f"[{event_id}] Entering Agent 3. Scheduling delay...")

    predicted_category = result_data(state, "agent_2").get("predicted_category")

    if predicted_category != "Auto resolving":
        output = {
            "ok": True,
            "status": "skipped",
            "data": {"queue_status": "not_scheduled"},
            "remarks": f"Not auto-resolving (predicted: {predicted_category}). Skipping scheduler."
        }
        logger.info(f"[{event_id}] Agent 3 completed. Output: {output}")
        return output

    try:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config.yaml",
        )
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        broker = RabbitMQBroker(config.get("rabbitmq", {}))
        success = broker.publish_delayed_message(alert)

        if success:
            output = {
                "ok": True,
                "data": {"queue_status": "delayed"},
                "remarks": "Payload successfully published to wait.q"
            }
        else:
            output = {
                "ok": False,
                "data": {"queue_status": "failed"},
                "remarks": "Failed to schedule delayed check - alert will be escalated immediately."
            }
        logger.info(f"[{event_id}] Agent 3 completed. Output: {output}")
        return output

    except Exception as e:
        logger.error(f"[{event_id}] Agent 3 failed to publish payload: {e}", exc_info=True)
        return {
            "ok": False,
            "data": {"queue_status": "failed"},
            "remarks": f"error: {str(e)} - alert will be escalated immediately."
        }
