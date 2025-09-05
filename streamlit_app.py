import os
import streamlit as st
from dotenv import load_dotenv
from agent_graph import build_graph, run_turn

# Load env
load_dotenv()

st.set_page_config(page_title="Clinic Scheduler", page_icon="🩺", layout="centered")
st.title("🩺 Clinic Appointment Scheduler")

if "graph" not in st.session_state:
    st.session_state.graph = build_graph()
if "state" not in st.session_state:
    st.session_state.state = {"messages": []}



user_input = st.chat_input("Say hello to begin, or share your details...")
if user_input:
    st.session_state.state, reply = run_turn(st.session_state.graph, user_input, st.session_state.state)
    st.chat_message("assistant").write(reply)

# Render full history
for m in st.session_state.state.get("messages", []):
    if m.type == "human":
        st.chat_message("user").write(m.content)
    else:
        st.chat_message("assistant").write(m.content)

st.markdown("---")
st.caption("After confirmation, an SMS is sent and a reminder is scheduled for 3 hours before the appointment.")
