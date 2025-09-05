# In ai-scheduling-agent/agents/intake_agent.py

from langchain_core.messages import AIMessage

def run(state):
    """
    This agent now acts as a simple entry point for form data.
    It confirms that data has been collected and passes it to the next step.
    """
    # --- IDEMPOTENCY CHECK ---
    # If the lookup agent has already run, it means intake is complete.
    if state.get("is_new_patient") is not None:
        return state

    messages = state.get("messages", [])
    patient = state.get("patient", {})

    # The form has already collected the data. This agent just confirms and proceeds.
    if patient.get("first_name"):
        messages.append(AIMessage(content=f"Thank you for providing your details, {patient.get('first_name', '')}."))
    
    state["messages"] = messages
    return state