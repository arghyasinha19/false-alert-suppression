import os
import yaml
import logging
import json
from typing import Dict, Any
from workflow.state import GraphState
from workflow.tools.email_client import EmailClient

logger = logging.getLogger(__name__)

def email_notifier(state: GraphState) -> GraphState:
    """
    Evaluates the GraphState and sends email notifications to the DL if configured
    conditions are met (backdated, auto-resolved, or pushed to SNOW).
    """
    alert = state.get("alert", {})
    event_id = alert.get("event_id", "UNKNOWN")
    logger.info(f"[{event_id}] Entering Email Notifier node.")
    
    try:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config.yaml",
        )
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            
        email_config = config.get("email_notifications", {})
        
        if not email_config.get("enabled"):
            logger.info(f"[{event_id}] Email notifications disabled globally.")
            return state
            
        client = EmailClient(email_config)
        results = state.get("results", {})
        
        # Condition 1: Backdated alert is suppressed
        # Checked via agent_2 reason when skipped
        agent_2 = results.get("agent_2", {})
        if agent_2.get("status") == "skipped" and "backdated alert" in agent_2.get("reason", "").lower():
            if email_config.get("notify_on_backdated_suppressed"):
                subject = f"[Suppressed] Backdated Alert: {event_id}"
                body = f"Alert {event_id} was suppressed because it is a backdated alert.\n\nDetails:\n{json.dumps(alert, indent=2)}"
                client.send_email(subject, body)
                logger.info(f"[{event_id}] Sent backdated suppression email.")
                
        # Condition 2: Auto-resolving alert is suppressed & resolved
        # Handled dynamically if the state itself flags it as resolved via run_delayed.py
        delayed_check = results.get("delayed_check", {})
        if delayed_check.get("status") == "resolved":
            if email_config.get("notify_on_autoresolve_resolved"):
                subject = f"[Resolved] Auto-resolving Alert Suppressed & Resolved: {event_id}"
                body = f"Alert {event_id} was classified as auto-resolving, suppressed, and verified resolved in DNAC.\n\nDetails:\n{json.dumps(alert, indent=2)}"
                client.send_email(subject, body)
                logger.info(f"[{event_id}] Sent auto-resolved suppression email.")
                
        # Condition 3: Genuine alerts pushed into ServiceNow
        # Checked via agent_4 action
        agent_4 = results.get("agent_4", {})
        agent_4_data = agent_4.get("data", {})
        action = agent_4_data.get("action", "")
        if action in ["incident_created", "incident_reopened", "comment_appended"]:
            if email_config.get("notify_on_genuine_servicenow"):
                incident = agent_4_data.get("incident", "UNKNOWN")
                subject = f"[Action Required] Genuine Alert Pushed to ServiceNow: {incident} ({event_id})"
                body = f"Alert {event_id} was verified as genuine and pushed to ServiceNow.\nAction: {action}, Incident: {incident}\n\nDetails:\n{json.dumps(alert, indent=2)}"
                client.send_email(subject, body)
                logger.info(f"[{event_id}] Sent ServiceNow push email.")
                
    except Exception as e:
        logger.error(f"[{event_id}] Failed in Email Notifier node: {e}", exc_info=True)
        
    return state
