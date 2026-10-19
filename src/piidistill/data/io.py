"""JSONL storage for eval sets: one document per line.

{"id": str, "text": str, "spans": [[start, end, label], ...], "ignore": [[start, end], ...],
 "meta": {...}}
"""

import json
from collections.abc import Iterable
from pathlib import Path

from piidistill.schema import Document, Span

Ignore = dict[str, list[tuple[int, int]]]


def doc_to_json(doc: Document, ignore: Iterable[tuple[int, int]] = (), **meta) -> str:
    row = {
        "id": doc.id,
        "text": doc.text,
        "spans": [[s.start, s.end, s.label] for s in doc.spans],
        "ignore": [list(r) for r in ignore],
        "meta": meta,
    }
    return json.dumps(row, ensure_ascii=False)


def read_jsonl(path: str | Path) -> tuple[list[Document], Ignore]:
    docs, ignore = [], {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            docs.append(Document(row["id"], row["text"], tuple(Span(*s) for s in row["spans"])))
            ignore[row["id"]] = [tuple(r) for r in row.get("ignore", [])]
    return docs, ignore
