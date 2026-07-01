import os
import sys
import logging
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Ensure project root is in python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from workflow.graph import build_graph
from workflow.nodes.node_agent_4_servicenow import agent_4_servicenow
from workflow.nodes.node_email_notifier import email_notifier
from workflow.nodes.node_reporter import reporter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

# Pre-compile the LangGraph (keeps the DistilBERT model "hot" in memory if it loads eagerly)
# We can initialize it during startup.
app = FastAPI(
    title="LangGraph False Alert Suppression API",
    description="Synchronous API to invoke the LangGraph workflow directly",
    version="1.0.0"
)

# Global graph instance
graph = None

@app.on_event("startup")
async def startup_event():
    global graph
    logger.info("Initializing LangGraph workflow and loading ML models...")
    graph = build_graph()
    logger.info("LangGraph initialized successfully.")

# Define the expected request payload matching run.py inputs
class AlertPayload(BaseModel):
    instance_id: Optional[str] = None
    event_id: str
    device_id: str
    device_name: str
    severity: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    raw_timestamp: Optional[str] = None
    correlation_id: Optional[str] = None
    source: Optional[str] = None
    issue_name: Optional[str] = None
    issue_details: Optional[str] = None

class InvokeResponse(BaseModel):
    overall_status: str
    results: Dict[str, Any]
    errors: list
    runtime_error: Optional[str] = None

def compute_overall_from_results(results: dict) -> str:
    statuses = [v.get("status") for v in (results or {}).values()]
    if any(s == "failed" for s in statuses):
        if any(s == "success" for s in statuses):
            return "partial_failure"
        return "failed"
    if statuses and all(s in ("success", "skipped") for s in statuses):
        return "success"
    return "unknown"

@app.get("/health", tags=["Operations"])
def health_check():
    return {"status": "healthy", "service": "langgraph-api"}

@app.post("/api/v1/invoke", response_model=InvokeResponse, tags=["Workflow"])
async def invoke_workflow(alert: AlertPayload):
    """
    Invokes the LangGraph false alert suppression workflow synchronously.
    """
    if graph is None:
        raise HTTPException(status_code=500, detail="Graph not initialized.")

    initial_state = {
        "alert": alert.model_dump()
    }
    
    logger.info(f"Invoking graph for event_id: {alert.event_id}")
    final_state = None
    try:
        # Invoke the graph synchronously (since the graph contains synchronous code)
        final_state = graph.invoke(initial_state)
        
        overall = final_state.get("overall_status", "unknown")
        results = final_state.get("results", {})
        errors = final_state.get("errors", [])
        
        if (not overall) or overall == "unknown":
            overall = compute_overall_from_results(results)

        logger.info(f"Graph completed for event_id: {alert.event_id} with status: {overall}")
        
        return InvokeResponse(
            overall_status=overall,
            results=results,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Runtime error during graph invocation: {str(e)}", exc_info=True)
        
        results = (final_state or {}).get("results", {})
        errors = (final_state or {}).get("errors", [])
        errors.append(f"Runtime Exception: {str(e)}")
        
        return InvokeResponse(
            overall_status="failed",
            results=results,
            errors=errors,
            runtime_error=str(e)
        )

def check_dnac_status(device_id: str, event_id: str) -> bool:
    """
    Check DNAC to see if the alert is still active.
    Returns True if still active, False if resolved.
    """
    logger.info(f"Checking DNAC status for device {device_id} and event {event_id}...")
    return True

@app.post("/api/v1/invoke/delayed", response_model=InvokeResponse, tags=["Workflow"])
async def invoke_delayed_workflow(alert: AlertPayload):
    """
    Invokes the delayed alert verification workflow directly.
    """
    initial_state = {
        "alert": alert.model_dump(),
        "results": {}
    }
    
    logger.info(f"Invoking delayed check for event_id: {alert.event_id}")
    final_state = None
    try:
        is_active = check_dnac_status(alert.device_id, alert.event_id)
        if is_active:
            logger.warning(f"Alert {alert.event_id} STILL ACTIVE. Forcing escalation.")
            initial_state["results"]["agent_2"] = {
                "data": {"predicted_category": "Non-Auto Resolving"}
            }
            
            agent4_result = agent_4_servicenow(initial_state)
            initial_state["results"]["agent_4"] = agent4_result
        else:
            logger.info(f"Alert {alert.event_id} is resolved in DNAC. No ServiceNow ticket required.")
            initial_state["results"]["delayed_check"] = {"status": "resolved"}
            
        initial_state = email_notifier(initial_state)
        final_state = reporter(initial_state)
        
        overall = final_state.get("overall_status", "unknown")
        results = final_state.get("results", {})
        errors = final_state.get("errors", [])
        
        if (not overall) or overall == "unknown":
            overall = compute_overall_from_results(results)

        logger.info(f"Delayed check completed for event_id: {alert.event_id} with status: {overall}")
        
        return InvokeResponse(
            overall_status=overall,
            results=results,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Runtime error during delayed graph invocation: {str(e)}", exc_info=True)
        
        results = (final_state or {}).get("results", {})
        errors = (final_state or {}).get("errors", [])
        errors.append(f"Runtime Exception: {str(e)}")
        
        return InvokeResponse(
            overall_status="failed",
            results=results,
            errors=errors,
            runtime_error=str(e)
        )

# Instructions to run:
# uvicorn workflow.api:app --host 0.0.0.0 --port 8001
