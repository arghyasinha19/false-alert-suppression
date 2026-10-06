from typing import TypedDict, Dict, Any, List, Optional, Literal

Status = Literal["pending", "running", "success", "failed", "skipped"]

class AgentResult(TypedDict, total=False):
    status: Status
    ok: bool
    data: Any
    error: str
    started_at: str
    ended_at: str
    reason: str # for skipped

class GraphState(TypedDict, total=False):
    alert: Dict[str, Any]
    
    # Generic registry for any number of agents
    results: Dict[str, AgentResult]
    
    # Optional global error store
    remarks: Dict[str, Any]
    
    # Structured exceptions captured by safe_node
    errors: List[Dict[str, Any]]

    # Final status computed by the reporter (must be declared or LangGraph drops it)
    overall_status: Optional[str]
    runtime_error: Optional[str]

    # Flow control
    next_node: Optional[str]
