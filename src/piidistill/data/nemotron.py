"""Map Nemotron-PII records onto our 14-type schema.

Source: nvidia/Nemotron-PII (CC BY 4.0), Steier, Manoel, Haushalter, Van Segbroeck, 2025.
https://huggingface.co/datasets/nvidia/Nemotron-PII

Nemotron splits names (first_name / last_name) and addresses (street_address, city, state,
postcode, ...) into parts; our guidelines want one PERSON span per name and one ADDRESS span
per contiguous address, so adjacent parts are merged. Labels outside our schema are either
dropped (not PII under our guidelines) or kept as ignore regions (plausibly PII, so a
prediction there is not counted as a false positive).
"""

import ast
import re

from piidistill.schema import Document, Span

LABEL_MAP = {
    "email": "EMAIL",
    "phone_number": "PHONE",
    "fax_number": "PHONE",
    "postcode": "POSTAL_CODE",  # only when not merged into an ADDRESS
    "date_of_birth": "DOB",
    "ssn": "GOV_ID",
    "national_id": "GOV_ID",
    "tax_id": "GOV_ID",
    "credit_debit_card": "CREDIT_CARD",
    "account_number": "BANK_ACCOUNT",
    "bank_routing_number": "BANK_ACCOUNT",
    "ipv4": "IP_ADDRESS",
    "ipv6": "IP_ADDRESS",
    "user_name": "USERNAME",
    "password": "SECRET",
    "api_key": "SECRET",
    "pin": "SECRET",
    "cvv": "SECRET",
    "customer_id": "ORG_ID",
    "employee_id": "ORG_ID",
    "medical_record_number": "ORG_ID",
    "health_plan_beneficiary_number": "ORG_ID",
}

# Plausibly PII but outside our schema, or (url) mostly non-personal so URL_PERSONAL
# cannot be scored on this source.
IGNORE_LABELS = frozenset(
    {
        "url",
        "certificate_license_number",
        "biometric_identifier",
        "device_identifier",
        "unique_id",
        "mac_address",
        "license_plate",
        "vehicle_identifier",
        "http_cookie",
        "swift_bic",
        "coordinate",
    }
)

# Everything else (date, time, company_name, occupation, age, gender, city/state/country on
# their own, sensitive attributes, ...) is not PII under our guidelines and becomes "O".

_NAME_PARTS = frozenset({"first_name", "last_name"})
_ADDRESS_TAIL = frozenset({"city", "state", "postcode", "county", "country"})
_NAME_GAP = re.compile(r" +(?:[A-Z]\.? +)?")  # "Ann Lee", "Ann B. Lee"
_ADDRESS_GAP = re.compile(r"[ ,]*\n?[ ,]*")  # ", " or a single line break


def _native_spans(record: dict, text: str) -> list[tuple[int, int, str]]:
    raw = record["spans"]
    raw = ast.literal_eval(raw) if isinstance(raw, str) else raw  # stored as a Python repr
    out = []
    for s in sorted(raw, key=lambda s: (s["start"], s["end"])):
        a, b = s["start"], s["end"]
        while a < b and text[a].isspace():
            a += 1
        while b > a and text[b - 1].isspace():
            b -= 1
        if a < b:
            out.append((a, b, s["label"]))
    return out


def convert(record: dict) -> tuple[Document, list[tuple[int, int]]]:
    """One Nemotron record -> (Document in our schema, ignore regions).

    Raises ValueError (from Document) if mapped spans overlap; callers drop such records.
    """
    text = record["text"]
    native = _native_spans(record, text)
    spans: list[Span] = []
    ignore: list[tuple[int, int]] = []
    i = 0
    while i < len(native):
        a, b, label = native[i]
        if label in _NAME_PARTS or label == "street_address":
            tail, gap, out_label = (
                (_NAME_PARTS, _NAME_GAP, "PERSON")
                if label in _NAME_PARTS
                else (_ADDRESS_TAIL, _ADDRESS_GAP, "ADDRESS")
            )
            while (
                i + 1 < len(native)
                and native[i + 1][2] in tail
                and native[i + 1][0] >= b
                and gap.fullmatch(text[b : native[i + 1][0]])
            ):
                i += 1
                b = native[i][1]
            spans.append(Span(a, b, out_label))
        elif label in LABEL_MAP:
            spans.append(Span(a, b, LABEL_MAP[label]))
        elif label in IGNORE_LABELS:
            ignore.append((a, b))
        i += 1
    doc_id = f"{record['uid']}-{record['locale']}"
    return Document(doc_id, text, tuple(spans)), ignore
