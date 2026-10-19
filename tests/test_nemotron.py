from piidistill.data.nemotron import convert


def record(text, *spans):
    """spans: (surface, label); located by first occurrence."""
    out = []
    for surface, label in spans:
        start = text.index(surface)
        out.append({"start": start, "end": start + len(surface), "text": surface, "label": label})
    return {"uid": "u1", "locale": "us", "text": text, "spans": repr(out)}


def labeled(doc):
    return [(doc.text[s.start : s.end], s.label) for s in doc.spans]


def test_adjacent_name_parts_merge_into_one_person():
    doc, _ = convert(record("Signed: Ann Lee.", ("Ann", "first_name"), ("Lee", "last_name")))
    assert labeled(doc) == [("Ann Lee", "PERSON")]


def test_middle_initial_is_absorbed():
    text = "Ann B. Lee called."
    doc, _ = convert(record(text, ("Ann", "first_name"), ("Lee", "last_name")))
    assert labeled(doc) == [("Ann B. Lee", "PERSON")]


def test_name_parts_across_punctuation_stay_separate():
    text = "First Name: Ann\nLast Name: Lee"
    doc, _ = convert(record(text, ("Ann", "first_name"), ("Lee", "last_name")))
    assert labeled(doc) == [("Ann", "PERSON"), ("Lee", "PERSON")]


def test_contiguous_address_parts_merge():
    text = "Ship to 12 Elm St, Dayton, OH 45402 today."
    doc, _ = convert(
        record(
            text,
            ("12 Elm St", "street_address"),
            ("Dayton", "city"),
            ("OH", "state"),
            ("45402", "postcode"),
        )
    )
    assert labeled(doc) == [("12 Elm St, Dayton, OH 45402", "ADDRESS")]


def test_address_tail_after_other_words_is_not_merged():
    text = "12 Elm St in Knox County"
    doc, _ = convert(record(text, ("12 Elm St", "street_address"), ("Knox County", "county")))
    assert labeled(doc) == [("12 Elm St", "ADDRESS")]


def test_standalone_postcode_and_city():
    text = "ZIP 45402, city Dayton"
    doc, _ = convert(record(text, ("45402", "postcode"), ("Dayton", "city")))
    assert labeled(doc) == [("45402", "POSTAL_CODE")]


def test_label_mapping_and_dropped_labels():
    text = "Card 4111 1111 1111 1111 cvv 913 on 2024-05-02 for Acme Corp, age 41."
    doc, _ = convert(
        record(
            text,
            ("4111 1111 1111 1111", "credit_debit_card"),
            ("913", "cvv"),
            ("2024-05-02", "date"),
            ("Acme Corp", "company_name"),
            ("41", "age"),
        )
    )
    assert labeled(doc) == [("4111 1111 1111 1111", "CREDIT_CARD"), ("913", "SECRET")]


def test_ignore_labels_become_ignore_regions():
    text = "See https://example.com/x and MAC 00:00:5E:00:53:01."
    doc, ignore = convert(
        record(text, ("https://example.com/x", "url"), ("00:00:5E:00:53:01", "mac_address"))
    )
    assert doc.spans == ()
    assert [text[a:b] for a, b in ignore] == ["https://example.com/x", "00:00:5E:00:53:01"]


def test_edge_whitespace_is_trimmed_and_id_includes_locale():
    text = "user: jdoe_88 "
    doc, _ = convert(record(text, ("jdoe_88 ", "user_name")))
    assert labeled(doc) == [("jdoe_88", "USERNAME")]
    assert doc.id == "u1-us"
