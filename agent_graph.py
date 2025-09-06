# In ai-scheduling-agent/agent_graph.py

from __future__ import annotations
from typing import TypedDict, Optional, Dict, Any, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from agents.intake_agent import run as intake_node
from agents.lookup_agent import run as lookup_node
from agents.schedule_agent import run as schedule_node
from agents.confirm_agent import run as confirm_node
from agents.reminder_agent import schedule_reminder_job

class AgentState(TypedDict, total=False):
    messages: List[Any]
    patient: Dict[str, Any]
    is_new_patient: bool
    appointment: Dict[str, Any]

def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("intake", intake_node)
    graph.add_node("lookup", lookup_node)
    graph.add_node("schedule", schedule_node)
    graph.add_node("confirm", confirm_node)
    # Removed form distribution; flow ends at confirm

    graph.set_entry_point("intake")
    graph.add_edge("intake", "lookup")
    graph.add_edge("lookup", "schedule")
    graph.add_edge("schedule", "confirm")
    graph.add_edge("confirm", END)

    # Compile without interrupts; schedule will propose times and confirm will run on the next turn
    return graph.compile()

# Helper to run one turn.
def run_turn(app, user_text: str, state: AgentState):
    if user_text:
        state['messages'].append(HumanMessage(content=user_text))

    # Keep track of existing messages
    current_messages = len(state.get("messages", []))
    
    # Invoke the graph
    result_state = app.invoke(state)

    # Find the newest AI message to display as the reply
    new_messages = result_state.get('messages', [])[current_messages:]
    last_ai_reply = ""
    for msg in new_messages:
        if isinstance(msg, AIMessage):
            last_ai_reply = msg.content
    
    appt = result_state.get('appointment')
    if appt and appt.get('status') == 'confirmed' and not appt.get('reminder_scheduled'):
        appt['patient'] = result_state.get('patient', {})
        schedule_reminder_job(appt)
        result_state['appointment']['reminder_scheduled'] = True

    return result_state, last_ai_reply