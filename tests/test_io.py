from piidistill.data.io import doc_to_json, read_jsonl
from piidistill.schema import Document, Span


def test_jsonl_round_trip(tmp_path):
    doc = Document("d1", "Ann Lee, ann@example.com", (Span(0, 7, "PERSON"), Span(9, 24, "EMAIL")))
    path = tmp_path / "x.jsonl"
    path.write_text(doc_to_json(doc, [(0, 3)], locale="us") + "\n", encoding="utf-8")
    docs, ignore = read_jsonl(path)
    assert docs == [doc]
    assert ignore == {"d1": [(0, 3)]}
