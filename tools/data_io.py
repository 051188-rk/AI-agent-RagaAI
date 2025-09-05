# In ai-scheduling-agent/tools/data_io.py

import os
import threading
import warnings
from datetime import datetime, date, timedelta
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PATIENTS_CSV = os.path.join(DATA_DIR, "patients.csv")
# Use the actual Excel file for doctors
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
    # Read from Excel to match repository data
    if not os.path.exists(DOCTORS_XLSX):
        return pd.DataFrame()
    return pd.read_excel(DOCTORS_XLSX)

def _write_doctors(df: pd.DataFrame):
    with _lock:
        # Persist back to Excel
        try:
            df.to_excel(DOCTORS_XLSX, index=False)
        except Exception:
            # As a fallback, still attempt to write CSV sidecar to avoid data loss
            try:
                df.to_csv(os.path.splitext(DOCTORS_XLSX)[0] + ".csv", index=False)
            except Exception:
                pass

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
    if df.empty or not all([first_name, last_name, dob]):
        return None
    mask = (
        (df['first_name'].str.lower() == str(first_name).lower()) &
        (df['last_name'].str.lower() == str(last_name).lower()) &
        (pd.to_datetime(df['dob']).dt.date == pd.to_datetime(dob).date())
    )
    match = df[mask]
    if match.empty:
        return None
    row = match.iloc[0].to_dict()
    row['dob'] = pd.to_datetime(row['dob']).date().isoformat()
    return row

def ensure_patient_record(patient: dict):
    df = _read_patients()
    if df.empty:
        next_id = 1
        df = pd.DataFrame(columns=pd.read_csv(PATIENTS_CSV).columns)
    else:
        next_id = int(df['patient_id'].max()) + 1

    record = {k: patient.get(k) for k in df.columns if k != "patient_id"}
    record["patient_id"] = next_id
    
    # Suppress the FutureWarning for cleaner output
    with warnings.catch_warnings():
        warnings.simplefilter(action='ignore', category=FutureWarning)
        new_df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
        
    _write_patients(new_df)
    record['dob'] = pd.to_datetime(record['dob']).date().isoformat() if record.get('dob') else None
    return record

def find_available_slots(doctor_name: str, day: date, duration_min: int = 30):
    df = _read_doctors()
    if df.empty:
        return []

    # Normalize types
    df['date_slot'] = pd.to_datetime(df['date_slot'])
    if 'is_available' in df.columns:
        # Ensure boolean dtype
        df['is_available'] = df['is_available'].astype(bool)
    day_mask = df['date_slot'].dt.date == day
    doc_mask = df['doctor_name'] == doctor_name
    available_slots_df = df[doc_mask & day_mask & (df['is_available'] == True)].sort_values('date_slot')

    slots = []
    if duration_min == 30:
        for _, r in available_slots_df.iterrows():
            slots.append({"doctor_name": r['doctor_name'], "date_slot": r['date_slot'].to_pydatetime()})
        return slots
    
    if duration_min == 60:
        slot_times = available_slots_df['date_slot'].tolist()
        for i in range(len(slot_times) - 1):
            if slot_times[i+1] == slot_times[i] + timedelta(minutes=30):
                slots.append({"doctor_name": doctor_name, "date_slot": slot_times[i].to_pydatetime()})
        return slots

    return slots

def reserve_slot(doctor_name: str, date_time: datetime, patient_id: int, duration_min: int = 30):
    df = _read_doctors()
    if df.empty:
        return False, None
    
    df['date_slot'] = pd.to_datetime(df['date_slot'])
    
    slots_to_reserve = [pd.to_datetime(date_time)]
    if duration_min == 60:
        slots_to_reserve.append(pd.to_datetime(date_time) + timedelta(minutes=30))
    
    mask = (df['doctor_name'] == doctor_name) & (df['date_slot'].isin(slots_to_reserve))
    available_mask = mask & (df['is_available'] == True)
    
    if len(df[available_mask]) != len(slots_to_reserve):
        return False, None

    indices_to_update = df[available_mask].index
    df.loc[indices_to_update, 'is_available'] = False
    df.loc[indices_to_update, 'patient_id'] = int(patient_id)
    _write_doctors(df)
    
    return True, df.loc[indices_to_update].iloc[0].to_dict()

def append_appointment_export(patient: dict, appt: dict):
    df = _read_appts()
    row = {
        "patient_id": patient.get("patient_id"),
        "first_name": patient.get("first_name"),
        "last_name": patient.get("last_name"),
        "doctor_name": appt.get("doctor_name"),
        "date_slot": appt.get("date_slot")
    }
    
    with warnings.catch_warnings():
        warnings.simplefilter(action='ignore', category=FutureWarning)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

    _write_appts(df)

def list_doctor_names() -> list:
    """
    Return a sorted list of unique doctor names from the doctors schedule file.
    If the file is missing or empty, return an empty list.
    """
    df = _read_doctors()
    if df.empty or 'doctor_name' not in df.columns:
        return []
    names = sorted(df['doctor_name'].dropna().astype(str).unique().tolist())
    return names