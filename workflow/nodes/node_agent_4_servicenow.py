import logging
import json
from typing import Dict, Any
from workflow.state import GraphState
from workflow.tools.servicenow_client import ServiceNowClient

logger = logging.getLogger(__name__)

def agent_4_servicenow(state: GraphState) -> Dict[str, Any]:
    """
    Agent 4 (ServiceNow): Intercepts 'Non-Auto Resolving' alerts and handles SNOW incidents.
    """
    alert = state.get("alert", {})
    event_id = alert.get("event_id", "UNKNOWN")
    logger.info(f"[{event_id}] Entering Agent 4 (ServiceNow). Input payload: {alert}")

    agent2_result = state.get("results", {}).get("agent_2", {})
    predicted_category = agent2_result.get("data", {}).get("predicted_category")
    
    # Check if we should process this alert
    if predicted_category == "Auto resolving":
        output = {
            "ok": True,
            "data": None,
            "remarks": f"Auto resolving alert. Skipping ServiceNow integration."
        }
        logger.info(f"[{event_id}] Agent 4 completed. Output: {output}")
        return output
        
    if not predicted_category:
        return {
            "ok": False,
            "data": None,
            "remarks": "Skipped: no classification category found."
        }
        
    try:
        client = ServiceNowClient()
        alert = state.get("alert", {})
        
        device_name = alert.get("device_name") or alert.get("device") or "Unknown Device"
        issue_name = alert.get("issue_name") or "Network Event"
        raw_alert = json.dumps(alert, indent=2)
        
        # 1. Check for active incident
        active_incident = client.find_incident(device_name, active=True)
        
        if active_incident:
            inc_number = active_incident.get("number")
            logger.info(f"Agent 4: Found active incident {inc_number} for {device_name}. Appending comment.")
            client.append_comment(
                active_incident.get("sys_id"), 
                f"Duplicate/Recurring alert detected for event: {alert.get('event_id')}\nTimestamp: {alert.get('raw_timestamp')}\nSeverity: {alert.get('severity')}"
            )
            output = {
                "ok": True,
                "data": {"action": "comment_appended", "incident": inc_number},
                "remarks": f"Appended to active incident {inc_number}"
            }
            logger.info(f"[{event_id}] Agent 4 completed. Output: {output}")
            return output
            
        # 2. Check for closed incident within 3 days
        closed_incident = client.find_incident(device_name, active=False, closed_within_days=3)
        
        if closed_incident:
            inc_number = closed_incident.get("number")
            logger.info(f"Agent 4: Found recently closed incident {inc_number} for {device_name}. Reopening.")
            client.reopen_incident(
                closed_incident.get("sys_id"), 
                f"Re-opened due to recurring alert for event: {alert.get('event_id')}\nSeverity: {alert.get('severity')}"
            )
            output = {
                "ok": True,
                "data": {"action": "incident_reopened", "incident": inc_number},
                "remarks": f"Re-opened recently closed incident {inc_number}"
            }
            logger.info(f"[{event_id}] Agent 4 completed. Output: {output}")
            return output
            
        # 3. Open a new incident
        logger.info(f"Agent 4: No active or recently closed incidents found for {device_name}. Creating new incident.")
        new_inc = client.create_incident(device_name, issue_name, raw_alert)
        if new_inc:
            output = {
                "ok": True,
                "data": {"action": "incident_created", "incident": new_inc.get("number")},
                "remarks": f"Created new incident {new_inc.get('number')}"
            }
            logger.info(f"[{event_id}] Agent 4 completed. Output: {output}")
            return output
        else:
            output = {
                "ok": False,
                "data": {"action": "incident_creation_failed"},
                "remarks": "Failed to create new incident."
            }
            logger.info(f"[{event_id}] Agent 4 completed. Output: {output}")
            return output
            
    except Exception as e:
        logger.error(f"[{event_id}] Agent 4 ServiceNow Orchestration failed: {e}", exc_info=True)
        return {
            "ok": False,
            "data": None,
            "remarks": f"error: {str(e)}"
        }
