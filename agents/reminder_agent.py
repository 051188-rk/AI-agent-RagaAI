# ai-scheduling-agent/agents/reminder_agent.py

from datetime import datetime, timedelta
import os
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone, UTC
from tools.messaging import send_sms
from tools.utils import sanitize_phone_in
import traceback

_scheduler = None

def _get_scheduler():
    global _scheduler
    if _scheduler is None:
        tz_name = os.environ.get("LOCAL_TZ", "UTC")
        try:
            tz = timezone(tz_name)
        except Exception:
            tz = UTC
        _scheduler = BackgroundScheduler(timezone=tz)
        _scheduler.start()
    return _scheduler

def _ensure_appt_datetime_tz(appt_dt):
    """
    Ensure appointment datetime is timezone-aware in LOCAL_TZ (or UTC fallback).
    Accepts naive or aware datetimes; returns an aware datetime.
    """
    if appt_dt is None:
        return None
    try:
        # If it's a pandas.Timestamp, convert
        import pandas as pd
        if isinstance(appt_dt, pd.Timestamp):
            appt_dt = appt_dt.to_pydatetime()
    except Exception:
        pass

    if appt_dt.tzinfo is not None:
        return appt_dt

    # Localize naive datetime to local TZ
    tz_name = os.environ.get("LOCAL_TZ", "UTC")
    try:
        tz = timezone(tz_name)
    except Exception:
        tz = UTC
    try:
        return tz.localize(appt_dt)
    except Exception:
        # If localize not supported, try replace tzinfo
        try:
            return appt_dt.replace(tzinfo=tz)
        except Exception:
            return appt_dt

def schedule_reminder_job(appt: dict):
    """
    Schedule reminders:
      - reminder 1: 24 hours before (if > now)
      - reminder 2: 3 hours before (if > now) [primary requirement]
    If the appointment is within 3 hours, send immediate reminder attempt.
    """
    # Validate input
    if not appt:
        print("Reminder scheduling aborted: empty appointment dict")
        return

    patient = appt.get("patient") or {}
    raw_phone = patient.get("cell_phone") or appt.get("patient_phone")
    phone = sanitize_phone_in(raw_phone)
    if not phone:
        print(f"Reminder Error: invalid phone number: {raw_phone}")
        return

    # Ensure proper timezone-aware datetime
    appt_time = appt.get("date_slot")
    appt_time = _ensure_appt_datetime_tz(appt_time)
    if not appt_time:
        print("Reminder Error: appointment datetime invalid or missing")
        return

    sched = _get_scheduler()
    now = datetime.now(appt_time.tzinfo)

    # Unique base id for jobs (use patient_id + timestamp)
    pid = str(patient.get("patient_id") or "unknown")
    ts = appt_time.strftime("%Y%m%dT%H%M")

    # 24-hours reminder
    run_time_1 = appt_time - timedelta(days=1)
    if run_time_1 > now:
        msg_1 = f"Reminder: Your appointment with {appt.get('doctor_name')} is tomorrow at {appt_time.strftime('%H:%M')}."
        job_id1 = f"reminder_24h_{pid}_{ts}"
        try:
            # remove existing job if any with same id
            if sched.get_job(job_id1):
                sched.remove_job(job_id1)
            sched.add_job(send_sms, 'date', run_date=run_time_1, args=[phone, msg_1], id=job_id1)
            print(f"Scheduled 24h reminder ({job_id1}) at {run_time_1} for {phone}")
        except Exception as e:
            print(f"Failed to schedule 24h reminder: {e}")
            traceback.print_exc()

    # 3-hours reminder (primary)
    run_time_2 = appt_time - timedelta(hours=3)
    job_id2 = f"reminder_3h_{pid}_{ts}"
    if run_time_2 > now:
        msg_2 = (
            f"Reminder: Your appointment with {appt.get('doctor_name')} is in 3 hours at {appt_time.strftime('%H:%M')}. "
            "Have you filled out your intake form? Reply YES to confirm or NO to cancel."
        )
        try:
            if sched.get_job(job_id2):
                sched.remove_job(job_id2)
            sched.add_job(send_sms, 'date', run_date=run_time_2, args=[phone, msg_2], id=job_id2)
            print(f"Scheduled 3h reminder ({job_id2}) at {run_time_2} for {phone}")
        except Exception as e:
            print(f"Failed to schedule 3h reminder: {e}")
            traceback.print_exc()
    else:
        # Appointment within 3 hours - send immediate reminder attempt
        try:
            send_sms(phone, f"Reminder: You have an appointment at {appt_time.strftime('%Y-%m-%d %H:%M')}.")
            print(f"Sent immediate reminder to {phone} for appt at {appt_time}")
        except Exception as e:
            print(f"Immediate reminder SMS failed for {phone}: {e}")
            traceback.print_exc()
