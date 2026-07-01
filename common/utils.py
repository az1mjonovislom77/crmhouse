import re


def normalize_phone(phone: str) -> str:
    if not phone:
        return ''
    digits = re.sub(r'\D', '', phone)
    return digits[-9:] if len(digits) >= 9 else digits
