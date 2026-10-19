# Eval sets (v1)

| Set | File | Docs | Spans | Docs without PII | Use |
|---|---|---|---|---|---|
| dev | `eval_sets/dev_v1.jsonl` | 500 | 1,821 | 31 | Debugging, thresholds, teacher few-shot examples |
| gold | `eval_sets/gold_v1.jsonl` | 2,000 | 7,010 | 110 | Final scoring only. Never tuned on, never trained on, never shown to the teacher |

Both files are frozen. `tests/test_eval_sets.py` pins their SHA-256, so any change fails CI.
A change means a new version (`*_v2.jsonl`), never an edit of v1.

## Source and attribution

Derived from the **test split** of [Nemotron-PII](https://huggingface.co/datasets/nvidia/Nemotron-PII)
by NVIDIA (Steier, Manoel, Haushalter, Van Segbroeck, 2025), revision
`b70ffaf5ff39e079776134c5bf4381f00a9fd1ed`, licensed
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Changes: labels mapped to our
schema, name and address parts merged, documents filtered and sampled as described below.

Nemotron-PII is fully synthetic (persona-based, generated with NeMo Data Designer), so the
values are fictional. Its labels were produced during generation, not by human annotators.

## How it was built

`uv run --extra data python scripts/build_eval_sets.py` reproduces both files byte for byte.

1. Keep documents of at most 180 whitespace words (roughly 256 encoder tokens). This drops
   21,188 of the 100,000 test-split documents.
2. Convert each record with `piidistill.data.nemotron.convert`: map labels (table below),
   merge `first_name`/`last_name` parts separated only by spaces or a middle initial into one
   PERSON, and merge a `street_address` with directly following city, state, postcode, county
   or country parts into one ADDRESS.
3. Group by `uid` and split by `uid` with a fixed seed. Each `uid` has a US-style and an
   international-style document built from the same persona (same birth date and IDs), so
   both always land on the same side.
4. Drop gold candidates that share any non-PERSON value (case-insensitive) with dev
   (118 documents dropped).

## Label mapping

| Ours | Nemotron labels |
|---|---|
| PERSON | `first_name`, `last_name` (merged when adjacent) |
| EMAIL | `email` |
| PHONE | `phone_number`, `fax_number` |
| ADDRESS | `street_address` plus directly adjoining `city`, `state`, `postcode`, `county`, `country` |
| POSTAL_CODE | `postcode` not merged into an address |
| DOB | `date_of_birth` |
| GOV_ID | `ssn`, `national_id`, `tax_id` |
| CREDIT_CARD | `credit_debit_card` |
| BANK_ACCOUNT | `account_number`, `bank_routing_number` |
| IP_ADDRESS | `ipv4`, `ipv6` |
| USERNAME | `user_name` |
| SECRET | `password`, `api_key`, `pin`, `cvv` |
| ORG_ID | `customer_id`, `employee_id`, `medical_record_number`, `health_plan_beneficiary_number` |
| URL_PERSONAL | none (not scored on v1) |
| *ignore region* | `url`, `certificate_license_number`, `biometric_identifier`, `device_identifier`, `unique_id`, `mac_address`, `license_plate`, `vehicle_identifier`, `http_cookie`, `swift_bic`, `coordinate` |
| not labeled | everything else: `date`, `time`, `company_name`, `occupation`, `age`, `gender`, city/state/country on their own, sensitive attributes, ... |

An ignore region is text that is plausibly PII but outside what these labels can score. A
prediction overlapping one (and no gold span) is not counted as a false positive.

## Gold span counts

| Type | Spans | | Type | Spans |
|---|---|---|---|---|
| PERSON | 2,007 | | ADDRESS | 399 |
| ORG_ID | 977 | | SECRET | 365 |
| EMAIL | 888 | | CREDIT_CARD | 261 |
| PHONE | 574 | | USERNAME | 227 |
| BANK_ACCOUNT | 485 | | GOV_ID | 220 |
| DOB | 394 | | IP_ADDRESS | 156 |
| | | | POSTAL_CODE | 57 |

## Limitations (state these next to any result)

- **No human labels and no measured agreement.** The labels come from the generator. Known
  noise includes form labels tagged as values (a `password` span reading `Temporary Password`)
  and `account_number` covering non-bank accounts.
- **Different generator from our training data.** That makes gold an out-of-distribution test,
  which is good. But it also means boundary conventions not fixed by the mapping (for example
  whether "+1" belongs to a phone) can cost strict F1. Report partial F1 and token recall
  alongside.
- **Few hard negatives.** Only 5.5% of gold documents have no PII, so precision on clean text
  is under-tested.
- **URL_PERSONAL is not evaluated.**
- **Possible contamination.** Nemotron-PII is public (released 2025-10-28), so a teacher LLM
  or a public baseline may have seen it. Never train on any part of Nemotron-PII, including
  the train split; that keeps the student's score clean even if a baseline's is not.
