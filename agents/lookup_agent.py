# In ai-scheduling-agent/agents/lookup_agent.py

from langchain_core.messages import AIMessage
from tools.data_io import find_patient_by_name_dob, ensure_patient_record

def run(state):
    # --- IDEMPOTENCY CHECK ---
    # If we have already determined the patient's status, do not run this agent again.
    if state.get("is_new_patient") is not None:
        return state

    messages = state.get("messages", [])
    patient = state.get("patient", {})
    
    if not patient.get("first_name") or not patient.get("last_name") or not patient.get("dob"):
        messages.append(AIMessage(content="I'm sorry, I seem to be missing some of your details. Let's start over."))
        state["messages"] = messages
        # In a real scenario, you might want to route back to the start
        return state

    record = find_patient_by_name_dob(patient.get("first_name"), patient.get("last_name"), patient.get("dob"))
    
    if record is None:
        # Create a new patient record
        record = ensure_patient_record(patient)
        state["is_new_patient"] = True
        messages.append(AIMessage(content=f"I didn't find you in our records, so I've created a new patient profile (ID: {record['patient_id']})."))
    else:
        # Patient found
        state["is_new_patient"] = False
        messages.append(AIMessage(content=f"Found your record (Patient ID: {record['patient_id']}). Welcome back!"))

    # Sync the full, correct record back to the main state
    state["patient"].update(record)

    messages.append(AIMessage(content="Which doctor and date would you like to schedule an appointment for? (e.g., Dr. Alice Wong on 2025-09-15)"))
    state["messages"] = messages
    
    return state