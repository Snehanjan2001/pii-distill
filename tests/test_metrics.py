import pytest

from piidistill.eval.metrics import evaluate, match_counts, prf, token_recall_counts
from piidistill.schema import Document, Span

TEXT = "Call Ann Lee at 415-555-0137 or ann@example.com today."
#       0    5   9     16          28  32              48
GOLD = Document(
    "d1",
    TEXT,
    (Span(5, 12, "PERSON"), Span(16, 28, "PHONE"), Span(32, 47, "EMAIL")),
)


def pred(*spans: Span, doc: Document = GOLD) -> Document:
    return Document(doc.id, doc.text, spans)


def test_fixture_offsets():
    assert [TEXT[s.start : s.end] for s in GOLD.spans] == [
        "Ann Lee",
        "415-555-0137",
        "ann@example.com",
    ]


def test_perfect_predictions_score_one():
    r = evaluate([GOLD], [pred(*GOLD.spans)], n_boot=0)
    for mode in ("strict", "partial"):
        assert r[mode]["micro"]["f1"] == 1.0
        assert r[mode]["macro_f1"] == 1.0
    assert r["token_recall"]["value"] == 1.0


def test_empty_predictions_score_zero_recall():
    r = evaluate([GOLD], [pred()], n_boot=0)
    for mode in ("strict", "partial"):
        m = r[mode]["micro"]
        assert (m["recall"], m["precision"], m["f1"]) == (0.0, 0.0, 0.0)
        assert m["fn"] == 3
    assert r["token_recall"]["value"] == 0.0


def test_off_by_one_is_strict_miss_but_partial_match():
    p = pred(Span(5, 11, "PERSON"), Span(16, 28, "PHONE"), Span(32, 47, "EMAIL"))  # "Ann Le"
    r = evaluate([GOLD], [p], n_boot=0)
    assert r["strict"]["per_type"]["PERSON"]["f1"] == 0.0
    assert r["partial"]["per_type"]["PERSON"]["f1"] == 1.0
    assert r["strict"]["micro"]["tp"] == 2 and r["partial"]["micro"]["tp"] == 3


def test_wrong_type_is_a_miss_in_both_modes():
    p = pred(Span(5, 12, "USERNAME"), Span(16, 28, "PHONE"), Span(32, 47, "EMAIL"))
    for partial in (False, True):
        c = match_counts(GOLD, p, partial=partial)
        assert c["PERSON"] == [0, 0, 1]
        assert c["USERNAME"] == [0, 1, 0]
    # Type-agnostic token recall still credits the redaction.
    assert token_recall_counts(GOLD, p) == (4, 4)


def test_partial_matching_is_one_to_one():
    gold = Document("d", "Ann Lee Bob Ray", (Span(0, 7, "PERSON"), Span(8, 15, "PERSON")))
    one_long = pred(Span(0, 15, "PERSON"), doc=gold)
    assert match_counts(gold, one_long, partial=True)["PERSON"] == [1, 0, 1]


def test_token_recall_counts_partially_covered_tokens():
    p = pred(Span(5, 8, "PERSON"))  # "Ann" only, misses "Lee"
    assert token_recall_counts(GOLD, p) == (1, 4)


def test_type_without_gold_has_no_recall_and_is_excluded_from_macro():
    p = pred(*GOLD.spans, Span(48, 53, "DOB"))  # spurious "today"
    r = evaluate([GOLD], [p], n_boot=0)
    dob = r["strict"]["per_type"]["DOB"]
    assert dob["support"] == 0 and dob["fp"] == 1
    assert dob["recall"] is None and dob["f1"] is None
    assert r["strict"]["macro_f1"] == 1.0
    assert r["strict"]["micro"]["precision"] == 0.75


def test_prf_zero_denominators():
    assert prf(0, 0, 0) == {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    assert prf(1, 1, 0)["f1"] == pytest.approx(2 / 3)


def _corpus():
    gold, preds = [], []
    for i in range(30):
        g = Document(f"d{i}", GOLD.text, GOLD.spans)
        keep = GOLD.spans[: 1 + i % 3]  # recall varies by doc: 1/3, 2/3, 3/3
        gold.append(g)
        preds.append(Document(g.id, g.text, keep))
    return gold, preds


def test_bootstrap_is_seeded_and_brackets_point_estimate():
    gold, preds = _corpus()
    a = evaluate(gold, preds, n_boot=300, seed=7)
    b = evaluate(gold, preds, n_boot=300, seed=7)
    m = a["strict"]["micro"]
    assert m["ci95"] == b["strict"]["micro"]["ci95"]
    lo, hi = m["ci95"]["f1"]
    assert lo < m["f1"] < hi
    lo, hi = a["token_recall"]["ci95"]
    assert lo <= a["token_recall"]["value"] <= hi


def test_mismatched_doc_ids_raise():
    other = Document("d2", GOLD.text, GOLD.spans)
    with pytest.raises(ValueError, match="doc ids differ"):
        evaluate([GOLD], [other], n_boot=0)


def test_mismatched_text_raises():
    with pytest.raises(ValueError, match="text differs"):
        evaluate([GOLD], [Document("d1", TEXT.upper(), ())], n_boot=0)
