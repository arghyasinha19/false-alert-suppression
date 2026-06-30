import os
import yaml
import logging
from typing import Dict, Any
from workflow.state import GraphState
from workflow.tools.message_broker import RabbitMQBroker

logger = logging.getLogger(__name__)

def agent_3_scheduler(state: GraphState) -> Dict[str, Any]:
    """
    Agent 3 (Scheduler): Intercepts 'Auto resolving' alerts and pushes them to a delayed queue.
    """
    alert = state.get("alert", {})
    event_id = alert.get("event_id", "UNKNOWN")
    logger.info(f"[{event_id}] Entering Agent 3. Scheduling delay...")
    
    agent2_result = state.get("results", {}).get("agent_2", {})
    predicted_category = agent2_result.get("data", {}).get("predicted_category")
    
    if predicted_category != "Auto resolving":
        output = {
            "ok": True,
            "data": None,
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
            
        rmq_config = config.get("rabbitmq", {})
        broker = RabbitMQBroker(rmq_config)
        
        # The user requested to push the entire payload into the queue
        payload = state.get("alert", {})
        
        success = broker.publish_delayed_message(payload)
        
        if success:
            output = {
                "ok": True,
                "data": {"queue_status": "delayed"},
                "remarks": "Payload successfully published to wait.q"
            }
            logger.info(f"[{event_id}] Agent 3 completed. Output: {output}")
            return output
        else:
            output = {
                "ok": False,
                "data": {"queue_status": "failed"},
                "remarks": "Failed to schedule delayed check. Check broker connection."
            }
            logger.info(f"[{event_id}] Agent 3 completed. Output: {output}")
            return output
            
    except Exception as e:
        logger.error(f"[{event_id}] Agent 3 Failed to publish payload: {e}")
        output = {
            "ok": False,
            "data": None,
            "remarks": f"error: {str(e)}"
        }