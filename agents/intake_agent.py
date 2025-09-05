from langchain_core.messages import AIMessage
from tools.utils import extract_fields_from_text, required_fields_present

REQUIRED = ["first_name","last_name","dob"]

def run(state):
    messages = state.get("messages", [])
    last_user = None
    for m in reversed(messages):
        if m.type == "human":
            last_user = m.content
            break

    collected = state.get("patient", {})
    found = extract_fields_from_text(last_user)

    # merge newly found fields
    for k,v in found.items():
        collected[k] = v

    state["patient"] = collected

    if not required_fields_present(collected, REQUIRED):
        missing = [f for f in REQUIRED if f not in collected or not collected[f]]
        msg = ("Thanks. I still need the following required fields: " + ", ".join(missing) +
               ". You can also provide optional fields like gender, phone, email, and insurance.")
        messages.append(AIMessage(content=msg))
        state["messages"] = messages
        return state

    messages.append(AIMessage(content="Thanks! Checking if you are an existing patient..."))
    state["messages"] = messages
    return state
