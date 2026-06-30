from datetime import datetime
import traceback
from typing import Callable, Any, Dict
from workflow.state import GraphState

def _now() -> str:
    return datetime.utcnow().isoformat()

def safe_node(agent_name: str, fn: Callable[[GraphState], Any]) -> Callable[[GraphState], GraphState]:
    """
    Wrap a node so exceptions become structured results instead of stopping the graph.
    """
    def _wrapped(state: GraphState) -> GraphState:
        state.setdefault("results", {})
        state.setdefault("remarks", {})
        
        # Mark running
        state["results"].setdefault(agent_name, {})
        state["results"][agent_name].update({
            "status": "running",
            "started_at": _now(),
        })
        
        try:
            out = fn(state)
            
            # Normalize outputs: if tool-like dict with ok/data/error exists, use it.
            if isinstance(out, dict) and "ok" in out:
                ok = bool(out.get("ok"))
                state["results"][agent_name].update({
                    "status": "success" if ok else "failed",
                    "ok": ok,
                    "data": out.get("data"),
                    "error": out.get("remarks"),
                    "ended_at": _now(),
                })
            else:
                state["results"][agent_name].update({
                    "status": "success",
                    "ok": True,
                    "data": out,
                    "remarks": out.get("remarks"),
                    "ended_at": _now(),
                })
                
        except Exception as e:
            state["results"][agent_name].update({
                "status": "failed",
                "ok": False,
                "error": f"{type(e).__name__}: {e}",
                "ended_at": _now(),
            })
            state["errors"].append({
                "agent": agent_name,
                "error": f"{type(e).__name__}: {e}",
                "trace": traceback.format_exc(),
                "time": _now(),
            })
            
        return state
        
    return _wrapped
