from langchain_core.messages import AIMessage
from tools.llm import get_llm

def run(state):
    messages = state.get("messages", [])
    # If first time, greet; else, only react if last was user
    llm = get_llm()
    if len(messages) == 1:
        reply = ("Hello! I'm your clinic assistant. I can help you book an appointment. "
                 "To get started, please share your full name and date of birth (YYYY-MM-DD).")
    else:
        # Keep it simple—defer to Intake agent for structured data collection
        reply = ("Great—let's gather your details to find or create your record. "
                 "Please provide: First name, Last name, and DOB (YYYY-MM-DD).")
    messages.append(AIMessage(content=reply))
    state["messages"] = messages
    return state
