"""Build the frozen dev and gold eval sets from the Nemotron-PII test split.

    uv run --extra data python scripts/build_eval_sets.py

Deterministic: pinned dataset revision, fixed seed. Re-running must reproduce the committed
files byte for byte (tests/test_eval_sets.py checks the gold hash).
"""

import random
import sys
import urllib.request
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq

from piidistill.data.io import doc_to_json
from piidistill.data.nemotron import convert

REVISION = "b70ffaf5ff39e079776134c5bf4381f00a9fd1ed"
URL = (
    f"https://huggingface.co/datasets/nvidia/Nemotron-PII/resolve/{REVISION}"
    "/data/test-00000-of-00001.parquet"
)
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / f"nemotron-pii-test-{REVISION[:8]}.parquet"
OUT = ROOT / "eval_sets"

SEED = 20261019
N_DEV, N_GOLD = 500, 2000
# ponytail: whitespace words as a proxy for <= 256 encoder tokens; measure with the real
# tokenizer in M7 and tighten if many docs overflow.
MAX_WORDS = 180


def main() -> None:
    if not RAW.exists():
        RAW.parent.mkdir(parents=True, exist_ok=True)
        print(f"downloading {URL}", file=sys.stderr)
        urllib.request.urlretrieve(URL, RAW)

    rows = pq.read_table(RAW).to_pylist()
    by_uid: dict[str, list] = {}
    dropped = Counter()
    for r in rows:
        if len(r["text"].split()) > MAX_WORDS:
            dropped["too_long"] += 1
            continue
        try:
            doc, ignore = convert(r)
        except ValueError:
            dropped["overlapping_spans"] += 1
            continue
        meta = {k: r[k] for k in ("uid", "locale", "domain", "document_type", "document_format")}
        by_uid.setdefault(r["uid"], []).append((doc, ignore, meta))

    # Split by uid: the us/intl pair of one uid share a persona (same DOB, IDs, ...).
    uids = sorted(by_uid)
    random.Random(SEED).shuffle(uids)

    dev, gold, dev_values = [], [], set()
    for uid in uids:
        items = by_uid[uid]
        if len(dev) < N_DEV:
            dev += items
            dev_values |= {_value(d, s) for d, _, _ in items for s in d.spans if _keyed(s)}
        elif len(gold) < N_GOLD:
            vals = {_value(d, s) for d, _, _ in items for s in d.spans if _keyed(s)}
            if vals & dev_values:
                dropped["gold_shares_value_with_dev"] += len(items)
                continue
            gold += items
        else:
            break
    dev, gold = dev[:N_DEV], gold[:N_GOLD]

    OUT.mkdir(exist_ok=True)
    for name, items in (("dev_v1", dev), ("gold_v1", gold)):
        with open(OUT / f"{name}.jsonl", "w", encoding="utf-8", newline="\n") as f:
            for doc, ignore, meta in sorted(items, key=lambda x: x[0].id):
                f.write(doc_to_json(doc, ignore, **meta) + "\n")
        counts = Counter(s.label for d, _, _ in items for s in d.spans)
        empty = sum(not d.spans for d, _, _ in items)
        print(f"{name}: {len(items)} docs, {sum(counts.values())} spans, {empty} without PII")
        for label, n in sorted(counts.items()):
            print(f"  {label:14}{n}")
    print(f"dropped: {dict(dropped)}")


def _keyed(span) -> bool:
    # First or last names alone collide by chance ("Brian"); full names and IDs do not.
    return span.label != "PERSON"


def _value(doc, span) -> str:
    return doc.text[span.start : span.end].lower()


if __name__ == "__main__":
    main()
