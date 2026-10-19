"""Entity-level evaluation: strict and partial P/R/F1, token-level PII recall, bootstrap CIs.

Conventions (cite these next to any reported number):
- Strict match: identical (start, end, label).
- Partial match: same label and at least one overlapping character, matched one-to-one.
- A ratio with a zero denominator is 0.0. A type with no gold spans has recall/F1 None
  and is left out of the macro average.
- Ignore regions (optional, per doc): an unmatched prediction that overlaps an ignore region
  and no gold span is dropped, not counted as a false positive. Used for text that is
  plausibly PII but outside the gold labels' scope.
- Headline numbers are micro-averaged over spans. CIs resample documents, not spans,
  because spans within a document are correlated.
"""

import random
import re
import statistics
from collections import defaultdict
from collections.abc import Iterable

from piidistill.schema import ENTITY_TYPES, Document, Span

_TOKEN = re.compile(r"\S+")


def _ratio(num: int, den: int) -> float:
    return num / den if den else 0.0


def prf(tp: int, fp: int, fn: int) -> dict[str, float]:
    p, r = _ratio(tp, tp + fp), _ratio(tp, tp + fn)
    return {"precision": p, "recall": r, "f1": 2 * p * r / (p + r) if p + r else 0.0}


def _overlaps(a: Span, start: int, end: int) -> bool:
    return a.start < end and start < a.end


def match_counts(
    gold: Document, pred: Document, partial: bool, ignore: Iterable[tuple[int, int]] = ()
) -> dict[str, list[int]]:
    """Per-label [tp, fp, fn] for one document."""
    counts: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
    ignore = list(ignore)

    def ignored(p: Span) -> bool:
        return any(_overlaps(p, a, b) for a, b in ignore) and not any(
            _overlaps(g, p.start, p.end) for g in gold.spans
        )

    if partial:
        # Greedy left-to-right is a maximum matching here: within one document the spans
        # on each side are sorted and non-overlapping (Document enforces it).
        unmatched = list(gold.spans)
        for p in pred.spans:
            hit = next(
                (g for g in unmatched if g.label == p.label and _overlaps(g, p.start, p.end)), None
            )
            if hit is None:
                if not ignored(p):
                    counts[p.label][1] += 1
            else:
                unmatched.remove(hit)
                counts[p.label][0] += 1
        for g in unmatched:
            counts[g.label][2] += 1
    else:
        gold_set, pred_set = set(gold.spans), set(pred.spans)
        for s in gold_set & pred_set:
            counts[s.label][0] += 1
        for s in pred_set - gold_set:
            if not ignored(s):
                counts[s.label][1] += 1
        for s in gold_set - pred_set:
            counts[s.label][2] += 1
    return counts


def token_recall_counts(gold: Document, pred: Document) -> tuple[int, int]:
    """(covered, total) gold PII tokens. Type-agnostic: was the text redacted at all?"""
    covered = total = 0
    for m in _TOKEN.finditer(gold.text):
        if any(_overlaps(g, m.start(), m.end()) for g in gold.spans):
            total += 1
            covered += any(_overlaps(p, m.start(), m.end()) for p in pred.spans)
    return covered, total


def _percentile_ci(values: list[float]) -> tuple[float, float]:
    cuts = statistics.quantiles(values, n=40, method="inclusive")  # 2.5% steps
    return cuts[0], cuts[-1]


def evaluate(
    gold: Iterable[Document],
    pred: Iterable[Document],
    n_boot: int = 1000,
    seed: int = 0,
    ignore: dict[str, list[tuple[int, int]]] | None = None,
) -> dict:
    """Score predictions against gold. Both sides must contain exactly the same doc ids.

    `ignore` maps doc id -> ignore regions, as returned by data.io.read_jsonl.
    """
    ignore = ignore or {}
    gold_by_id = {d.id: d for d in gold}
    pred_by_id = {d.id: d for d in pred}
    if gold_by_id.keys() != pred_by_id.keys():
        missing = sorted(gold_by_id.keys() - pred_by_id.keys())[:5]
        extra = sorted(pred_by_id.keys() - gold_by_id.keys())[:5]
        raise ValueError(f"doc ids differ: missing preds {missing}, unexpected preds {extra}")
    for doc_id, g in gold_by_id.items():
        if pred_by_id[doc_id].text != g.text:
            raise ValueError(f"{doc_id}: prediction text differs from gold text")

    ids = sorted(gold_by_id)
    report: dict = {"n_docs": len(ids)}
    # Per-doc totals, kept for the bootstrap.
    per_doc: dict[str, list[tuple[int, int, int]]] = {}

    for mode in ("strict", "partial"):
        by_type: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
        doc_totals = []
        for i in ids:
            c = match_counts(
                gold_by_id[i], pred_by_id[i], partial=mode == "partial", ignore=ignore.get(i, ())
            )
            for label, (tp, fp, fn) in c.items():
                by_type[label][0] += tp
                by_type[label][1] += fp
                by_type[label][2] += fn
            doc_totals.append(tuple(sum(v[k] for v in c.values()) for k in range(3)))
        per_doc[mode] = doc_totals

        tp, fp, fn = (sum(t[k] for t in doc_totals) for k in range(3))
        per_type = {}
        for label in ENTITY_TYPES:
            ltp, lfp, lfn = by_type[label]
            support = ltp + lfn
            row = {"support": support, "tp": ltp, "fp": lfp, "fn": lfn, **prf(ltp, lfp, lfn)}
            if support == 0:
                row["recall"] = row["f1"] = None
            per_type[label] = row
        scored = [r["f1"] for r in per_type.values() if r["f1"] is not None]
        report[mode] = {
            "micro": {"tp": tp, "fp": fp, "fn": fn, **prf(tp, fp, fn)},
            "macro_f1": statistics.fmean(scored) if scored else 0.0,
            "per_type": per_type,
        }

    tok = [token_recall_counts(gold_by_id[i], pred_by_id[i]) for i in ids]
    report["token_recall"] = {"value": _ratio(sum(c for c, _ in tok), sum(t for _, t in tok))}

    if n_boot and len(ids) > 1:
        rng = random.Random(seed)
        samples: dict[str, list[float]] = defaultdict(list)
        n = len(ids)
        for _ in range(n_boot):
            idx = [rng.randrange(n) for _ in range(n)]
            for mode in ("strict", "partial"):
                tp, fp, fn = (sum(per_doc[mode][j][k] for j in idx) for k in range(3))
                for metric, value in prf(tp, fp, fn).items():
                    samples[f"{mode}.{metric}"].append(value)
            samples["token_recall"].append(
                _ratio(sum(tok[j][0] for j in idx), sum(tok[j][1] for j in idx))
            )
        for key, values in samples.items():
            if key == "token_recall":
                report["token_recall"]["ci95"] = _percentile_ci(values)
            else:
                mode, metric = key.split(".")
                report[mode]["micro"].setdefault("ci95", {})[metric] = _percentile_ci(values)
    return report


def format_report(report: dict) -> str:
    """Plain-text summary table."""

    def ci(m: dict, metric: str) -> str:
        lo, hi = m.get("ci95", {}).get(metric, (None, None))
        return f"[{lo:.3f}, {hi:.3f}]" if lo is not None else ""

    lines = [f"docs: {report['n_docs']}", ""]
    lines.append(f"{'':8} {'P':>6} {'R':>6} {'F1':>6}  {'F1 95% CI':<17} macro-F1")
    for mode in ("strict", "partial"):
        m = report[mode]["micro"]
        lines.append(
            f"{mode:8} {m['precision']:6.3f} {m['recall']:6.3f} {m['f1']:6.3f}  "
            f"{ci(m, 'f1'):<17} {report[mode]['macro_f1']:.3f}"
        )
    tr = report["token_recall"]
    tr_ci = f"[{tr['ci95'][0]:.3f}, {tr['ci95'][1]:.3f}]" if "ci95" in tr else ""
    lines += [f"token-level PII recall: {tr['value']:.3f} {tr_ci}", ""]

    lines.append(f"{'type':14} {'n':>4} {'strict F1':>10} {'partial F1':>11}")
    for label in ENTITY_TYPES:
        s, p = report["strict"]["per_type"][label], report["partial"]["per_type"][label]
        if s["support"] == 0 and s["fp"] == 0:
            continue
        fmt = lambda v: "n/a" if v is None else f"{v:.3f}"  # noqa: E731
        lines.append(f"{label:14} {s['support']:4} {fmt(s['f1']):>10} {fmt(p['f1']):>11}")
    return "\n".join(lines)
