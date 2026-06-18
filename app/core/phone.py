import re


def process_phone(phone: str) -> str | None:
    if not isinstance(phone, str):
        return None

    phone = phone.strip()

    if phone.startswith("+"):
        phone = phone[1:]

    if not re.fullmatch(r"\d+", phone):
        return None

    if phone.startswith("0"):
        phone = phone[1:]

    if phone.startswith("254"):
        phone = phone[3:]

    if len(phone) != 9:
        return None

    if phone[0] not in ("7", "1"):
        return None

    return "254" + phone
