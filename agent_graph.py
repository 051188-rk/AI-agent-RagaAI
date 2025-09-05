from __future__ import annotations
from typing import TypedDict, Optional, Dict, Any, List
from datetime import datetime, timedelta
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

# Agent node functions
from agents.greeting_agent import run as greeting_node
from agents.intake_agent import run as intake_node
from agents.lookup_agent import run as lookup_node
from agents.schedule_agent import run as schedule_node
from agents.confirm_agent import run as confirm_node
from agents.reminder_agent import schedule_reminder_job

class AgentState(TypedDict, total=False):
    messages: List[Any]          # chat history
    patient: Dict[str, Any]      # dict of patient details
    is_new_patient: bool
    appointment: Dict[str, Any]  # chosen slot + doctor
    error: Optional[str]
    next: Optional[str]          # manual routing hint

def build_graph():
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("greeting", greeting_node)
    graph.add_node("intake", intake_node)
    graph.add_node("lookup", lookup_node)
    graph.add_node("schedule", schedule_node)
    graph.add_node("confirm", confirm_node)

    # Entry
    graph.set_entry_point("greeting")

    # Static, rule-based edges
    graph.add_edge("greeting", "intake")
    graph.add_edge("intake", "lookup")
    graph.add_edge("lookup", "schedule")
    graph.add_edge("schedule", "confirm")

    # Confirm is terminal; but it can also schedule a reminder and end
    graph.add_edge("confirm", END)

    return graph.compile()

# Helper to run one turn inside Streamlit
def run_turn(app, user_text: str, state: Optional[AgentState] = None):
    if state is None:
        state = AgentState(messages=[])

    # add user message
    state['messages'] = state.get('messages', []) + [HumanMessage(content=user_text)]
    result_state = app.invoke(state)

    # fetch the last agent message for display convenience
    last_ai = None
    for m in result_state.get('messages', [])[::-1]:
        if isinstance(m, AIMessage):
            last_ai = m
            break

    # schedule reminder if appointment is confirmed
    appt = result_state.get('appointment')
    if appt and appt.get('status') == 'confirmed' and not appt.get('reminder_scheduled'):
        schedule_reminder_job(appt)  # runs async via APScheduler
        appt['reminder_scheduled'] = True

    return result_state, (last_ai.content if last_ai else "")
