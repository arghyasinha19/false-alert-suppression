import logging
from typing import Dict, Any
from workflow.state import GraphState
from workflow.tools.mongodb_client import MongoDBClient

logger = logging.getLogger(__name__)


def compute_overall_status(results: Dict[str, Any]) -> str:
    statuses = [(r or {}).get("status", "pending") for r in (results or {}).values()]
    if any(s == "failed" for s in statuses):
        return "partial_failure" if any(s == "success" for s in statuses) else "failed"
    if statuses and all(s in ("success", "skipped") for s in statuses):
        return "success"
    return "unknown"


def reporter(state: GraphState, merge_results: bool = False) -> GraphState:
    """
    Persist the outcome to MongoDB and compute ``overall_status``.

    merge_results=False (main flow): the document's ``results`` is set.
    merge_results=True (delayed flow): only the keys produced by the delayed
    run are written (``results.<agent>``), so the main run's Agent 1-3 results
    are preserved instead of being overwritten.
    """
    results = state.get("results", {}) or {}
    alert = state.get("alert", {}) or {}
    alert_id = alert.get("event_id") or alert.get("id") or "unknown_event_id"

    overall = compute_overall_status(results)
    state["overall_status"] = overall

    try:
        mongo = MongoDBClient()
        if merge_results:
            payload = {f"results.{k}": v for k, v in results.items()}
            payload["alert_details"] = alert
            payload["delayed_overall_status"] = overall
        else:
            payload = {
                "results": results,
                "runtime_error": state.get("runtime_error"),
                "alert_details": alert,
                "overall_status": overall,
            }
        mongo.save_alert_result(alert_id, payload)
    except Exception as e:
        logger.error(f"Failed to save results to MongoDB: {e}")

    return state
