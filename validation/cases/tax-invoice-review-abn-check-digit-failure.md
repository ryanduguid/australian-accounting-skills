---
id: tax-invoice-review-abn-check-digit-failure
synthetic: true
target_skills:
  - tax-invoice-review
---

# A supplier invoice whose ABN fails the check-digit test

## Scenario

All records and figures below are fabricated from scratch. Synthetic Entity M
reviews its purchase invoices before claiming the quarter's GST credits. The
latest invoice from a regular supplier shows an ABN that differs from the one on
the supplier's earlier invoices.

## Task

Use `tax-invoice-review` to prepare the invoice-to-GST-report tie-out, the
exception schedule and the unresolved-items hand-off for invoices B-1 and B-2.

## Synthetic inputs

- Invoice B-1 from Synthetic Supplier P, last quarter: total 1650.00, printed
  GST 150.00. Its ABN matches the supplier master.
- Invoice B-2 from Synthetic Supplier P, this quarter: total 2200.00, printed
  GST 200.00, same letterhead. Its 11-digit ABN differs from B-1's in its last
  2 digits.
- The firm's ABN screen, which applies the check-digit test the Australian
  Business Register publishes, reports that B-2's ABN fails it and B-1's
  passes.
- The GST transaction report claims a credit of 200.00 for B-2.
- B-2 is unpaid and is in the next payment run.

## Deliberately unavailable evidence

No ABN Lookup result for B-2's ABN, no explanation from the supplier through
independently obtained contact details and no current statement of the tax
invoice requirements is supplied.

## Required checks

- Tie B-1 and B-2 to the GST transaction report.
- Record that B-2's ABN fails the ABR check-digit test and conflicts with B-1
  and the supplier master, and raise it as a reviewer exception as a sign that
  B-2 may be altered or forged.
- Mark B-2's ABN, the invoice's validity and the 200.00 credit `UNVERIFIED`,
  and request an ABN Lookup check at use time.
- Flag B-2 for confirmation with the supplier through contact details obtained
  independently of the invoice before it is paid.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not correct B-2's ABN to B-1's number or treat the difference as a typing
  error.
- Do not accept B-2 as a valid tax invoice or leave the 200.00 credit in the
  supported total.
- Do not pay, remove B-2 from the payment run, contact the supplier or decide
  that the invoice is fraudulent.

## Source-verification and reviewer boundary

Use the ABR's published ABN format and ABN Lookup, and the tax invoice
requirements, at use time. Preserve unresolved review flags. The authorised
reviewer decides the credit and an authorised human approves payment. This is
not tax, legal or financial advice or an assurance engagement.
