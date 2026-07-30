import logging
import json
import os
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

    # Read the push-enabled flag from the environment (default: yes)
    snow_push_enabled = os.getenv("SNOW_PUSH_ENABLED", "yes").strip().lower() == "yes"
    if not snow_push_enabled:
        logger.info(f"[{event_id}] SNOW_PUSH_ENABLED is set to 'no'. Ticket creation/update will be skipped (dry-run mode).")

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
            logger.info(f"Agent 4: Found active incident {inc_number} for {device_name}.")

            if snow_push_enabled:
                logger.info(f"Agent 4: Appending comment to {inc_number}.")
                client.append_comment(
                    active_incident.get("sys_id"), 
                    f"Duplicate/Recurring alert detected for event: {alert.get('event_id')}\nTimestamp: {alert.get('raw_timestamp')}\nSeverity: {alert.get('severity')}"
                )
                output = {
                    "ok": True,
                    "data": {"action": "comment_appended", "incident": inc_number},
                    "remarks": f"Appended to active incident {inc_number}"
                }
            else:
                logger.info(f"Agent 4: Dry-run — skipping comment append to {inc_number}.")
                output = {
                    "ok": True,
                    "data": {"action": "comment_appended_dry_run", "incident": inc_number},
                    "remarks": f"Dry-run: would have appended to active incident {inc_number}"
                }

            logger.info(f"[{event_id}] Agent 4 completed. Output: {output}")
            return output
            
        # 2. Check for closed incident within 3 days
        closed_incident = client.find_incident(device_name, active=False, closed_within_days=3)
        
        if closed_incident:
            inc_number = closed_incident.get("number")
            logger.info(f"Agent 4: Found recently closed incident {inc_number} for {device_name}.")

            if snow_push_enabled:
                logger.info(f"Agent 4: Reopening incident {inc_number}.")
                client.reopen_incident(
                    closed_incident.get("sys_id"), 
                    f"Re-opened due to recurring alert for event: {alert.get('event_id')}\nSeverity: {alert.get('severity')}"
                )
                output = {
                    "ok": True,
                    "data": {"action": "incident_reopened", "incident": inc_number},
                    "remarks": f"Re-opened recently closed incident {inc_number}"
                }
            else:
                logger.info(f"Agent 4: Dry-run — skipping reopen of {inc_number}.")
                output = {
                    "ok": True,
                    "data": {"action": "incident_reopened_dry_run", "incident": inc_number},
                    "remarks": f"Dry-run: would have re-opened incident {inc_number}"
                }

            logger.info(f"[{event_id}] Agent 4 completed. Output: {output}")
            return output
            
        # 3. Open a new incident
        logger.info(f"Agent 4: No active or recently closed incidents found for {device_name}.")

        if snow_push_enabled:
            logger.info(f"Agent 4: Creating new incident for {device_name}.")
            new_inc = client.create_incident(device_name, issue_name, raw_alert)
            if new_inc:
                output = {
                    "ok": True,
                    "data": {"action": "incident_created", "incident": new_inc.get("number")},
                    "remarks": f"Created new incident {new_inc.get('number')}"
                }
            else:
                output = {
                    "ok": False,
                    "data": {"action": "incident_creation_failed"},
                    "remarks": "Failed to create new incident."
                }
        else:
            logger.info(f"Agent 4: Dry-run — skipping new incident creation for {device_name}.")
            output = {
                "ok": True,
                "data": {"action": "incident_created_dry_run"},
                "remarks": f"Dry-run: would have created a new incident for {device_name}"
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

