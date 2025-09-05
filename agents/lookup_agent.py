from langchain_core.messages import AIMessage
from tools.data_io import find_patient_by_name_dob, ensure_patient_record

def run(state):
    messages = state.get("messages", [])
    patient = state.get("patient", {})
    if not patient:
        messages.append(AIMessage(content="I couldn't parse your details. Please re-enter name and DOB."))
        state["messages"] = messages
        state["error"] = "no_patient_details"
        return state

    record = find_patient_by_name_dob(patient.get("first_name"), patient.get("last_name"), patient.get("dob"))
    if record is None:
        # create new record
        record = ensure_patient_record(patient)
        state["is_new_patient"] = True
        messages.append(AIMessage(content=f"I didn't find you in our records, so I created a new patient profile (ID: {record['patient_id']})."))
    else:
        state["is_new_patient"] = False
        messages.append(AIMessage(content=f"Found your record (Patient ID: {record['patient_id']}). Welcome back!"))

    # Sync normalized record back to state.patient
    for k,v in record.items():
        if k not in ["internal_notes"]:
            state["patient"][k] = v

    messages.append(AIMessage(content="Which doctor and date do you prefer? (e.g., Dr. Alice Wong on 2025-09-06)"))
    state["messages"] = messages
    return state
