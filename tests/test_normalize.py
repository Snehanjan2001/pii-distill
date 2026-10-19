import pytest

from piidistill.validators.normalize import nfkc


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("４１１１ １１１１", "4111 1111"),  # fullwidth digits and ideographic space
        ("ａｎｎ＠example.com", "ann@example.com"),  # fullwidth letters and at sign
        ("ﬁle", "file"),  # ligature expands: length changes
        ("an​n@example.com", "ann@example.com"),  # zero-width space
        ("﻿AKIA", "AKIA"),  # byte-order mark
        ("Ann Lee", "Ann Lee"),  # no-break space
        ("①②③", "123"),  # circled digits
        ("plain ascii", "plain ascii"),  # untouched
        ("", ""),
    ],
)
def test_nfkc(raw, expected):
    assert nfkc(raw) == expected


def test_nfkc_is_idempotent():
    s = "ｆｕｌｌ​width ﬁ"
    assert nfkc(nfkc(s)) == nfkc(s)
