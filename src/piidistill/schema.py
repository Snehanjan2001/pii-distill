"""Label schema. Stdlib only: every other module imports this.

ENTITY_TYPES order is frozen. Append new types at the end, never reorder or remove,
or every trained model's label ids silently shift.
"""

from dataclasses import dataclass

ENTITY_TYPES: tuple[str, ...] = (
    "PERSON",
    "EMAIL",
    "PHONE",
    "ADDRESS",
    "POSTAL_CODE",
    "DOB",
    "GOV_ID",
    "CREDIT_CARD",
    "BANK_ACCOUNT",
    "IP_ADDRESS",
    "USERNAME",
    "SECRET",
    "ORG_ID",
    "URL_PERSONAL",
)

LABELS: tuple[str, ...] = ("O",) + tuple(
    f"{prefix}-{etype}" for etype in ENTITY_TYPES for prefix in ("B", "I")
)
LABEL2ID: dict[str, int] = {label: i for i, label in enumerate(LABELS)}
ID2LABEL: dict[int, str] = dict(enumerate(LABELS))


@dataclass(frozen=True)
class Span:
    """Character span over Document.text, end exclusive."""

    start: int
    end: int
    label: str

    def __post_init__(self) -> None:
        if self.label not in ENTITY_TYPES:
            raise ValueError(f"unknown entity type: {self.label!r}")
        if not 0 <= self.start < self.end:
            raise ValueError(f"bad offsets: start={self.start}, end={self.end}")


@dataclass(frozen=True)
class Document:
    """Text plus non-overlapping spans, stored sorted by start."""

    id: str
    text: str
    spans: tuple[Span, ...] = ()

    def __post_init__(self) -> None:
        spans = tuple(sorted(self.spans, key=lambda s: (s.start, s.end)))
        object.__setattr__(self, "spans", spans)
        prev_end = 0
        for s in spans:
            if s.end > len(self.text):
                raise ValueError(f"{self.id}: span {s} past end of text ({len(self.text)})")
            if s.start < prev_end:
                raise ValueError(f"{self.id}: span {s} overlaps the previous span")
            surface = self.text[s.start : s.end]
            if surface != surface.strip():
                raise ValueError(f"{self.id}: span {s} has edge whitespace: {surface!r}")
            prev_end = s.end
