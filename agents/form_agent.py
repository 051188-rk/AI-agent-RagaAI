# In ai-scheduling-agent/agents/form_agent.py

import os
from langchain_core.messages import AIMessage
from tools.email import send_email_with_attachment

def run(state):
    """Sends the intake form via email."""
    messages = state.get("messages", [])
    patient = state.get("patient", {})
    email = patient.get("email")

    if not email:
        # This should ideally not happen if intake agent enforces email collection
        messages.append(AIMessage(content="Could not send intake form as no email is on file."))
        state["messages"] = messages
        return state

    # Define the path to the intake form
    # This assumes the script is run from the root of 'ai-scheduling-agent'
    form_path = os.path.join(os.getcwd(), "templates", "New Patient Intake Form.pdf")

    subject = "Your Upcoming Appointment: Please Complete the New Patient Form"
    body = (
        f"Dear {patient.get('first_name')},\n\n"
        "Thank you for scheduling an appointment with us.\n\n"
        "Please find the new patient intake form attached. "
        "Kindly complete it and email it back to us or bring it to your appointment.\n\n"
        "We look forward to seeing you.\n\n"
        "Best regards,\n"
        "MediCare Allergy & Wellness Center"
    )

    try:
        send_email_with_attachment(email, subject, body, form_path)
        messages.append(AIMessage(content="I've also sent the new patient intake form to your email. Please fill it out before your visit."))
    except Exception as e:
        print(f"Form Agent Error: {e}")
        messages.append(AIMessage(content="I was unable to send the patient intake form to your email. Please contact our office for assistance."))

    state["messages"] = messages
    return state