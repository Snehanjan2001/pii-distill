"""Date validators: date of birth and card expiry."""

import re
from datetime import date, datetime

_DOB_FORMATS = (
    "%Y-%m-%d",
    "%m/%d/%Y", "%d/%m/%Y", "%m/%d/%y", "%d/%m/%y",
    "%m-%d-%Y", "%d-%m-%Y", "%d.%m.%Y",
    "%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y",
)  # fmt: skip


def parse_dob(s: str, today: date | None = None) -> date | None:
    """First plausible birth date (1900-01-01 to today) that `s` parses as, else None.

    Ambiguous numeric dates (03/04/1988) are accepted if either reading is valid.
    Two-digit years resolve to the most recent past century ("50" -> 1950).
    """
    today = today or date.today()
    text = re.sub(r"(?<=[0-9])(st|nd|rd|th)\b", "", " ".join(s.split()), flags=re.IGNORECASE)
    for fmt in _DOB_FORMATS:
        try:
            d = datetime.strptime(text, fmt).date()
        except ValueError:
            continue
        if "%y" in fmt and d > today:
            d = d.replace(year=d.year - 100)
        if date(1900, 1, 1) <= d <= today:
            return d
    return None


def is_valid_dob(s: str) -> bool:
    return parse_dob(s) is not None


def is_valid_card_expiry(s: str) -> bool:
    """Card expiry MM/YY or MM/YYYY ("/" or "-"). Expired dates still count: format only."""
    m = re.fullmatch(r"(0?[1-9]|1[0-2]) ?[/-] ?([0-9]{2}|20[0-9]{2})", s)
    return m is not None
