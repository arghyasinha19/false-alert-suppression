import logging
import json
import os
from typing import Dict, Any, Optional, Tuple
from workflow.state import GraphState
from workflow.tools.servicenow_client import ServiceNowClient, ServiceNowError
from workflow.utils.helpers import result_data

logger = logging.getLogger(__name__)

REOPEN_WINDOW_DAYS = int(os.getenv("SNOW_REOPEN_WINDOW_DAYS", "3"))


def _correlation_id(alert: Dict[str, Any]) -> str:
    """One DNAC notification -> one SNOW action (idempotent on redelivery)."""
    if alert.get("instance_id"):
        return f"dnac:{alert['instance_id']}"
    parts = [alert.get("event_id"), alert.get("device_id") or alert.get("device_name"), alert.get("raw_timestamp")]
    return "dnac:" + ":".join(str(p) for p in parts if p)


def _escalation_decision(state: GraphState) -> Tuple[bool, str]:
    """
    Decide whether this alert must go to ServiceNow.

    Fail-safe: anything other than a *successfully scheduled* auto-resolving
    alert is escalated - including classifier failures and delay-queue
    failures, which previously dropped the alert silently.
    """
    predicted = result_data(state, "agent_2").get("predicted_category")
    a3 = (state.get("results") or {}).get("agent_3") or {}
    queue_status = result_data(state, "agent_3").get("queue_status")

    if predicted == "Auto resolving":
        if queue_status == "delayed":
            return False, "Auto resolving alert scheduled for delayed DNAC re-check."
        if a3 and (a3.get("ok") is False or queue_status == "failed"):
            return True, "Auto resolving, but delayed re-check could not be scheduled - escalating now."
        if not a3:
            # Called outside the main graph (e.g. delayed path) with an auto label.
            return False, "Auto resolving alert. Skipping ServiceNow integration."
        return True, f"Auto resolving, but delay status unknown ({queue_status}) - escalating."
    if not predicted:
        return True, "No classification available (classifier failed) - escalating to be safe."
    return True, f"Classified as '{predicted}' - escalating."


def agent_4_servicenow(state: GraphState) -> Dict[str, Any]:
    """
    Agent 4 (ServiceNow): raises / updates incidents for alerts that need a human.

    Order of operations:
      1. Idempotency: incident already exists for this DNAC notification -> no-op.
      2. Open incident for the device            -> append comment.
      3. Recently Resolved incident for device    -> reopen.
      4. Otherwise                                -> create (referencing a recently Closed one).

    Any ServiceNow error makes this agent FAIL (never silently "succeeds"), so
    Jenkins/the dashboard show it and the failure email fires.
    """
    alert = state.get("alert", {})
    event_id = alert.get("event_id", "UNKNOWN")
    logger.info(f"[{event_id}] Entering Agent 4 (ServiceNow).")

    escalate, reason = _escalation_decision(state)
    if not escalate:
        output = {"ok": True, "status": "skipped", "data": {"action": "none"}, "remarks": reason}
        logger.info(f"[{event_id}] Agent 4 completed. Output: {output}")
        return output
    logger.info(f"[{event_id}] Agent 4: {reason}")

    snow_push_enabled = os.getenv("SNOW_PUSH_ENABLED", "yes").strip().lower() == "yes"

    device_name = alert.get("device_name") or alert.get("device") or "Unknown Device"
    issue_name = alert.get("issue_name") or "Network Event"
    correlation_id = _correlation_id(alert)
    raw_alert = json.dumps(alert, indent=2, default=str)
    note = (
        f"DNAC alert {alert.get('event_id')} ({issue_name})\n"
        f"Device: {device_name}\nSeverity: {alert.get('severity')}\n"
        f"Timestamp: {alert.get('raw_timestamp')}\nReason: {reason}"
    )

    def _out(action: str, incident: Optional[str], msg: str, ok: bool = True) -> Dict[str, Any]:
        if not snow_push_enabled and ok:
            action, msg = f"{action}_dry_run", f"Dry-run: {msg}"
        output = {"ok": ok, "data": {"action": action, "incident": incident, "reason": reason}, "remarks": msg}
        logger.info(f"[{event_id}] Agent 4 completed. Output: {output}")
        return output

    try:
        client = ServiceNowClient()
        if not snow_push_enabled and not client.configured:
            return _out("incident_created", None, f"would have escalated {device_name} (SNOW not configured)")

        # 1. Idempotency on redelivery
        existing = client.find_by_correlation_id(correlation_id)
        if existing:
            return _out("duplicate_event_ignored", existing.get("number"),
                        f"Incident {existing.get('number')} already raised for this DNAC notification.")

        # 2. Open incident for this device -> comment
        open_inc = client.find_open_incident(device_name)
        if open_inc:
            if snow_push_enabled:
                client.append_comment(open_inc["sys_id"], "Recurring alert detected.\n" + note)
            return _out("comment_appended", open_inc.get("number"),
                        f"Appended to open incident {open_inc.get('number')}")

        # 3. Recently resolved -> reopen
        resolved_inc = client.find_recently_resolved_incident(device_name, REOPEN_WINDOW_DAYS)
        if resolved_inc:
            if snow_push_enabled:
                client.reopen_incident(resolved_inc["sys_id"], "Re-opened due to recurring alert.\n" + note)
            return _out("incident_reopened", resolved_inc.get("number"),
                        f"Re-opened recently resolved incident {resolved_inc.get('number')}")

        # 4. Create (Closed incidents cannot normally be reopened -> new, linked)
        closed_inc = client.find_recently_closed_incident(device_name, REOPEN_WINDOW_DAYS)
        related = closed_inc.get("number") if closed_inc else None
        if snow_push_enabled:
            new_inc = client.create_incident(
                device_name, issue_name, raw_alert,
                correlation_id=correlation_id,
                severity=alert.get("severity"),
                related_incident=related,
            )
            return _out("incident_created", new_inc.get("number"), f"Created new incident {new_inc.get('number')}")
        return _out("incident_created", None, f"would have created a new incident for {device_name}")

    except ServiceNowError as e:
        logger.error(f"[{event_id}] Agent 4 ServiceNow error: {e}")
        return {
            "ok": False,
            "data": {"action": "servicenow_failed", "reason": reason},
            "remarks": f"error: {e}",
        }
    except Exception as e:
        logger.error(f"[{event_id}] Agent 4 ServiceNow orchestration failed: {e}", exc_info=True)
        return {
            "ok": False,
            "data": {"action": "servicenow_failed", "reason": reason},
            "remarks": f"error: {e}",
        }
