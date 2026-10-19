import pytest

from piidistill.schema import ENTITY_TYPES, ID2LABEL, LABEL2ID, LABELS, Document, Span

# Pinned literal on purpose: if this fails, someone reordered the schema.
FROZEN_TYPES = (
    "PERSON", "EMAIL", "PHONE", "ADDRESS", "POSTAL_CODE", "DOB", "GOV_ID",
    "CREDIT_CARD", "BANK_ACCOUNT", "IP_ADDRESS", "USERNAME", "SECRET", "ORG_ID",
    "URL_PERSONAL",
)  # fmt: skip


def test_entity_order_is_frozen():
    # Appending is allowed; the existing prefix must never change.
    assert ENTITY_TYPES[: len(FROZEN_TYPES)] == FROZEN_TYPES


def test_label_layout():
    assert len(LABELS) == 1 + 2 * len(ENTITY_TYPES) == 29
    assert LABELS[0] == "O"
    for i, etype in enumerate(ENTITY_TYPES):
        assert LABELS[1 + 2 * i] == f"B-{etype}"
        assert LABELS[2 + 2 * i] == f"I-{etype}"


def test_id_round_trip():
    assert len(set(LABELS)) == len(LABELS)
    for label, i in LABEL2ID.items():
        assert ID2LABEL[i] == label


@pytest.mark.parametrize("start,end", [(5, 5), (6, 5), (-1, 3)])
def test_span_rejects_bad_offsets(start, end):
    with pytest.raises(ValueError):
        Span(start, end, "PERSON")


def test_span_rejects_unknown_label():
    with pytest.raises(ValueError):
        Span(0, 3, "NAME")


def test_document_sorts_and_accepts_adjacent_spans():
    text = "Ann Lee ann@example.org"
    doc = Document("d1", text, (Span(8, 23, "EMAIL"), Span(0, 7, "PERSON")))
    assert [s.label for s in doc.spans] == ["PERSON", "EMAIL"]
    assert text[doc.spans[1].start : doc.spans[1].end] == "ann@example.org"


def test_document_rejects_overlap():
    with pytest.raises(ValueError, match="overlaps"):
        Document("d", "12 Elm St, 90210", (Span(0, 16, "ADDRESS"), Span(11, 16, "POSTAL_CODE")))


def test_document_rejects_span_past_end():
    with pytest.raises(ValueError, match="past end"):
        Document("d", "short", (Span(0, 6, "PERSON"),))


def test_document_rejects_edge_whitespace():
    with pytest.raises(ValueError, match="whitespace"):
        Document("d", "Ann Lee ", (Span(0, 8, "PERSON"),))
