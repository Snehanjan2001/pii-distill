import pytest

from piidistill.validators.credentials import is_valid_cvv, is_valid_secret, shannon_entropy

# Token-shaped values are assembled from pieces so GitHub secret scanning does not flag
# these fake test values on push.
TOKEN_BODY = "q7Rk2LmX9vTz4NpWb8Hc3JdYf6Gs1QaE"  # 32 mixed chars, high entropy
PEM = (
    "-----BEGIN " + "PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASC\n-----END PRIVATE KEY-----"
)


@pytest.mark.parametrize(
    "s",
    [
        "AKIA" + "IOSFODNN7EXAMPLE",  # AWS documentation example
        "gh" + "p_" + TOKEN_BODY + "abcd",
        "sk_" + "live_" + TOKEN_BODY[:24],
        "sk-" + "ant-" + TOKEN_BODY,
        "xo" + "xb-" + "1234567890-" + TOKEN_BODY[:20],
        PEM,
        TOKEN_BODY,  # generic high-entropy token
        "hunter2!",  # short password with mixed classes
        "Tr0ub4dor",
    ],
)
def test_secret_valid(s):
    assert is_valid_secret(s)


@pytest.mark.parametrize(
    "s",
    [
        "deadbeefdeadbeef",  # near-miss: token-length hex, but a repeated pattern
        "a" * 32,  # near-miss: long but zero entropy
        "aaaabbbbccccdddd",  # near-miss: 16 chars, only 2 bits/char
        "password",  # single character class
        "correct horse battery",  # whitespace
        "ab1!",  # too short
        "12345",
        "",
    ],
)
def test_secret_invalid(s):
    assert not is_valid_secret(s)


def test_shannon_entropy():
    assert shannon_entropy("") == 0.0
    assert shannon_entropy("aaaa") == 0.0
    assert shannon_entropy("abcd") == 2.0


@pytest.mark.parametrize("s", ["913", "0123", "000", "7402"])
def test_cvv_valid(s):
    assert is_valid_cvv(s)


@pytest.mark.parametrize(
    "s",
    [
        "91",  # near-miss: two digits
        "91345",  # near-miss: five digits
        "9l3",  # near-miss: letter l for digit 1
        "９１３",  # fullwidth: normalize with nfkc first
        " 913",
        "",
    ],
)
def test_cvv_invalid(s):
    assert not is_valid_cvv(s)
