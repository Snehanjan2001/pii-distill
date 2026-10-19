from datetime import date

import pytest

from piidistill.validators.dates import is_valid_card_expiry, is_valid_dob, parse_dob

TODAY = date(2026, 10, 19)


@pytest.mark.parametrize(
    "s,expected",
    [
        ("1988-03-14", date(1988, 3, 14)),
        ("03/14/1988", date(1988, 3, 14)),
        ("14/03/1988", date(1988, 3, 14)),  # day-first is the only valid reading
        ("14.03.1988", date(1988, 3, 14)),
        ("14 March 1988", date(1988, 3, 14)),
        ("14th March 1988", date(1988, 3, 14)),
        ("March 14, 1988", date(1988, 3, 14)),
        ("Mar 14 1988", date(1988, 3, 14)),
        ("03/14/88", date(1988, 3, 14)),
        ("01/01/50", date(1950, 1, 1)),  # two-digit year resolves to the past
        ("29 February 2000", date(2000, 2, 29)),
    ],
)
def test_parse_dob(s, expected):
    assert parse_dob(s, today=TODAY) == expected


@pytest.mark.parametrize(
    "s",
    [
        "02/30/1990",  # near-miss: no Feb 30
        "29 February 1999",  # near-miss: not a leap year
        "13/13/1990",  # near-miss: month 13 in both readings
        "1899-12-31",  # before 1900
        "2027-01-01",  # in the future
        "March 1988",  # no day
        "14 Marchh 1988",
        "",
    ],
)
def test_parse_dob_invalid(s):
    assert parse_dob(s, today=TODAY) is None


def test_is_valid_dob_uses_real_today():
    assert is_valid_dob("1988-03-14")
    assert not is_valid_dob("2999-01-01")


@pytest.mark.parametrize("s", ["08/29", "8/29", "08/2029", "12-30", "01 / 27", "08/19"])
def test_expiry_valid(s):
    assert is_valid_card_expiry(s)


@pytest.mark.parametrize(
    "s",
    [
        "13/29",  # near-miss: month 13
        "00/29",  # near-miss: month 0
        "08/299",  # near-miss: three-digit year
        "08/1929",  # four-digit year outside 20xx
        "0829",
        "08.29",
        "08/",
        "",
    ],
)
def test_expiry_invalid(s):
    assert not is_valid_card_expiry(s)
