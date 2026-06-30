from langgraph.graph import StateGraph, END
from .state import GraphState
from .utils.helpers import safe_node
from .nodes.node_agent_1 import agent_1_logic
from .nodes.node_agent_2 import agent_2_logic
from .nodes.node_agent_3_scheduler import agent_3_scheduler
from .nodes.node_agent_4_servicenow import agent_4_servicenow
from .nodes.node_supervisor import supervisor, route_next
from .nodes.node_reporter import reporter
from .nodes.node_email_notifier import email_notifier

def build_graph():
    builder = StateGraph(GraphState)

    # Wrap agent nodes so they never terminate the graph on exception
    builder.add_node("agent_1", safe_node("agent_1", agent_1_logic))
    builder.add_node("agent_2", safe_node("agent_2", agent_2_logic))
    builder.add_node("agent_3", safe_node("agent_3", agent_3_scheduler))
    builder.add_node("agent_4", safe_node("agent_4", agent_4_servicenow))

    builder.add_node("supervisor", supervisor)
    builder.add_node("email_notifier", safe_node("email_notifier", email_notifier))
    builder.add_node("reporter", reporter)

    builder.set_entry_point("agent_1")

    # Always go to supervisor after agent_1 (even if agent_1 failed)
    builder.add_edge("agent_1", "supervisor")

    # Supervisor chooses next node
    builder.add_conditional_edges(
        "supervisor",
        route_next,
        {
            "reporter": "email_notifier",
            "agent_2": "agent_2",
        },
    )

    # Always go to agent_3 after agent_2
    builder.add_edge("agent_2", "agent_3")
    
    # Always go to agent_4 after agent_3
    builder.add_edge("agent_3", "agent_4")
    
    # Always go to email_notifier after agent_4
    builder.add_edge("agent_4", "email_notifier")
    
    # Always go to reporter after email_notifier
    builder.add_edge("email_notifier", "reporter")

    # Reporter ends
    builder.add_edge("reporter", END)

    return builder.compile()
