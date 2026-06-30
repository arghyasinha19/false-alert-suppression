import os, sys
import yaml
import logging
from typing import Dict, Any
from workflow.state import GraphState
from workflow.tools.mongodb_client import MongoDBClient

def reporter(state: GraphState) -> GraphState:
    results = state.get("results", {})
    statuses = [r.get("status", "pending") for r in results.values()]
    
    final_output = {
        "results": results,
        "runtime_error": state.get("runtime_error")
    }
    
    # Save the final structured output to MongoDB for the React Dashboard
    alert = state.get("alert", {})
    alert_id = alert.get("event_id") or alert.get("id") or "unknown_event_id"
    
    try:
        mongo = MongoDBClient()
        # Mix the original alert details into the payload for better UI querying
        db_payload = {**final_output, "alert_details": alert}
        mongo.save_alert_result(alert_id, db_payload)
    except Exception as e:
        logging.error(f"Failed to save results to MongoDB: {e}")
    
    # Also save to disk (existing behavior)
    import json
    with open("status.json", "w") as f:
        json.dump(final_output, f, indent=2)
    
    if any(s == "failed" for s in statuses) and any(s == "success" for s in statuses):
        overall = "partial_failure"
    elif any(s == "failed" for s in statuses):
        overall = "failed"
    elif all(s in ("success", "skipped") for s in statuses) and statuses:
        overall = "success"
    else:
        overall = "unknown"
        
    state["overall_status"] = overall
    return state
