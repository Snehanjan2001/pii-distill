import pytest

from piidistill.validators.contact import (
    is_valid_email,
    is_valid_ip,
    is_valid_phone,
    is_valid_postal_code,
)


@pytest.mark.parametrize(
    "s",
    [
        "ann@example.com",
        "l.moreau@fastmail-example.com",
        "j.okafor+invoices@mail.example.co.uk",
        "support@acme-example.com",
        "x_y-z@sub.example.org",
    ],
)
def test_email_valid(s):
    assert is_valid_email(s)


@pytest.mark.parametrize(
    "s",
    [
        "ann.@example.com",  # near-miss: trailing dot in local part
        "ann..lee@example.com",  # near-miss: consecutive dots
        "ann@example",  # near-miss: no TLD
        "ann@-example.com",  # domain label starts with hyphen
        "ann@example.c",  # one-letter TLD
        "ann lee@example.com",
        "annexample.com",
        "<ann@example.com>",  # brackets belong outside the span
        "a" * 65 + "@example.com",  # local part over 64 chars
    ],
)
def test_email_invalid(s):
    assert not is_valid_email(s)


@pytest.mark.parametrize(
    "s",
    [
        "+1 (415) 555-0137",
        "415-555-0137",
        "(212) 555-0199",
        "415.555.0137",
        "+44 20 7946 0958",  # UK drama-reserved range
        "+1 415 555 0137 ext. 22",
        "415-555-0137 x22",
    ],
)
def test_phone_valid(s):
    assert is_valid_phone(s)


@pytest.mark.parametrize(
    "s",
    [
        "555-0137",  # near-miss: no area code
        "+1 (415) 155-0137",  # near-miss: exchange cannot start with 1
        "+1 (115) 555-0137",  # near-miss: area code cannot start with 1
        "Tel: 415-555-0137",  # label word belongs outside the span
        "1-800-FLOWERS",  # vanity letters
        "415-555-013",
        "12345",
        "",
    ],
)
def test_phone_invalid(s):
    assert not is_valid_phone(s)


@pytest.mark.parametrize(
    "s", ["192.0.2.1", "198.51.100.42", "203.0.113.255", "2001:db8::8a2e:370:7334", "::1"]
)
def test_ip_valid(s):
    assert is_valid_ip(s)


@pytest.mark.parametrize(
    "s",
    [
        "256.1.1.1",  # near-miss: octet out of range
        "192.0.2",  # near-miss: three octets
        "192.0.2.01",  # near-miss: leading zero (ambiguous octal)
        "192.0.2.1.5",
        "2001:db8:::1",
        "v1.2.3.4",
        "192.0.2.1/24",  # a network, not an address
        "",
    ],
)
def test_ip_invalid(s):
    assert not is_valid_ip(s)


@pytest.mark.parametrize(
    "s", ["45402", "45402-1234", "SW1A 2AA", "sw1a2aa", "M1 1AE", "K1A 0B1", "K1A0B1"]
)
def test_postal_valid(s):
    assert is_valid_postal_code(s)


@pytest.mark.parametrize(
    "s",
    [
        "4540",  # near-miss: four digits
        "45402-123",  # near-miss: short +4
        "D1A 0B1",  # near-miss: D is not a valid Canadian first letter
        "00000",
        "SW1A 2A",
        "454021",
        "45402 1234",
        "",
    ],
)
def test_postal_invalid(s):
    assert not is_valid_postal_code(s)
