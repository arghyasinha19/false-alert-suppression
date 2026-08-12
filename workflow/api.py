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

def check_dnac_status(
    device_id: str = None,
    event_id: str = None,
    instance_id: str = None,
    device_name: str = None,
    issue_name: str = None,
    issue_details: str = None
) -> Union[bool, str]:
    """
    Check DNAC to see if the alert is still active.
    Returns:
      - True if still active in DNAC (primary check or fallback active match)
      - False if resolved in DNAC (primary check or fallback resolved match)
      - "Uncertain" if alert cannot be found in active or resolved lists
    """
    import yaml
    from app.dnac_client import DNACClient

    try:
        config_path = os.path.join(project_root, "config.yaml")
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        dnac_config = config.get("dnac", {})
        client = DNACClient(dnac_config)

        # 1. Primary check using instance_id
        if instance_id:
            status = client.get_issue_status(instance_id)
            logger.info(f"DNAC primary status check for instance_id={instance_id}: status={status}")
            if status != "NOT_FOUND":
                if status.upper() in ("RESOLVED", "DELETED", "CLEARED", "IGNORED"):
                    return False
                else:
                    return True
            logger.info(f"instance_id={instance_id} returned NOT_FOUND (404). Triggering device fallback check.")

        # Helper function for description matching
        def is_match(issue: dict) -> bool:
            target_texts = [str(t).strip().lower() for t in [issue_name, issue_details, event_id] if t]
            if not target_texts:
                return False
            issue_texts = [
                str(issue.get(k, "")).strip().lower()
                for k in ["name", "issueName", "description", "issueDescription", "issueDetails", "title", "summary", "eventId"]
                if issue.get(k)
            ]
            for target in target_texts:
                for itext in issue_texts:
                    if target in itext or itext in target:
                        return True
            return False

        # 2. Fallback Step A: Check active device issues
        logger.info(f"Checking active issues for device_id={device_id}, device_name={device_name}")
        active_issues = client.get_device_issues(device_id=device_id, device_name=device_name, issue_status="ACTIVE")
        for issue in active_issues:
            iss_status = str(issue.get("issueStatus", issue.get("status", "ACTIVE"))).upper()
            if iss_status not in ["RESOLVED", "IGNORED", "CLEARED", "DELETED"]:
                if is_match(issue):
                    logger.info(f"Fallback check: Found matching active issue on device {device_id}/{device_name}")
                    return True

        # 3. Fallback Step B: Check resolved device issues
        logger.info(f"Checking resolved issues for device_id={device_id}, device_name={device_name}")
        resolved_issues = client.get_device_issues(device_id=device_id, device_name=device_name, issue_status="RESOLVED")
        for issue in resolved_issues:
            iss_status = str(issue.get("issueStatus", issue.get("status", "RESOLVED"))).upper()
            if iss_status in ["RESOLVED", "IGNORED", "CLEARED", "DELETED"]:
                if is_match(issue):
                    logger.info(f"Fallback check: Found matching resolved issue on device {device_id}/{device_name}")
                    return False

        # 4. Fallback Step C: If not found in active or resolved list -> Uncertain
        logger.warning(f"Fallback check: Issue not found in active or resolved issues for device {device_id}/{device_name}. Marking as Uncertain.")
        return "Uncertain"

    except FileNotFoundError:
        logger.error(f"config.yaml not found at {config_path}. Cannot initialize DNACClient. Defaulting to Uncertain.")
        return "Uncertain"
    except Exception as e:
        logger.error(f"Failed to check DNAC status for device {device_id}: {e}", exc_info=True)
        return "Uncertain"

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
        status = check_dnac_status(
            device_id=alert.device_id,
            event_id=alert.event_id,
            instance_id=alert.instance_id,
            device_name=alert.device_name,
            issue_name=alert.issue_name,
            issue_details=alert.issue_details
        )
        if status is True or status == "ACTIVE":
            logger.warning(f"Alert {alert.event_id} STILL ACTIVE. Forcing escalation.")
            initial_state["results"]["agent_2"] = {
                "data": {"predicted_category": "Non-Auto Resolving"}
            }
            agent4_result = agent_4_servicenow(initial_state)
            initial_state["results"]["agent_4"] = agent4_result
        elif status == "Uncertain":
            logger.warning(f"Alert {alert.event_id} status UNCERTAIN in DNAC. Forcing escalation to be safe.")
            initial_state["results"]["agent_2"] = {
                "data": {"predicted_category": "Uncertain"}
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
