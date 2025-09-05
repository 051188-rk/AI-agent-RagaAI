# In ai-scheduling-agent/agents/schedule_agent.py

from datetime import datetime
from langchain_core.messages import AIMessage, HumanMessage
from tools.data_io import find_available_slots
import re

def run(state):
    messages = state.get("messages", [])
    
    if state.get("appointment", {}).get("options"):
        return state

    last_user = None
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            last_user = m.content
            break

    if not last_user:
        return state

    date_match = re.search(r"(20\d{2}-\d{2}-\d{2})", last_user)
    date_str = date_match.group(1) if date_match else None
    doc_match = re.search(r"(Dr\.?\s+[A-Z][a-zA-Z]+\s+[A-Z][a-zA-Z]+)", last_user)
    doctor = doc_match.group(1) if doc_match else None

    # CRITICAL FIX: Handle parsing failure explicitly
    if not doctor or not date_str:
        # This occurs when the user is likely trying to select a time.
        # But if we are in this agent, it means something went wrong.
        # Instead of failing silently, we prompt the user again.
        messages.append(AIMessage(content="I'm sorry, I couldn't understand that. Please provide the doctor and date again, like 'Dr. Alice Wong on 2025-09-15'."))
        state["messages"] = messages
        return state

    is_new = state.get("is_new_patient", False)
    duration = 60 if is_new else 30
    
    date_obj = datetime.fromisoformat(date_str)
    slots = find_available_slots(doctor, date_obj.date(), duration)

    if not slots:
        messages.append(AIMessage(content=f"Sorry, no available slots for {doctor} on {date_str}. Please try another date or doctor."))
        state["messages"] = messages
        return state

    shown = slots[:5]
    pretty = ", ".join([s['date_slot'].strftime("%H:%M") for s in shown])
    messages.append(AIMessage(content=f"Available times for {doctor} on {date_str}: {pretty}. Which time works?"))
    
    state.setdefault("appointment", {})
    state["appointment"]["doctor_name"] = doctor
    state["appointment"]["date"] = date_str
    state["appointment"]["duration_min"] = duration
    state["appointment"]["options"] = shown
    state["messages"] = messages
    
    return state