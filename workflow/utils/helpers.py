from datetime import datetime, timezone
import logging
import traceback
from typing import Callable, Any, Dict
from workflow.state import GraphState

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def result_data(state: GraphState, agent_name: str) -> Dict[str, Any]:
    """
    Safe accessor for an agent's ``data`` dict.

    ``results[agent]["data"]`` is explicitly None when an agent fails, so
    ``.get("data", {})`` returns None and the next ``.get`` raises. Always use
    this helper instead.
    """
    data = ((state.get("results") or {}).get(agent_name) or {}).get("data")
    return data if isinstance(data, dict) else {}

def safe_node(agent_name: str, fn: Callable[[GraphState], Any]) -> Callable[[GraphState], GraphState]:
    """
    Wrap a node so exceptions become structured results instead of stopping the graph.
    """
    def _wrapped(state: GraphState) -> GraphState:
        state.setdefault("results", {})
        state.setdefault("remarks", {})
        state.setdefault("errors", [])
        
        # Mark running
        state["results"].setdefault(agent_name, {})
        state["results"][agent_name].update({
            "status": "running",
            "started_at": _now(),
        })
        
        try:
            out = fn(state)
            
            if out is state:
                state["results"][agent_name].update({
                    "status": "success",
                    "ok": True,
                    "ended_at": _now(),
                })
            elif isinstance(out, dict) and "ok" in out:
                ok = bool(out.get("ok"))
                status = out.get("status") or ("success" if ok else "failed")
                state["results"][agent_name].update({
                    "status": status,
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
                    "remarks": out.get("remarks") if isinstance(out, dict) else None,
                    "ended_at": _now(),
                })
                
        except Exception as e:
            logger.exception(f"Node {agent_name} raised: {e}")
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
