"""Frozen eval sets. If a hash test fails, the file changed: that is a new version (v2),
never an edit of v1."""

import hashlib
from collections import Counter
from pathlib import Path

import pytest

from piidistill.data.io import read_jsonl
from piidistill.schema import ENTITY_TYPES

SETS = Path(__file__).resolve().parents[1] / "eval_sets"
FROZEN_SHA256 = {
    "dev_v1.jsonl": "c0df352efe0bea5b1b714c89976011e489e2dcd78dedb29889671601e0d7ff5d",
    "gold_v1.jsonl": "18c09fe42355c31144b420519155d08adf688d49ca42aff1ee4e6f17fcd27e7d",
}
NOT_SCORED_ON_NEMOTRON = {"URL_PERSONAL"}


@pytest.fixture(scope="module")
def dev():
    return read_jsonl(SETS / "dev_v1.jsonl")


@pytest.fixture(scope="module")
def gold():
    return read_jsonl(SETS / "gold_v1.jsonl")


@pytest.mark.parametrize("name", sorted(FROZEN_SHA256))
def test_frozen_hash(name):
    digest = hashlib.sha256((SETS / name).read_bytes()).hexdigest()
    assert digest == FROZEN_SHA256[name]


def test_sizes(dev, gold):
    assert len(dev[0]) == 500
    assert len(gold[0]) == 2000


def test_every_scored_type_has_support(gold):
    counts = Counter(s.label for d in gold[0] for s in d.spans)
    for label in set(ENTITY_TYPES) - NOT_SCORED_ON_NEMOTRON:
        assert counts[label] >= 20, label


def test_dev_and_gold_are_disjoint(dev, gold):
    def uid(doc_id):
        return doc_id.rsplit("-", 1)[0]

    assert not {uid(d.id) for d in dev[0]} & {uid(d.id) for d in gold[0]}
    assert not {d.text for d in dev[0]} & {d.text for d in gold[0]}

    def values(docs):
        return {
            d.text[s.start : s.end].lower() for d in docs for s in d.spans if s.label != "PERSON"
        }

    assert not values(dev[0]) & values(gold[0])
