# Annotation guidelines

Version 0.2 (draft). These rules apply to the gold set, the dev set, teacher prompts and
validators alike. If a rule changes after gold annotation starts, bump the version and
re-annotate the affected documents.

All examples are fictional.

## General rules

1. **Spans are character offsets, end exclusive**, over the raw document text.
2. **No leading or trailing whitespace** inside a span. The schema rejects it.
3. **Trailing punctuation goes outside the span.** That covers the sentence period, a comma,
   a closing bracket or a quote. Punctuation that is part of the value stays inside, for
   example the dots in an IP address or the dashes in an SSN.
4. **No overlapping or nested spans.** BIO tagging can only represent a flat sequence. When
   two types could cover the same text, the *outer* span wins (see ADDRESS / POSTAL_CODE).
5. **Label only values that identify or contact a specific individual**, or that grant access
   to their accounts. A generic placeholder (`your-email@here`), an obviously fake value in an
   instruction, or a company switchboard number is not PII. Exceptions are listed per type.
6. **Partial values still count.** For example, a masked card shown as `**** **** **** 4421`
   gets CREDIT_CARD on the visible part. See each type for details.
7. **Prefer recall when unsure.** If you hesitate between "PII" and "not PII", label it and add
   the case to the "Open questions" log at the bottom of this file.

## Entity types

### PERSON
A name of a specific human, whether full, first only, last only or initials plus surname.
- Include: `Priya Ramanathan`, `J. Okafor`, `Mr. Delgado` → span is `Delgado`.
- Exclude: titles and honorifics (`Dr.`, `Mr.`, `Ms.`, `Prof.`), job titles, generic roles
  (`the customer`), and fictional or public figures named in a non-personal context
  (`Sherlock Holmes`, `Abraham Lincoln`).
- Possessive: `Ana's` → span is `Ana`.

### EMAIL
A full email address.
- Include: `l.moreau@fastmail-example.com`.
- Exclude: `mailto:` prefix, surrounding `< >`.
- Role addresses (`support@`, `noreply@`, `info@`): **label them**. They are cheap
  false positives, and missing a personal address is expensive.

### PHONE
A phone or fax number.
- Include: country code, area code in parentheses, extension (`+1 (415) 555-0137 ext. 22`).
- Exclude: the label word (`Tel:`).

### ADDRESS
A street-level postal address: street number and street, optionally with unit, city, region,
postal code and country, as one contiguous span.
- `12 Larkspur Ave, Apt 4B, Dayton, OH 45402` → one ADDRESS span, postal code included.
- A city or country on its own is **not** ADDRESS.
- A PO Box with a number is ADDRESS.
- A line break inside the address is allowed in the span. A blank line ends it.

### POSTAL_CODE
A postal code that stands **outside** a full address (`ZIP: 45402`, `postcode SW1A 2AA`).
Inside an ADDRESS span it is not labeled separately.

### DOB
A date of birth, or a date that the context marks as a birth date.
- Include: `born 14 March 1988`, which gives the span `14 March 1988`, and `DOB: 03/14/1988`.
- Exclude: other dates such as appointments, order dates and the date a document was signed.
- An age (`34 years old`) is not DOB.

### GOV_ID
A government-issued identifier: SSN, passport number, driver's licence, national insurance
number, tax ID or similar.
- The span is the number only, without the label (`SSN: 078-05-1120` → `078-05-1120`).

### CREDIT_CARD
A payment card number (PAN), full or partially masked.
- Expiry date and CVV are **not** part of the CREDIT_CARD span. Label each one as SECRET,
  value only (`CVV 913` → `913`, `exp 08/29` → `08/29`).

### BANK_ACCOUNT
An IBAN, an account number, or a routing number paired with an account.
- A SWIFT/BIC code on its own identifies a bank, not a person, so it is not labeled.

### IP_ADDRESS
An IPv4 or IPv6 address of a host or user.
- Include: `203.0.113.47`, `2001:db8::8a2e:370:7334`.
- Exclude: version strings that look like IPs (`v1.2.3.4`), and netmasks on their own.

### USERNAME
A login handle or account name: `@jdoe_88`, `user: mkowalski`.
- Include the leading `@` when it is written as part of the handle (`@jdoe_88`).

### SECRET
A credential that grants access: password, API key, access token, private key, a
connection string containing a password, or a card's CVV or expiry date.
- For a connection string, the span is the password part only, unless the whole string is a
  single opaque token.

### ORG_ID
An identifier that an organisation assigns to an individual: employee ID, customer number,
patient or medical record number, student ID, membership number.
- Order numbers, ticket numbers and invoice numbers are **not** ORG_ID unless the context ties
  them to identifying a person.

### URL_PERSONAL
A URL that points to a specific individual: a social profile, personal site, or a link with
personal tokens in it.
- Include: `https://linkedin.com/in/ana-souza-1234`, a password-reset link with a token.
- Exclude: a company homepage or a public docs page.

## Hard cases

| Text | Labels | Why |
|---|---|---|
| `Call Dr. Mensah at 555-0199.` | PERSON `Mensah`, PHONE `555-0199` | title and final period are outside |
| `12 Elm St, Austin, TX 78701` | ADDRESS for the whole string | postal code is absorbed by the outer span |
| `ZIP 78701` | POSTAL_CODE `78701` | stands alone |
| `appointment on 2024-05-02` | none | a date that is not a birth date |
| `password: hunter2!` | SECRET `hunter2!` | `!` is part of the value |
| `support@acme-example.com` | EMAIL | role address, labeled for recall |
| `card 4111 1111 1111 1111 exp 08/29 CVV 913` | CREDIT_CARD the number, SECRET `08/29`, SECRET `913` | three separate spans |
| `ping @jdoe_88` | USERNAME `@jdoe_88` | `@` is part of the handle |

## Open questions

Log ambiguous cases here as they come up, with the decision and the date.

- 2026-10-19: role email addresses are labeled EMAIL.
- 2026-10-19: the `@` prefix is included in USERNAME spans.
- 2026-10-19: CVV and card expiry date are labeled SECRET.
