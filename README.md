# AI Scheduling Agent (LangGraph + LangChain + Gemini + Twilio + Streamlit)

This project is a **rule-based multi-agent** appointment scheduler for a clinic, built with **LangGraph** (orchestration), **LangChain** (tools), **Gemini** (LLM), **Twilio** (SMS), and **Streamlit** (UI).

## Features
- Greeting → Intake → Patient Lookup (CSV EMR) → Scheduling (Excel) → Confirmation (SMS) → 3h Reminder (SMS)
- Admin export to Excel/CSV of appointments
- Local-only execution (no deployment required)
- Uses your `.env` for **Gemini** and **Twilio**

## Quick Start
1. **Install** (Python 3.10+ recommended):
   ```bash
   pip install -r requirements.txt
   ```
2. **Create `.env`** in the project root (see `.env.example`) with your keys.
3. **Add Data Files** (you said you'll generate them):
   - `data/patients.csv` — 50 synthetic patients
   - `data/doctors.xlsx` — availability grid (doctor_name, specialty, date_slot, is_available, patient_id)
4. **Run**:
   ```bash
   streamlit run streamlit_app.py
   ```

## Notes
- Reminder SMS is scheduled **3 hours** before the appointment via a background scheduler (APScheduler).
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
└── .env.example
```
