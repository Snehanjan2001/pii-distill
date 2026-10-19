"""Checksum and structure validators: payment cards, IBANs, US SSNs.

Inputs are expected to be NFKC-normalized first (see normalize.nfkc), so only ASCII
digits are accepted here.
"""

import re

# ponytail: common SEPA countries only; add entries as the generator covers more countries.
IBAN_LENGTHS = {
    "AT": 20, "BE": 16, "CH": 21, "CZ": 24, "DE": 22, "DK": 18, "ES": 24, "FI": 18,
    "FR": 27, "GB": 22, "IE": 22, "IT": 27, "LU": 20, "NL": 18, "NO": 15, "PL": 28,
    "PT": 25, "SE": 24,
}  # fmt: skip


def is_valid_luhn(s: str) -> bool:
    """Payment card number (PAN): 12-19 digits, optional spaces/dashes, Luhn checksum."""
    if not re.fullmatch(r"[0-9]+(?:[ -][0-9]+)*", s):
        return False
    digits = re.sub(r"[ -]", "", s)
    if not 12 <= len(digits) <= 19 or digits[0] == "0":
        return False
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def is_valid_iban(s: str) -> bool:
    """IBAN: known country, exact country length, ISO 7064 mod-97 checksum."""
    v = s.replace(" ", "").upper()
    if not re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z0-9]+", v):
        return False
    if IBAN_LENGTHS.get(v[:2]) != len(v):
        return False
    rearranged = v[4:] + v[:4]
    return int("".join(str(int(ch, 36)) for ch in rearranged)) % 97 == 1


def is_valid_ssn(s: str) -> bool:
    """US SSN: AAA-GG-SSSS (dashes, spaces or none, used consistently), SSA-assignable ranges."""
    m = re.fullmatch(r"([0-9]{3})([- ]?)([0-9]{2})\2([0-9]{4})", s)
    if not m:
        return False
    area, _, group, serial = m.groups()
    if area in ("000", "666") or area[0] == "9":
        return False
    return group != "00" and serial != "0000"
