import os
import sys
import logging
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Union

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

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
    instance_id: Optional[Union[str, int]] = None
    event_id: Optional[Union[str, int]] = None
    device_id: Optional[Union[str, int]] = None
    device_name: Optional[Union[str, int]] = None
    severity: Optional[Union[str, int, float]] = None
    category: Optional[str] = None
    status: Optional[str] = None
    raw_timestamp: Optional[Union[str, int, float]] = None
    correlation_id: Optional[Union[str, int]] = None
    source: Optional[str] = None
    issue_name: Optional[str] = None
    issue_details: Optional[str] = None

    @field_validator("event_id", "device_id", "device_name", "instance_id", "severity", "raw_timestamp", "correlation_id", mode="before")
    @classmethod
    def coerce_to_str_or_none(cls, v: Any) -> Any:
        if v is None:
            return None
        return str(v)

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

def check_dnac_status(device_id: str, event_id: str, instance_id: str = None) -> bool:
    """
    Check DNAC to see if the alert is still active by calling
    DNACClient.get_issue_status().

    Uses instance_id (the DNAC issue ID) as the primary lookup key.
    Falls back to event_id if instance_id is not available.

    Returns True if still active, False if resolved/cleared.
    """
    import yaml
    from app.dnac_client import DNACClient

    issue_id = instance_id or event_id
    if not issue_id:
        logger.warning("No instance_id or event_id available. Cannot check DNAC status. Assuming still active.")
        return True

    try:
        config_path = os.path.join(project_root, "config.yaml")
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        dnac_config = config.get("dnac", {})
        client = DNACClient(dnac_config)

        logger.info(f"Querying DNAC for issue status: issue_id={issue_id}, device_id={device_id}, event_id={event_id}")
        status = client.get_issue_status(issue_id)

        if status.upper() in ("RESOLVED", "DELETED", "CLEARED"):
            logger.info(f"DNAC reports issue {issue_id} as '{status}' — alert has auto-resolved.")
            return False
        else:
            logger.warning(f"DNAC reports issue {issue_id} as '{status}' — alert is STILL ACTIVE.")
            return True

    except FileNotFoundError:
        logger.error(f"config.yaml not found at {config_path}. Cannot initialize DNACClient. Assuming alert still active.")
        return True
    except Exception as e:
        logger.error(f"Failed to check DNAC status for issue {issue_id}: {e}", exc_info=True)
        # Fail-safe: assume still active so it gets escalated
        logger.warning("Defaulting to 'still active' due to DNAC check failure.")
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
        is_active = check_dnac_status(alert.device_id, alert.event_id, instance_id=alert.instance_id)
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
