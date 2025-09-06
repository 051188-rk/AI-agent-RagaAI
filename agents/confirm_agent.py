# ai-scheduling-agent/agents/confirm_agent.py

from datetime import datetime
from langchain_core.messages import AIMessage, HumanMessage
from tools.data_io import reserve_slot, append_appointment_export
from tools.messaging import send_sms
from tools.email import send_email
from tools.utils import sanitize_phone_in, sanitize_email
import re
import traceback

def _normalize_time_token(token: str):
    """
    Convert various user time representations into HH:MM (24-hour) string.
    Accepts: '9', '9am', '9:00', '09:30', '9:30pm', '21:00' etc.
    Returns a string "HH:MM" or None.
    """
    if not token:
        return None
    token = token.strip().lower()
    # Handle compact forms like '1130' or '930pm'
    m = re.match(r'^(?P<h>\d{1,2})(?P<m>\d{2})\s*(?P<ampm>am|pm)?$', token)
    if m:
        h = int(m.group('h'))
        minute = int(m.group('m'))
        ampm = m.group('ampm')
        if ampm:
            if ampm == 'pm' and h != 12:
                h += 12
            if ampm == 'am' and h == 12:
                h = 0
        if 0 <= h <= 23 and 0 <= minute <= 59:
            return f"{h:02d}:{minute:02d}"

    # Handle separators ':' or '.' like '11.30' or '9:30pm' and bare hour like '9am'
    m = re.match(r'^(?P<h>\d{1,2})(?::|\.)?(?P<m>\d{2})?\s*(?P<ampm>am|pm)?$', token)
    if not m:
        return None
    h = int(m.group('h'))
    minute = int(m.group('m')) if m.group('m') else 0
    ampm = m.group('ampm')
    if ampm:
        if ampm == 'pm' and h != 12:
            h += 12
        if ampm == 'am' and h == 12:
            h = 0
    # Validate range
    if not (0 <= h <= 23 and 0 <= minute <= 59):
        return None
    return f"{h:02d}:{minute:02d}"

def _extract_time_from_text(text: str):
    """
    Find a time-like token in text. Returns the portion likely representing time.
    """
    if not text:
        return None
    # try direct HH:MM or H:MM or H formats, with optional am/pm
    # capture tokens such as 09:30, 9:30am, 9am, 9
    patterns = [
        r'(\d{1,2}:\d{2}\s*(?:am|pm)?)',
        r'(\d{3,4}\s*(?:am|pm)?)',
        r'(\d{1,2}\s*(?:am|pm))',
        r'(\d{1,2}[\.:]\d{2}\s*(?:am|pm)?)',
        r'(\d{1,2}:\d{2})',
        r'\b(\d{1,2})\b'
    ]
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            return m.group(1)
    return None

def _extract_option_index(text: str, max_len: int):
    """
    Try to extract an option index from the user's message.
    Accepts formats like '1', '2', 'option 3', 'choose 1', etc.
    Returns zero-based index or None if not found/invalid.
    """
    if not text:
        return None
    # Look for a standalone small integer 1..max_len
    m = re.search(r"\b(\d{1,2})\b", text)
    if m:
        try:
            idx = int(m.group(1))
            if 1 <= idx <= max_len:
                return idx - 1
        except Exception:
            pass
    # Look for 'option X' pattern
    m = re.search(r"option\s*(\d{1,2})", text, flags=re.IGNORECASE)
    if m:
        try:
            idx = int(m.group(1))
            if 1 <= idx <= max_len:
                return idx - 1
        except Exception:
            pass
    return None

def run(state):
    """
    Confirm agent:
    - Expects state["appointment"]["options"] to be a list of candidate slots (each has 'date_slot' datetime).
    - Expects user to reply with a time (flexible formats).
    - Reserves the slot via tools.data_io.reserve_slot(doctor_name, datetime, patient_id).
    - Sends SMS and Email confirmations; logs any send errors.
    """
    messages = state.get("messages", [])
    appt = state.get("appointment", {})
    patient = state.get("patient", {})

    # Guard: must have options
    if not appt or "options" not in appt:
        # nothing to do
        return state

    # Find last human message
    last_user = None
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            last_user = m.content
            break

    if not last_user:
        return state

    # Try option index selection first
    idx = _extract_option_index(last_user, len(appt["options"]))
    normalized_time = None
    if idx is None:
        # Extract and normalize time token from the user's reply
        raw_time_token = _extract_time_from_text(last_user)
        normalized_time = _normalize_time_token(raw_time_token) if raw_time_token else None
        if not normalized_time:
            messages.append(AIMessage(content="Please reply with one of the available times (examples: '09:30', '9:30am', or '9') or the option number (e.g., '1')."))
            state["messages"] = messages
            return state

    # Match normalized_time to one of the proposed options
    chosen = None
    if idx is not None:
        # Select by numeric option
        try:
            chosen = appt["options"][idx]
        except Exception:
            chosen = None
    
    for s in appt["options"] if chosen is None else []:
        slot_dt = s.get("date_slot")
        try:
            # slot_dt might be a pandas.Timestamp or datetime
            slot_str = slot_dt.strftime("%H:%M")
        except Exception:
            # Attempt conversion if needed
            try:
                import pandas as pd
                slot_dt = pd.to_datetime(slot_dt).to_pydatetime()
                slot_str = slot_dt.strftime("%H:%M")
            except Exception:
                slot_str = None

        if slot_str == normalized_time:
            chosen = s
            break

    # If no exact match and user provided only hour (e.g., '11:00' derived from '11'),
    # try to pick a slot within the same hour (prefer :00 then :30)
    if chosen is None and normalized_time and normalized_time.endswith(":00"):
        target_hour = normalized_time.split(":")[0]
        same_hour = []
        for s in appt["options"]:
            slot_dt = s.get("date_slot")
            try:
                hh = slot_dt.strftime("%H")
                mm = slot_dt.strftime("%M")
            except Exception:
                try:
                    import pandas as pd
                    slot_dt = pd.to_datetime(slot_dt).to_pydatetime()
                    hh = slot_dt.strftime("%H")
                    mm = slot_dt.strftime("%M")
                except Exception:
                    continue
            if hh == target_hour:
                same_hour.append((mm, s))
        if same_hour:
            # Prefer :00 over :30, else the earliest minute
            same_hour.sort()
            for mm, s in same_hour:
                if mm in ("00", "30"):
                    chosen = s
                    break
            if not chosen:
                chosen = same_hour[0][1]

    if not chosen:
        messages.append(AIMessage(content="That selection wasn't one of the proposed options. Please reply with a listed time (e.g., '09:30') or the option number (e.g., '1')."))
        state["messages"] = messages
        return state

    # Reserve the slot
    patient_id = patient.get("patient_id")
    try:
        # reserve_slot expected signature: (doctor_name, date_time, patient_id)
        ok, reserved_row = reserve_slot(appt["doctor_name"], chosen["date_slot"], patient_id)
    except TypeError:
        # If reserve_slot supports an optional duration param (backwards compatible),
        # try calling without duration too
        try:
            ok, reserved_row = reserve_slot(appt["doctor_name"], chosen["date_slot"], patient_id, appt.get("duration_min", 30))
        except Exception as e:
            ok = False
            reserved_row = None
            print("reserve_slot call failed:", e)
    except Exception as e:
        ok = False
        reserved_row = None
        print("reserve_slot exception:", e)
        traceback.print_exc()

    if not ok:
        messages.append(AIMessage(content="Sorry — that slot was just taken by someone else. Please choose another available time."))
        state["messages"] = messages
        # clear options to allow re-selection
        state["appointment"].pop("options", None)
        return state

    # Finalize appointment details
    appt["date_slot"] = chosen["date_slot"]
    appt["status"] = "confirmed"
    # Ensure patient info is attached for reminders
    appt["patient"] = patient
    state["appointment"] = appt

    # --- Notifications ---
    # SMS
    normalized_phone = sanitize_phone_in(patient.get("cell_phone"))
    if normalized_phone:
        # persist normalized phone back into patient record in state
        patient["cell_phone"] = normalized_phone
        sms_text = (
            f"Hello {patient.get('first_name')}, your appointment with {appt['doctor_name']} "
            f"on {appt['date_slot']:%Y-%m-%d at %H:%M} is confirmed. See you then!"
        )
        try:
            sid = send_sms(normalized_phone, sms_text)
            print(f"Confirmation SMS sent. SID: {sid} to {normalized_phone}")
        except Exception as e:
            print(f"Confirmation SMS failed for {normalized_phone}: {e}")

    # Email
    sanitized_email = sanitize_email(patient.get("email"))
    if sanitized_email:
        patient["email"] = sanitized_email
        subject = "Appointment Confirmation"
        body = (
            f"Dear {patient.get('first_name')} {patient.get('last_name')},\n\n"
            f"Your appointment is confirmed.\n\n"
            f"Doctor: {appt['doctor_name']}\n"
            f"Date & Time: {appt['date_slot']:%Y-%m-%d %H:%M}\n\n"
            "If you have any questions, reply to this email.\n\n"
            "Thank you,\nClinic Team"
        )
        try:
            send_email(sanitized_email, subject, body)
            print(f"Confirmation email sent to {sanitized_email}")
        except Exception as e:
            print(f"Confirmation email failed for {sanitized_email}: {e}")

    # Append to admin export
    try:
        append_appointment_export(patient, appt)
    except Exception as e:
        print(f"Failed to append appointment export: {e}")

    # Inform user in chat and set state
    notify_bits = []
    if normalized_phone:
        notify_bits.append(f"SMS to {normalized_phone}")
    if sanitized_email:
        notify_bits.append(f"email to {sanitized_email}")
    notify_text = ", ".join(notify_bits) if notify_bits else "no contact available"

    messages.append(AIMessage(content=f"✅ Booked! {appt['doctor_name']} on {appt['date_slot']:%Y-%m-%d %H:%M}. Confirmation sent via {notify_text}."))
    state["messages"] = messages
    # persist corrected patient back into state
    state["patient"] = patient

    return state
