"""Credential validators: API keys, tokens, passwords, private keys, CVVs.

Not named secrets.py to avoid confusion with the stdlib `secrets` module.
"""

import math
import re
from collections import Counter

_KNOWN_PREFIXES = re.compile(
    r"(?:AKIA|ASIA)[0-9A-Z]{16}"  # AWS access key id
    r"|gh[pousr]_[A-Za-z0-9]{36}"  # GitHub token
    r"|github_pat_[A-Za-z0-9_]{60,}"  # GitHub fine-grained token
    r"|(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{16,}"  # Stripe
    r"|sk-[A-Za-z0-9_-]{20,}"  # OpenAI / Anthropic style
    r"|xox[abposr]-[A-Za-z0-9-]{10,}"  # Slack
    r"|AIza[0-9A-Za-z_-]{35}"  # Google API key
    r"|eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*"  # JWT
)
_PEM = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.+-----END [A-Z ]*PRIVATE KEY-----", re.S)


def shannon_entropy(s: str) -> float:
    """Bits per character."""
    n = len(s)
    return -sum(c / n * math.log2(c / n) for c in Counter(s).values()) if n else 0.0


def is_valid_secret(s: str) -> bool:
    """Plausible credential value.

    ponytail: heuristic. Known token formats and PEM keys always pass; other tokens need
    16+ chars and >= 3.5 bits/char entropy; short passwords (6-15 chars) need 2+ character
    classes. Passphrases with spaces are rejected. Revisit with teacher-label stats in M6.
    """
    if _PEM.fullmatch(s) or _KNOWN_PREFIXES.fullmatch(s):
        return True
    if not s or any(ch.isspace() for ch in s):
        return False
    if len(s) >= 16:
        return shannon_entropy(s) >= 3.5
    if len(s) >= 6:
        classes = (str.islower, str.isupper, str.isdigit, lambda c: not c.isalnum())
        return sum(any(f(ch) for ch in s) for f in classes) >= 2
    return False


def is_valid_cvv(s: str) -> bool:
    """Card verification value: 3 or 4 ASCII digits."""
    return bool(re.fullmatch(r"[0-9]{3,4}", s))
