# AI Scheduling Agent (LangGraph + LangChain + Gemini + Twilio + Streamlit)

<p align="center">
  <img src="https://raw.githubusercontent.com/051188-rk/AI-agent-RagaAI/main/dd.drawio.png" alt="architecture diagram" />
</p>

This project is a **rule-based multi-agent** appointment scheduler for a clinic, built with **LangGraph** (orchestration), **LangChain** (tools), **Gemini** (LLM), **Twilio** (SMS), and **Streamlit** (UI).

## Features
- Greeting → Intake (Streamlit forms) → Patient Lookup (CSV EMR) → Doctor List Prompt → Scheduling (Excel) → Confirmation (SMS + Email) → Reminders (SMS)
- Shows all available doctor names (from `data/doctors.xlsx`) right after Insurance Member ID so users can pick a valid name
- Phone numbers are normalized to E.164 with +91 default before sending SMS; invalid contacts are safely skipped
- Admin export to Excel/CSV of appointments
- Local-only execution (no deployment required)
- Uses your `.env` for **Gemini**, **Twilio**, and Email SMTP

## Quick Start
1. **Install** (Python 3.10+ recommended):
   ```bash
   pip install -r requirements.txt
   ```
2. **Create `.env`** in the project root (see sample below) with your keys.
3. **Add Data Files**:
   - `data/patients.csv` — 50 synthetic patients
   - `data/doctors.xlsx` — availability grid (doctor_name, specialty, date_slot, is_available, patient_id)
4. **Run**:
   ```bash
   streamlit run streamlit_app.py
   ```

### Sample .env
```
# Gemini
GOOGLE_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.0-pro

# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_FROM_NUMBER=+1XXXXXXXXXX
# Default country code for phone normalization (optional, defaults to +91)
DEFAULT_COUNTRY_CODE=+91

# Email SMTP (Gmail example)
EMAIL_USER=yourname@gmail.com
EMAIL_PASSWORD=your_app_password

# Local timezone for reminders (optional)
LOCAL_TZ=Asia/Kolkata
```

## Notes
- Confirmation is sent via SMS and Email. No intake form attachments are sent.
- Reminder SMS jobs are scheduled ~24 hours and 3 hours before the appointment (if in future) via APScheduler. If within 3 hours, an immediate reminder is attempted.
- Phone numbers are validated and normalized; if invalid (e.g., `nan`), notifications are skipped with a log.
- For Twilio trial, verify the destination phone numbers in your Twilio console.
- Default Gemini model is set from `GEMINI_MODEL` env (e.g. `gemini-2.5-pro` or `gemini-2.0-pro`).

## Structure
```
ai-scheduling-agent/
├── agents/
│   ├── greeting_agent.py
│   ├── intake_agent.py
│   ├── lookup_agent.py
│   ├── schedule_agent.py
│   ├── confirm_agent.py
│   └── reminder_agent.py
├── tools/
│   ├── data_io.py
│   ├── messaging.py
│   ├── llm.py
│   └── utils.py
├── data/                 # add your patients.csv and doctors.xlsx here
├── templates/
│   └── intake_form.json
├── docs/
│   └── technical_approach.md
├── agent_graph.py
├── streamlit_app.py
├── requirements.txt
└── .env
```

## Troubleshooting
- Twilio 21211 Invalid 'To' Number
  - Ensure the number is a real mobile and normalized to E.164 (e.g., `+9198XXXXXXXX`).
  - If on a Twilio trial, verify the destination number in Twilio console.
  - Confirm `TWILIO_FROM_NUMBER` is SMS-capable and configured to send to your region.

- Email sending errors
  - Ensure `EMAIL_USER` and `EMAIL_PASSWORD` are set; for Gmail, use an App Password.
  - Invalid patient emails are ignored safely; use a valid address.

## Current UX at a Glance
- After completing the intake, you’ll see a chat prompt.
