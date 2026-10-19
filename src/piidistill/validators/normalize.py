"""Text normalization for span values.

Apply to span text only, never to a whole document: NFKC can change string length
(e.g. the ligature "ﬁ" becomes "fi"), which would shift every character offset after it.
"""

import unicodedata


def nfkc(s: str) -> str:
    """NFKC-normalize and drop invisible format characters (zero-width space, BOM, ...)."""
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Cf")
    return unicodedata.normalize("NFKC", s)
