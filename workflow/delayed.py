"""
Delayed verification flow (shared by workflow/api.py and workflow/run_delayed.py).

An alert classified 'Auto resolving' waits in the delay queue, then this
re-checks DNAC:
    ACTIVE or UNCERTAIN -> escalate to ServiceNow (Agent 4)
    RESOLVED            -> suppressed (no ticket), notification email
"""
import logging
from typing import Dict, Any

from workflow.utils.helpers import safe_node
from workflow.nodes.node_agent_4_servicenow import agent_4_servicenow
from workflow.nodes.node_email_notifier import email_notifier
from workflow.nodes.node_reporter import reporter
from workflow.tools.dnac_status import check_alert_status, ACTIVE, RESOLVED

logger = logging.getLogger(__name__)


def run_delayed_check(alert: Dict[str, Any]) -> Dict[str, Any]:
    """
    Delayed verification for an alert classified 'Auto resolving'.
    Shared by workflow/api.py and workflow/run_delayed.py.

    ACTIVE or UNCERTAIN -> escalate to ServiceNow. RESOLVED -> suppressed.
    """
    state: Dict[str, Any] = {"alert": alert, "results": {}, "errors": [], "remarks": {}}

    dnac_status = check_alert_status(
        issue_id=alert.get("issue_id"),
        device_id=alert.get("device_id"),
        device_name=alert.get("device_name"),
        issue_name=alert.get("issue_name"),
    )
    state["results"]["delayed_check"] = {
        "status": "success",
        "ok": True,
        "data": {"dnac_status": dnac_status},
    }

    if dnac_status == RESOLVED:
        logger.info(f"Alert {alert.get('event_id')} is resolved in DNAC. No ServiceNow ticket required.")
        # Kept for the email notifier's "auto-resolved" condition.
        state["results"]["delayed_check"]["data"]["outcome"] = "resolved"
    else:
        label = "Non-Auto Resolving" if dnac_status == ACTIVE else "Uncertain"
        logger.warning(f"Alert {alert.get('event_id')} DNAC status {dnac_status}. Escalating to ServiceNow.")
        state["results"]["agent_2"] = {
            "status": "skipped",
            "ok": True,
            "data": {"predicted_category": label},
            "reason": f"delayed_check: DNAC status {dnac_status}",
        }
        state = safe_node("agent_4", agent_4_servicenow)(state)

    # Mutates state in place (do NOT assign its return value to state).
    safe_node("email_notifier", email_notifier)(state)
    state = reporter(state, merge_results=True)
    return state
