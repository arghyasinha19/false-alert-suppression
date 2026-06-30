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
    remarks: List[Dict[str, Any]]
    
    # Flow control
    next_node: Optional[str]
