from datetime import datetime
from langchain_core.messages import AIMessage
from tools.data_io import find_available_slots, reserve_slot

def run(state):
    messages = state.get("messages", [])
    patient = state.get("patient", {})
    # Parse the user's last message to extract doctor name and date
    last_user = None
    for m in reversed(messages):
        if m.type == "human":
            last_user = m.content
            break

    if not last_user:
        messages.append(AIMessage(content="Please provide the doctor name and desired date (YYYY-MM-DD)."))
        state["messages"] = messages
        return state

    # naive parse
    # Expect pattern "Dr. Name on YYYY-MM-DD" or include a date string
    import re
    date_match = re.search(r"(20\d{2}-\d{2}-\d{2})", last_user)
    date_str = date_match.group(1) if date_match else None
    doc_match = re.search(r"(Dr\.?\s+[A-Z][a-zA-Z]+\s+[A-Z][a-zA-Z]+)", last_user)
    doctor = doc_match.group(1) if doc_match else None

    if not doctor or not date_str:
        messages.append(AIMessage(content="I couldn't parse that. Please specify like: 'Dr. Alice Wong on 2025-09-06'."))
        state["messages"] = messages
        return state

    date_obj = datetime.fromisoformat(date_str)
    slots = find_available_slots(doctor, date_obj.date())

    if not slots:
        messages.append(AIMessage(content=f"Sorry, no available slots for {doctor} on {date_str}. Try another date or doctor."))
        state["messages"] = messages
        return state

    # show top 3 choices
    shown = slots[:3]
    pretty = ", ".join([s['date_slot'].strftime("%H:%M") for s in shown])
    messages.append(AIMessage(content=f"Available times for {doctor} on {date_str}: {pretty}. Which time works?"))
    state["messages"] = messages

    # Next human message should contain a time selection; try to reserve
    # (We do the reservation in the confirm node after user selects)
    state.setdefault("appointment", {})
    state["appointment"]["doctor_name"] = doctor
    state["appointment"]["date"] = date_str
    state["appointment"]["options"] = shown
    return state
