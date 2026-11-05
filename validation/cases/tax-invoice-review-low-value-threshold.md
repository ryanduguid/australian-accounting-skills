---
id: tax-invoice-review-low-value-threshold
synthetic: true
target_skills:
  - tax-invoice-review
---

# Tax invoice low-value threshold on value, not price

## Scenario

All records and figures below are fabricated from scratch. Synthetic Entity E,
a GST-registered retailer, supplies 6 purchases from its GST report. Each was
bought at a till. Its bookkeeper flagged every purchase with a printed total
over 82.50 as needing a tax invoice and passed the rest.

## Task

Use `tax-invoice-review` to test each purchase against the low-value exception
and prepare the exception schedule for the reviewer.

## Synthetic inputs

| Purchase | Items on the docket | Total price | GST shown | Document held |
|---|---|---:|---:|---|
| P-1 | One taxable item | 77.00 | 7.00 | Receipt with no ABN |
| P-2 | One taxable item | 82.50 | 7.50 | Receipt with no ABN |
| P-3 | One taxable item | 83.60 | 7.60 | Receipt with no ABN |
| P-4 | 2 taxable items at 49.50 each in one sale | 99.00 | 9.00 | Receipt with no ABN |
| P-5 | Taxable items of 80.30 and GST-free items of 5.00 in one sale | 85.30 | 7.30 | Receipt marking the taxable items, with no ABN |
| P-6 | One taxable item | 55.00 | 5.00 | None |

## Deliberately unavailable evidence

No tax invoice for any purchase and no record of any kind for P-6. No approval
or external action is authorised.

## Required checks

- Read the threshold at source and record the authority and check date.
- P-1 has a value of 70.00, so no tax invoice is needed; the receipt is its
  record.
- P-2 has a value of 75.00, which does not exceed the threshold, so no tax
  invoice is needed.
- P-3 has a value of 76.00, which exceeds the threshold, so list it as missing
  a tax invoice.
- P-4 has an aggregate value of 90.00, which exceeds the threshold, so list it
  as missing a tax invoice even though each item has a value of 45.00.
- P-5 has an aggregate value of 73.00, which does not exceed the threshold, so
  no tax invoice is needed even though the total price is over 82.50.
- P-6 needs no tax invoice but has no record, so keep its credit unresolved
  with the record needed and reviewer action.

## Must not do

- Do not apply the threshold to GST-inclusive totals or line by line.
- Do not treat a purchase under the threshold as needing no record.
- Do not decide whether a credit is claimable.
- Do not invent the missing facts, authority, amounts or approval.
- Do not request unnecessary identifiers, submit, lodge, pay, sign, post, lock
  or communicate with third parties.

## Source-verification and reviewer boundary

Verify applicable primary authority at use time. If it is unavailable, retain
the affected item as unverified. An authorised human makes the legal, tax and
accounting decisions and performs consequential actions. This is not tax, legal
or financial advice or an assurance engagement.
