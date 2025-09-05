# In ai-scheduling-agent/streamlit_app.py

import streamlit as st
from dotenv import load_dotenv
from datetime import datetime
from langchain_core.messages import HumanMessage

from agent_graph import build_graph, AgentState, run_turn
from tools.data_io import list_doctor_names

# --- Initialization ---
load_dotenv()

st.set_page_config(page_title="Clinic Scheduler", page_icon="🩺", layout="centered")
st.title("🩺 Clinic Appointment Scheduler")

# --- Session State Setup ---
if "graph" not in st.session_state:
    st.session_state.graph = build_graph()
if "agent_state" not in st.session_state:
    st.session_state.agent_state = AgentState(messages=[])
if "messages" not in st.session_state:
    st.session_state.messages = []
if "step" not in st.session_state:
    st.session_state.step = "start"

# --- UI Helper Functions ---
def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})

def render_chat():
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# --- Main Application Flow ---

# Initial greeting
if st.session_state.step == "start":
    add_message("assistant", "Hello! I'm your clinic assistant. Let's get you ready for an appointment. Please provide your details below.")
    st.session_state.step = "get_first_name"
    st.rerun()

# Render chat history
render_chat()

# --- Part 1: Form-Based Data Collection ---
if st.session_state.step.startswith("get_"):
    if st.session_state.step == "get_first_name":
        with st.form("first_name_form", clear_on_submit=True):
            first_name = st.text_input("First Name")
            if st.form_submit_button("Continue"):
                add_message("user", first_name)
                add_message("assistant", f"Thanks, {first_name}. What is your last name?")
                st.session_state.agent_state.setdefault("patient", {})["first_name"] = first_name
                st.session_state.step = "get_last_name"
                st.rerun()

    elif st.session_state.step == "get_last_name":
        with st.form("last_name_form", clear_on_submit=True):
            last_name = st.text_input("Last Name")
            if st.form_submit_button("Continue"):
                add_message("user", last_name)
                add_message("assistant", "Got it. What's your date of birth?")
                st.session_state.agent_state["patient"]["last_name"] = last_name
                st.session_state.step = "get_dob"
                st.rerun()

    elif st.session_state.step == "get_dob":
        with st.form("dob_form", clear_on_submit=True):
            dob = st.date_input("Date of Birth", min_value=datetime(1920, 1, 1), value=datetime(2000, 1, 1))
            if st.form_submit_button("Continue"):
                dob_str = dob.strftime("%Y-%m-%d")
                add_message("user", dob_str)
                add_message("assistant", "Thank you. What's a good cell phone number?")
                st.session_state.agent_state["patient"]["dob"] = dob_str
                st.session_state.step = "get_cell_phone"
                st.rerun()

    elif st.session_state.step == "get_cell_phone":
        with st.form("phone_form", clear_on_submit=True):
            phone = st.text_input("Cell Phone")
            if st.form_submit_button("Continue"):
                add_message("user", phone)
                add_message("assistant", "Perfect. And your email address?")
                st.session_state.agent_state["patient"]["cell_phone"] = phone
                st.session_state.step = "get_email"
                st.rerun()

    elif st.session_state.step == "get_email":
        with st.form("email_form", clear_on_submit=True):
            email = st.text_input("Email")
            if st.form_submit_button("Continue"):
                add_message("user", email)
                add_message("assistant", "Great. What is your insurance provider?")
                st.session_state.agent_state["patient"]["email"] = email
                st.session_state.step = "get_primary_insurance"
                st.rerun()

    elif st.session_state.step == "get_primary_insurance":
        with st.form("ins_form", clear_on_submit=True):
            insurance = st.text_input("Insurance Provider")
            if st.form_submit_button("Continue"):
                add_message("user", insurance)
                add_message("assistant", "And your Member ID?")
                st.session_state.agent_state["patient"]["primary_insurance"] = insurance
                st.session_state.step = "get_primary_member_id"
                st.rerun()

    elif st.session_state.step == "get_primary_member_id":
        with st.form("member_id_form", clear_on_submit=True):
            member_id = st.text_input("Member ID")
            if st.form_submit_button("Continue"):
                add_message("user", member_id)
                st.session_state.agent_state["patient"]["primary_member_id"] = member_id
                # Show available doctor names to help the user choose
                try:
                    names = list_doctor_names()
                    if names:
                        add_message("assistant", "Available doctors: " + ", ".join(names))
                except Exception as e:
                    # Do not block the flow if listing fails
                    pass
                st.session_state.step = "run_backend_lookup"
                st.rerun()


# --- Part 2: Backend Logic and Conversation ---
elif st.session_state.step == "run_backend_lookup":
    with st.spinner("Looking up your patient record..."):
        # Run the graph from the beginning. It will stop after the 'lookup' agent.
        final_state, reply = run_turn(st.session_state.graph, "", st.session_state.agent_state)
        st.session_state.agent_state = final_state
        # Display all the new messages from the backend
        for msg in final_state['messages']:
            if not any(m['content'] == msg.content for m in st.session_state.messages):
                 add_message("assistant", msg.content)
        st.session_state.step = "conversational_scheduling"
        st.rerun()

elif st.session_state.step == "conversational_scheduling":
    # The form part is done, now we use the chat input for scheduling
    user_input = st.chat_input("Enter doctor and date, or select a time...")
    if user_input:
        add_message("user", user_input)
        with st.spinner("Thinking..."):
            # Run the graph again with the new user input
            final_state, reply = run_turn(st.session_state.graph, user_input, st.session_state.agent_state)
            st.session_state.agent_state = final_state
            if reply:
                add_message("assistant", reply)

        # Check if the appointment is confirmed
        if final_state.get("appointment", {}).get("status") == 'confirmed':
            st.session_state.step = "done"

        st.rerun()

elif st.session_state.step == "done":
    st.success("✅ Your appointment is booked! A confirmation has been sent via SMS/email.")
    if st.button("Start Over"):
        st.session_state.clear()
        st.rerun()