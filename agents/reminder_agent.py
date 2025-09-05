from datetime import datetime, timedelta
import os
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone, utc
from tools.messaging import send_sms

_scheduler = None

def _get_scheduler():
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone=os.environ.get("LOCAL_TZ","UTC"))
        _scheduler.start()
    return _scheduler

def schedule_reminder_job(appt: dict):
    # appt: {doctor_name, date_slot: datetime, ...}
    phone = appt.get("patient_phone") or appt.get("patient",{}).get("cell_phone")
    if not phone:
        return
    run_time = appt["date_slot"] - timedelta(hours=3)
    if run_time < datetime.now(run_time.tzinfo or None):
        # if within 3h already, send immediately
        try:
            send_sms(phone, "Reminder: You have an appointment in less than 3 hours.")
        except Exception:
            pass
        return
    msg = f"Reminder: You have an appointment with {appt['doctor_name']} at {appt['date_slot']:%Y-%m-%d %H:%M} (in ~3 hours)."
    sched = _get_scheduler()
    sched.add_job(send_sms, 'date', run_date=run_time, args=[phone, msg])
