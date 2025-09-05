import os
import threading
from datetime import datetime, date
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PATIENTS_CSV = os.path.join(DATA_DIR, "patients.csv")
DOCTORS_XLSX = os.path.join(DATA_DIR, "doctors.xlsx")
APPTS_CSV = os.path.join(DATA_DIR, "appointments.csv")
APPTS_XLSX = os.path.join(DATA_DIR, "appointments.xlsx")

_lock = threading.Lock()

def _read_patients():
    if not os.path.exists(PATIENTS_CSV):
        return pd.DataFrame()
    return pd.read_csv(PATIENTS_CSV)

def _write_patients(df: pd.DataFrame):
    with _lock:
        df.to_csv(PATIENTS_CSV, index=False)

def _read_doctors():
    if not os.path.exists(DOCTORS_XLSX):
        return pd.DataFrame()
    return pd.read_excel(DOCTORS_XLSX)

def _write_doctors(df: pd.DataFrame):
    with _lock:
        df.to_excel(DOCTORS_XLSX, index=False)

def _read_appts():
    if not os.path.exists(APPTS_CSV):
        return pd.DataFrame(columns=["patient_id","first_name","last_name","doctor_name","date_slot"])
    return pd.read_csv(APPTS_CSV, parse_dates=["date_slot"])

def _write_appts(df: pd.DataFrame):
    with _lock:
        df.to_csv(APPTS_CSV, index=False)
        try:
            df.to_excel(APPTS_XLSX, index=False)
        except Exception:
            pass

def find_patient_by_name_dob(first_name: str, last_name: str, dob: str):
    df = _read_patients()
    if df.empty:
        return None
    # normalize
    mask = (
        (df['first_name'].str.lower() == str(first_name).lower()) &
        (df['last_name'].str.lower() == str(last_name).lower()) &
        (pd.to_datetime(df['dob']).dt.date == pd.to_datetime(dob).date())
    )
    match = df[mask]
    if match.empty:
        return None
    row = match.iloc[0].to_dict()
    # convert dates
    row['dob'] = pd.to_datetime(row['dob']).date().isoformat()
    return row

def ensure_patient_record(patient: dict):
    df = _read_patients()
    if df.empty:
        next_id = 1
        df = pd.DataFrame(columns=[
            "patient_id","first_name","middle_initial","last_name","dob","gender",
            "cell_phone","email","street","city","state","zip_code",
            "emergency_contact","emergency_relation","emergency_phone",
            "primary_insurance","primary_member_id","primary_group",
            "secondary_insurance","secondary_member_id","secondary_group"
        ])
    else:
        next_id = int(df['patient_id'].max()) + 1

    record = {k: patient.get(k) for k in df.columns if k != "patient_id"}
    record["patient_id"] = next_id
    new_df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    _write_patients(new_df)
    record['dob'] = pd.to_datetime(record['dob']).date().isoformat() if record.get('dob') else None
    return record

def find_available_slots(doctor_name: str, day: date):
    df = _read_doctors()
    if df.empty:
        return []
    # Expect columns: doctor_name, specialty, date_slot, is_available, patient_id
    df['date_slot'] = pd.to_datetime(df['date_slot'])
    day_mask = df['date_slot'].dt.date == day
    mask = (df['doctor_name'] == doctor_name) & (df['is_available'] == True) & day_mask
    rows = df[mask].sort_values('date_slot')
    slots = []
    for _, r in rows.iterrows():
        slots.append({
            "doctor_name": r['doctor_name'],
            "date_slot": r['date_slot'].to_pydatetime()
        })
    return slots

def reserve_slot(doctor_name: str, date_time: datetime, patient_id: int):
    df = _read_doctors()
    if df.empty:
        return False, None
    df['date_slot'] = pd.to_datetime(df['date_slot'])
    mask = (df['doctor_name']==doctor_name) & (df['date_slot']==pd.to_datetime(date_time))
    idx = df[mask & (df['is_available']==True)].index
    if len(idx)==0:
        return False, None
    df.loc[idx, 'is_available'] = False
    df.loc[idx, 'patient_id'] = patient_id
    _write_doctors(df)
    return True, df.loc[idx].iloc[0].to_dict()

def append_appointment_export(patient: dict, appt: dict):
    df = _read_appts()
    row = {
        "patient_id": patient.get("patient_id"),
        "first_name": patient.get("first_name"),
        "last_name": patient.get("last_name"),
        "doctor_name": appt.get("doctor_name"),
        "date_slot": appt.get("date_slot")
    }
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    _write_appts(df)
