import sys, os

from workflow.state import GraphState
import logging

logger = logging.getLogger(__name__)

def _extract_gate_status(agent1_data) -> str:
    """
    Extract the gate status from agent_1 output data.
    
    Tries common keys:
      - data["ok"]
    """
    if not isinstance(agent1_data, dict):
        return ""
        
    # Common direct keys
    for k in ("ok",):
        v = agent1_data.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
            
    return ""
    
def supervisor(state: GraphState) -> GraphState:
    """
    Routing rules:
      1) If agent_1 determined the alert is backdated -> skip rest of the flow and report
      2) If agent_1 returned Non back dated alert -> route to agent_2
    """
    state.setdefault("results", {})
    
    event_id = state.get("alert", {}).get("event_id", "UNKNOWN")
    logger.info(f"[{event_id}] Entering Supervisor node to determine next route.")
    
    a1 = state["results"].get("agent_1", {})
    agent1_data = a1.get("data") or {}
    
    # Check for failure in agent 1 execution
    a1_ok = a1.get("ok")
    if not a1_ok:
        state["results"].setdefault("agent_2", {})
        state["results"]["agent_2"].update({
            "status": "skipped",
            "ok": False,
            "reason": f"dependency_failed_or_not_success: agent_1 ok={a1_ok}"
        })
        state["next_node"] = "reporter"
        logger.info(f"[{event_id}] Supervisor decided: Route to reporter (Agent 1 failed).")
        return state

    # Rule 1: Backdated gate
    is_backdated = agent1_data.get("is_backdated", False)
    if is_backdated:
        state["results"].setdefault("agent_2", {})
        state["results"]["agent_2"].update({
            "status": "skipped",
            "ok": False,
            "reason": "agent1_gate: backdated alert"
        })
        state["next_node"] = "reporter"
        logger.info(f"[{event_id}] Supervisor decided: Route to reporter (Backdated alert).")
        return state
        
    # Rule 2: agent_1 Non-CITO gate
    agent1_data = a1.get("data") or {}
    gate_status = _extract_gate_status(agent1_data)
    
    if gate_status.lower() == "non-cito":
        state["results"].setdefault("agent_2", {})
        state["results"]["agent_2"].update({
            "status": "skipped",
            "ok": False,
            "reason": "agent1_gate: Non-CITO"
        })
        state["next_node"] = "reporter"
        logger.info(f"[{event_id}] Supervisor decided: Route to reporter (Non-CITO).")
        return state
        
    # Rule 3: run agent_2
    state["next_node"] = "agent_2"
    logger.info(f"[{event_id}] Supervisor decided: Route to agent_2.")
    return state
    
def route_next(state: GraphState) -> str:
    return state.get("next_node") or "reporter"
