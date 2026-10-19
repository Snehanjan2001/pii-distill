"""Contact-point validators: email, phone, IP address, postal code."""

import ipaddress
import re

import phonenumbers

_ATOM = r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
_EMAIL = re.compile(
    rf"{_ATOM}(?:\.{_ATOM})*@(?:[A-Za-z0-9](?:[A-Za-z0-9-]{{0,61}}[A-Za-z0-9])?\.)+[A-Za-z]{{2,63}}"
)

# Digits and phone punctuation only, plus an optional extension. Keeps label words like
# "Tel:" out, which phonenumbers.parse would otherwise skip over silently.
_PHONE_CHARS = re.compile(r"\+?[0-9()\-. /]+(?:\s*(?:ext\.?|x)\s*[0-9]{1,6})?", re.IGNORECASE)

_POSTAL = re.compile(
    r"[0-9]{5}(?:-[0-9]{4})?"  # US ZIP, ZIP+4
    r"|GIR ?0AA|[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}"  # UK
    r"|[ABCEGHJ-NPRSTVXY][0-9][ABCEGHJ-NPRSTV-Z] ?[0-9][ABCEGHJ-NPRSTV-Z][0-9]",  # Canada
    re.IGNORECASE,
)


def is_valid_email(s: str) -> bool:
    """Practical email check (not full RFC 5322): dot-atom local part, dotted domain."""
    local, _, _ = s.partition("@")
    return len(s) <= 254 and len(local) <= 64 and bool(_EMAIL.fullmatch(s))


def is_valid_phone(s: str, region: str = "US") -> bool:
    """Phone number valid per libphonenumber metadata; numbers without +CC use `region`."""
    if not _PHONE_CHARS.fullmatch(s) or sum(ch.isdigit() for ch in s) < 7:
        return False
    try:
        return phonenumbers.is_valid_number(phonenumbers.parse(s, region))
    except phonenumbers.NumberParseException:
        return False


def is_valid_ip(s: str) -> bool:
    """IPv4 or IPv6 address."""
    try:
        ipaddress.ip_address(s)
    except ValueError:
        return False
    return True


def is_valid_postal_code(s: str) -> bool:
    """US, UK or Canadian postal code. Format only: any 5 digits pass, context decides."""
    return bool(_POSTAL.fullmatch(s)) and s != "00000"
