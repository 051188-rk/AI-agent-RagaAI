# In ai-scheduling-agent/tools/utils.py

import re
from datetime import datetime
from typing import Optional

def sanitize_phone_in(phone: object, default_cc: str = "+91") -> Optional[str]:
    """
    Normalize a user-provided Indian phone number to E.164 or return None if invalid.
    Accepts numbers with spaces/dashes/parentheses, 10-digit local, or 0-prefixed 11-digit.
    Returns string like '+9198XXXXXXXX' or None when not possible.
    """
    if phone is None:
        return None
    s = str(phone).strip()
    if not s or s.lower() == 'nan':
        return None
    # Remove common formatting chars
    s = re.sub(r"[\s\-()]+", "", s)
    # If already E.164
    if s.startswith('+') and re.fullmatch(r"\+\d{8,15}", s):
        return s
    # Digits only
    digits = re.sub(r"\D", "", s)
    cc = default_cc.lstrip('+')
    if digits.startswith(cc) and len(digits) > len(cc):
        return f"+{digits}"
    if len(digits) == 10:
        return f"+{cc}{digits}"
    if len(digits) == 11 and digits.startswith('0'):
        return f"+{cc}{digits[1:]}"
    # Fallback: try '+' + digits if length is plausible
    if 8 <= len(digits) <= 15:
        return f"+{digits}"
    return None

def sanitize_email(email: object) -> Optional[str]:
    """Return a lowercased email string if valid-looking, else None. Protects against float NaN."""
    if email is None:
        return None
    s = str(email).strip()
    if not s or s.lower() == 'nan':
        return None
    m = re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", s)
    return s.lower() if m else None

def extract_fields_from_text(text: str):
    if not text:
        return {}
    out = {}

    # Standard labeled fields
    m = re.search(r'first\s*name\s*[:=-]\s*([A-Za-z]+)', text, re.I)
    if m: out['first_name'] = m.group(1).strip()
    m = re.search(r'last\s*name\s*[:=-]\s*([A-Za-z\s]+)', text, re.I) # Allow spaces in last name
    if m: out['last_name'] = m.group(1).strip()

    # Name heuristic for inputs like "Rakesh Kumar Banik"
    if 'first_name' not in out or 'last_name' not in out:
        # Remove other known patterns to isolate the name
        name_text = re.sub(r'(19|20)\d\d-\d\d-\d\d', '', text).strip()
        name_text = re.sub(r'(\+?\d[\d\-\s]{7,}\d)', '', name_text).strip()
        name_text = re.sub(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', '', name_text).strip()
        tokens = re.findall(r"[A-Za-z']+", name_text)

        if len(tokens) == 2:
            out.setdefault('first_name', tokens[0])
            out.setdefault('last_name', tokens[1])
        elif len(tokens) > 2:
            # Assume first name is all but the last word
            out.setdefault('first_name', " ".join(tokens[:-1]))
            out.setdefault('last_name', tokens[-1])

    # DOB YYYY-MM-DD
    m = re.search(r'((19|20)\d\d-\d{1,2}-\d{1,2})', text)
    if m: out['dob'] = m.group(1)

    # Phone number (improved regex)
    m = re.search(r'(\+?\d{1,2}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', text)
    if m: out['cell_phone'] = re.sub(r'[\s().-]', '', m.group(0))

    # Email
    m = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text)
    if m: out['email'] = m.group(0)

    # Insurance
    m = re.search(r'insurance\s*[:=-]\s*([A-Za-z]+)', text, re.I)
    if m: out['primary_insurance'] = m.group(1).strip()
    m = re.search(r'member\s*id\s*[:=-]\s*([A-Za-z0-9]+)', text, re.I)
    if m: out['primary_member_id'] = m.group(1).strip()


    return out

def required_fields_present(data: dict, fields: list[str]):
    for f in fields:
        if f not in data or not data[f]:
            return False
    return True