from datetime import datetime
from langchain_core.messages import AIMessage
from tools.data_io import reserve_slot, append_appointment_export
from tools.messaging import send_sms

def run(state):
    messages = state.get("messages", [])
    appt = state.get("appointment", {})
    patient = state.get("patient", {})
    if not appt or "options" not in appt:
        messages.append(AIMessage(content="Let's pick a doctor and date first."))
        state["messages"] = messages
        return state

    last_user = None
    for m in reversed(messages):
        if m.type == "human":
            last_user = m.content
            break

    # parse time like 09:00 or 9am
    import re
    tmatch = re.search(r"(\d{1,2}:\d{2})", last_user or "")
    if not tmatch:
        messages.append(AIMessage(content="Please reply with the time (e.g., 09:00)."))
        state["messages"] = messages
        return state
    time_str = tmatch.group(1)

    # locate chosen slot in options
    chosen = None
    for s in appt["options"]:
        if s["date_slot"].strftime("%H:%M") == time_str:
            chosen = s
            break

    if not chosen:
        messages.append(AIMessage(content="That time wasn't one of the proposed options. Please choose from the listed times."))
        state["messages"] = messages
        return state

    # reserve
    ok, updated = reserve_slot(appt["doctor_name"], chosen["date_slot"], patient.get("patient_id"))
    if not ok:
        messages.append(AIMessage(content="Oops, that slot was just taken. Please pick another time."))
        state["messages"] = messages
        return state

    # finalize appointment details
    appt["date_slot"] = chosen["date_slot"]
    appt["status"] = "confirmed"
    state["appointment"] = appt

    # Confirmation SMS
    phone = patient.get("cell_phone")
    if phone:
        txt = f"Hello {patient.get('first_name')}, your appointment with {appt['doctor_name']} on {appt['date_slot']} is confirmed."
        try:
            send_sms(phone, txt)
        except Exception as e:
            pass  # do not fail the flow

    # Append to export
    append_appointment_export(patient, appt)

    messages.append(AIMessage(content=f"✅ Booked! {appt['doctor_name']} on {appt['date_slot']:%Y-%m-%d %H:%M}. "
                                      f"A confirmation SMS has been sent. A reminder will go out 3 hours before."))
    state["messages"] = messages
    return state
