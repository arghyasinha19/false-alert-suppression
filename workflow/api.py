import os
import sys
import hmac
import logging
from typing import Optional, Dict, Any, Union

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, field_validator

# Ensure project root is in python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(project_root, ".env"), override=False)

from workflow.graph import build_graph  # noqa: E402
from workflow.nodes.node_reporter import compute_overall_status  # noqa: E402
from workflow.delayed import run_delayed_check  # noqa: E402

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LangGraph False Alert Suppression API",
    description="Synchronous API to invoke the LangGraph workflow directly",
    version="1.1.0"
)

# Shared secret required on /api/v1/invoke* (sent by the Jenkins jobs).
WORKFLOW_API_TOKEN = os.getenv("WORKFLOW_API_TOKEN", "")

graph = None


@app.on_event("startup")
def startup_event():
    global graph
    logger.info("Initializing LangGraph workflow and loading ML models...")
    graph = build_graph()
    # Load the classifier eagerly so a missing model is visible at startup,
    # not discovered per alert.
    from workflow.nodes.node_agent_2 import _get_classifiers
    ml, dl = _get_classifiers()
    if ml is None and dl is None:
        logger.error("NO CLASSIFIER LOADED - every alert will be escalated to ServiceNow until fixed.")
    if not WORKFLOW_API_TOKEN:
        logger.error("WORKFLOW_API_TOKEN is not set - /api/v1/invoke* will reject all calls.")
    logger.info("LangGraph initialized successfully.")


def _require_token(request: Request) -> None:
    presented = request.headers.get("X-API-Token", "")
    if not (WORKFLOW_API_TOKEN and presented and hmac.compare_digest(presented, WORKFLOW_API_TOKEN)):
        raise HTTPException(status_code=401, detail="Unauthorized")


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
    # Assurance issueId (from ciscoDnaEventLink) - used by the delayed DNAC check
    issue_id: Optional[Union[str, int]] = None
    # When the webhook received the event (ISO-8601) - used for backdate detection
    received_at: Optional[str] = None

    @field_validator("event_id", "device_id", "device_name", "instance_id", "severity",
                     "raw_timestamp", "correlation_id", "issue_id", mode="before")
    @classmethod
    def coerce_to_str_or_none(cls, v: Any) -> Any:
        if v is None:
            return None
        return str(v)

    @field_validator("*", mode="before")
    @classmethod
    def empty_to_none(cls, v: Any) -> Any:
        # Jenkins passes unset parameters as "" - treat them as missing.
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class InvokeResponse(BaseModel):
    overall_status: str
    results: Dict[str, Any]
    errors: list
    runtime_error: Optional[str] = None


@app.get("/health", tags=["Operations"])
def health_check():
    return {"status": "healthy" if graph is not None else "starting", "service": "langgraph-api"}


# NOTE: plain ``def`` (not async): graph.invoke is blocking (ML, DNAC, SNOW,
# SMTP). FastAPI runs sync endpoints in a thread pool, so one slow alert no
# longer blocks every other request and /health.
@app.post("/api/v1/invoke", response_model=InvokeResponse, tags=["Workflow"])
def invoke_workflow(alert: AlertPayload, request: Request):
    """Invoke the false-alert suppression workflow for one alert."""
    _require_token(request)
    if graph is None:
        raise HTTPException(status_code=503, detail="Graph not initialized.")

    initial_state = {"alert": alert.model_dump(), "results": {}, "errors": [], "remarks": {}}
    logger.info(f"Invoking graph for event_id: {alert.event_id}")
    final_state = None
    try:
        final_state = graph.invoke(initial_state)
        results = final_state.get("results", {})
        overall = final_state.get("overall_status") or compute_overall_status(results)
        if overall == "unknown":
            overall = compute_overall_status(results)
        logger.info(f"Graph completed for event_id: {alert.event_id} with status: {overall}")
        return InvokeResponse(overall_status=overall, results=results, errors=final_state.get("errors", []))
    except Exception as e:
        logger.error(f"Runtime error during graph invocation: {e}", exc_info=True)
        results = (final_state or {}).get("results", {})
        errors = list((final_state or {}).get("errors", []))
        errors.append(f"Runtime Exception: {e}")
        return InvokeResponse(overall_status="failed", results=results, errors=errors, runtime_error=str(e))


@app.post("/api/v1/invoke/delayed", response_model=InvokeResponse, tags=["Workflow"])
def invoke_delayed_workflow(alert: AlertPayload, request: Request):
    """Invoke the delayed alert verification workflow."""
    _require_token(request)
    logger.info(f"Invoking delayed check for event_id: {alert.event_id}")
    final_state = None
    try:
        final_state = run_delayed_check(alert.model_dump())
        results = final_state.get("results", {})
        overall = final_state.get("overall_status") or compute_overall_status(results)
        logger.info(f"Delayed check completed for event_id: {alert.event_id} with status: {overall}")
        return InvokeResponse(overall_status=overall, results=results, errors=final_state.get("errors", []))
    except Exception as e:
        logger.error(f"Runtime error during delayed invocation: {e}", exc_info=True)
        results = (final_state or {}).get("results", {})
        errors = list((final_state or {}).get("errors", []))
        errors.append(f"Runtime Exception: {e}")
        return InvokeResponse(overall_status="failed", results=results, errors=errors, runtime_error=str(e))

# Run (bind to localhost - only the Jenkins agent on this host should call it):
#   uvicorn workflow.api:app --host 127.0.0.1 --port 8001
