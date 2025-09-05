# Technical Approach (1 page)

**Architecture**  
- **LangGraph** orchestrates a rule-based multi-agent flow: Greeting → Intake → Patient Lookup → Schedule → Confirm → (spawn) Reminder.  
- **LangChain** tools handle data (CSV/Excel) and Twilio SMS.  
- **Gemini** (via Google Generative AI API) provides LLM reasoning in each agent.  
- **Streamlit** hosts the chat interface; state is maintained in LangGraph + session state.

**Framework Choice**  
- **LangGraph** was chosen over minimal custom FSM because it encodes multi-agent workflows as a state graph with explicit nodes/edges, improving reliability and testability.  
- **LangChain** gives batteries-included tools for CSV/Excel/Twilio and easy LLM plumbing.  
- **Gemini** 2.5 Pro API is used because it's free to start and offers strong reasoning.

**Integration Strategy**  
- **EMR**: Read/write `data/patients.csv` using pandas. Fuzzy match by name + DOB; create new row if not found.  
- **Schedules**: Read/write `data/doctors.xlsx` using pandas/openpyxl. Filter rows with `is_available == True`, then reserve chosen slot by writing `is_available=False` and `patient_id`.  
- **Communication**: Twilio is wrapped in `tools/messaging.py` for confirmations and a scheduled reminder 3 hours before the appointment.  
- **Export**: Append confirmed bookings to `data/appointments.csv` and (re)generate `data/appointments.xlsx` for admin.

**Challenges & Solutions**  
- **Ambiguous user inputs**: Intake agent validates required fields; fallbacks prompt user to re-enter.  
- **Data races on files**: Simple file lock context to serialize writes.  
- **Scheduling reminders**: Use APScheduler to schedule a single reminder at `start_time - 3h`; if within 3h, send immediately.  
- **LLM determinism**: Rule-based edges in LangGraph enforce flow boundaries; prompts steer extraction in Intake Agent.

**Security**  
- No PHI leaves local machine; environment variables used for API keys.  
- Twilio numbers sanitized; optional allowlist for testing.

**Success Metrics**  
- End-to-end booking flow completes; SMS sent; admin export generated.
