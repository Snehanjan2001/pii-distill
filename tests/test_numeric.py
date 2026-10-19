import pytest

from piidistill.validators.numeric import is_valid_iban, is_valid_luhn, is_valid_ssn


@pytest.mark.parametrize(
    "s",
    [
        "4111 1111 1111 1111",  # Visa test PAN
        "4111111111111111",
        "4111-1111-1111-1111",
        "5555 5555 5555 4444",  # Mastercard test PAN
        "3782 822463 10005",  # Amex test PAN (15 digits)
        "6011 1111 1111 1117",  # Discover test PAN
    ],
)
def test_luhn_valid(s):
    assert is_valid_luhn(s)


@pytest.mark.parametrize(
    "s",
    [
        "4111 1111 1111 1112",  # near-miss: last digit changed
        "4111 1111 1111 1121",  # near-miss: adjacent digits swapped
        "0000 0000 0000 0000",  # passes the checksum but no PAN starts with 0
        "4111 1111 111",  # too short
        "4111 1111 1111 1111 1111",  # too long
        "4111 1111 1111 111a",
        "4111  1111 1111 1111",  # double separator
        " 4111 1111 1111 1111",  # edge whitespace belongs outside the span
        "",
    ],
)
def test_luhn_invalid(s):
    assert not is_valid_luhn(s)


@pytest.mark.parametrize(
    "s",
    [
        "GB82 WEST 1234 5698 7654 32",
        "GB82WEST12345698765432",
        "gb82 west 1234 5698 7654 32",  # lowercase accepted
        "DE89 3704 0044 0532 0130 00",
        "FR14 2004 1010 0505 0001 3M02 606",
        "NL91 ABNA 0417 1643 00",
        "BE68 5390 0754 7034",
    ],
)
def test_iban_valid(s):
    assert is_valid_iban(s)


@pytest.mark.parametrize(
    "s",
    [
        "GB82 WEST 1234 5698 7654 33",  # near-miss: last digit changed
        "GB82 WEST 1234 5698 7654 23",  # near-miss: digits swapped
        "GB28 WEST 1234 5698 7654 32",  # near-miss: check digits swapped
        "GB82 WEST 1234 5698 7654 3",  # wrong length for GB
        "XX82 WEST 1234 5698 7654 32",  # unknown country
        "GB8A WEST 1234 5698 7654 32",  # check digits not numeric
        "GB82-WEST-1234-5698-7654-32",  # dashes not allowed
        "",
    ],
)
def test_iban_invalid(s):
    assert not is_valid_iban(s)


@pytest.mark.parametrize("s", ["123-45-6789", "123 45 6789", "123456789", "665-01-0001"])
def test_ssn_valid(s):
    assert is_valid_ssn(s)


@pytest.mark.parametrize(
    "s",
    [
        "000-45-6789",  # near-miss: area 000
        "666-45-6789",  # near-miss: area 666
        "923-45-6789",  # near-miss: area 9xx (ITIN range)
        "123-00-6789",  # group 00
        "123-45-0000",  # serial 0000
        "123-45 6789",  # mixed separators
        "12-345-6789",  # wrong grouping
        "123-45-678",
    ],
)
def test_ssn_invalid(s):
    assert not is_valid_ssn(s)
