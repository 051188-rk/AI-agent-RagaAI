import re
from datetime import datetime

def extract_fields_from_text(text: str):
    if not text:
        return {}
    out = {}
    # very naive parsing just to get started; users can refine
    # first/last names: look for 'first name: X', etc.
    m = re.search(r'first\s*name\s*[:=-]\s*([A-Za-z]+)', text, re.I)
    if m: out['first_name'] = m.group(1).strip()
    m = re.search(r'last\s*name\s*[:=-]\s*([A-Za-z]+)', text, re.I)
    if m: out['last_name'] = m.group(1).strip()
    # if not found, try split heuristic "John Doe"
    if 'first_name' not in out or 'last_name' not in out:
        tokens = re.findall(r"[A-Za-z']+", text)
        if len(tokens) >= 2:
            out.setdefault('first_name', tokens[0])
            out.setdefault('last_name', tokens[1])

    # DOB YYYY-MM-DD
    m = re.search(r'(19|20)\d\d-\d\d-\d\d', text)
    if m: out['dob'] = m.group(0)

    # phone, simple
    m = re.search(r'(\+?\d[\d\-\s]{7,}\d)', text)
    if m: out['cell_phone'] = re.sub(r'\s+', '', m.group(1))

    # email
    m = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text)
    if m: out['email'] = m.group(0)

    return out

def required_fields_present(data: dict, fields: list[str]):
    for f in fields:
        if f not in data or not data[f]:
            return False
    return True
