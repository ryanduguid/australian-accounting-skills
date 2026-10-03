# Prepare an aged receivables review

Reconcile the supplied Aged Receivables Summary, then list the invoice evidence
needed for debtor decisions. A Summary supports contact-level arithmetic and
ageing triage. Obtain Aged Receivables Detail before investigating particular
invoices, due dates, disputes, subsequent receipts or proposed write-offs.

## Confirm the sources

Use the export manifest and completeness checks in `../SKILL.md`. Record report
name, entity, generated timestamp, cut-off date, ageing basis, accounting basis,
currency, filters, population, source format and any recalculation or conversion.
Ageing by due date and ageing by invoice date are different settings. A Summary
name alone does not establish either.

For the verifier's supported CSV shape, the first logical record's first field
must declare `Aged Receivables Summary` after surrounding source whitespace is
trimmed. The manifest's report name must match exactly. A canonical title in
another metadata field does not satisfy this check; unsupported titles remain
`REVIEW` while supported arithmetic continues. A title and matching source digest
establish declarations and byte consistency, not Xero origin or truthfulness.

Retain the original source bytes and hash, on-screen contact-row count and total,
and the exact logical CSV record containing the terminal grand total. CSV record
numbers count a quoted multiline field as one record. They establish provenance;
they are not persistent contact identifiers. A contact can itself be named
`Total`, so its label cannot identify the footer by itself.

For the control, retain its independent source, account population, entity,
date, currency, accounting basis, filters and sign convention. Confirm that the
control is comparable before interpreting a difference. Missing evidence stays
in the exceptions list; numerical agreement does not fill it.
The source entity must occupy exactly one distinct pre-header metadata record,
excluding the report title, `As at` and `Ageing by` records. Missing, duplicate
or contradictory entity records require review. Both source entity and the
unique cut-off record must confirm the manifest before the control tie is
supported; a matching string elsewhere in metadata cannot supply that evidence.

## Reconcile the summary ties

1. Sum each contact's ageing buckets, including `Current` when present, and
   compare with that row's exported `Total`.
2. Sum the identified footer's ageing buckets and compare with its `Total`.
3. Sum signed contact amounts for every supplied ageing column and compare with
   that column in the identified footer. Include `Current` only when present.
4. Sum signed contact totals and compare with the identified export grand total.
5. Compare the export grand total with the independently supplied receivables
   control only when their metadata and populations agree.
6. Compare the export grand total with the recorded on-screen total, and confirm
   the on-screen contact count against the preserved rows.

Keep each difference separately. Use fixed decimal arithmetic and require
`abs(difference) < 0.005`; exactly positive or negative `0.005` needs review.
Compare before rounding. A genuine blank amount can be zero; a physically
missing CSV field cannot. Preserve credits and every supplied contact row,
including repeated names. Do not merge contacts without supplied stable identity.
The fixed half-cent tolerance assumes a two-decimal currency convention such as
AUD. Supplied amounts accept at most 15 integer digits and 4 decimal places.
Agreement between row and column totals cannot establish each contact's ageing
allocation; independent Detail is required for that check. Missing footer,
screen or comparable control evidence prevents summary `PASS`.

The existing [Power Query adapter](https://github.com/ryanduguid/accounting-review-pipeline/blob/main/adapters/accounting-excel-toolkit/powerquery/Xero.AgedReceivables.pq)
parses the observed export and preserves signed amounts and contacts named
`Total`. It identifies the terminal footer from an amount-bearing `Total` and
`Percentage of total` pair. A lone terminal label requires an explicit
`HasSummaryFooter` choice; confirm its role against the original records.

The [stdlib summary verifier](https://github.com/ryanduguid/accounting-review-pipeline/blob/main/adapters/accounting-excel-toolkit/tools/xero_aged_receivables.py)
implements these ties beside that adapter. It requires a supplied manifest and
accepts an optional independent control. Sectioned exports and rows with wholly
blank amounts require population review. Record the generated timestamp with its
timezone. The [fabricated manifest](https://github.com/ryanduguid/accounting-review-pipeline/blob/main/adapters/accounting-excel-toolkit/samples/sample-aged-receivables-manifest.json)
shows its fields. It is not bundled with a copied skill; use an authorised local
installation or perform the same supported arithmetic with an available local tool.
Never invent a tool run when the verifier is absent.

From an Accounting Review Pipeline checkout, this fabricated example runs with
Python 3.10 or later and no installed dependencies:

```powershell
python adapters/accounting-excel-toolkit/tools/xero_aged_receivables.py adapters/accounting-excel-toolkit/samples/sample-aged-receivables-review.csv --manifest adapters/accounting-excel-toolkit/samples/sample-aged-receivables-manifest.json --control adapters/accounting-excel-toolkit/samples/sample-aged-receivables-control.json
```

The three fabricated contact totals are `100`, `-25` and `10`, giving `85`.
Two contacts share `00123`; the third is named `Total`. All remain separate.
The footer and independent control are both `85`. The verifier reports `PASS`
for bounded summary checks and `REVIEW` for debtor decisions. For a valid invocation,
its exits are `0` for passing summary checks, `2` for review findings and `1` for
invalid source or evidence input. Command-line usage errors also exit `2`.

## Prepare the dated review pack

Include the source manifest, preserved rows, signed ageing totals, all summary
ties, credits requiring investigation, and an exceptions list with source
record, expected/found amount, difference, owner, status and next action.
Keep the cut-off date separate from the generated timestamp.

Where Detail, receipt or dispute evidence is absent, state the missing evidence
and retain the decision at `REVIEW`. Complete supported arithmetic even if
another check is unavailable. Do not infer collectability, recommend a write-off
as established treatment, approve the close or send collection messages.

Keep real exports and outputs in the firm's approved location outside every
version-control checkout. Not tax, legal or assurance advice. An authorised
human resolves the evidence and decides what action to take.
