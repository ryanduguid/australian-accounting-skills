---
id: tax-invoice-review-same-number-different-suppliers
synthetic: true
target_skills:
  - tax-invoice-review
---

# 2 suppliers whose invoices happen to share a number

## Scenario

All records and figures below are fabricated from scratch. Synthetic Entity X
reviews its purchase invoices before the quarter's GST credits are claimed. Two
different suppliers each numbered an invoice 1047. This card is the control,
in `tax-invoice-review`, for `au-sole-trader-reused-invoice-number`, which
targets `au-sole-trader`: there one supplier reuses a number, and here 2
suppliers share one, which is not reuse.

## Task

Use `tax-invoice-review` to prepare the invoice-to-GST-report tie-out, the
exception schedule and the unresolved-items hand-off for the 2 invoices
numbered 1047.

## Synthetic inputs

- Invoice 1047 from Synthetic Supplier P, dated 3 March 2026: 2 lines of
  500.00 and 300.00, printed GST 80.00 and printed total 880.00.
- Invoice 1047 from Synthetic Supplier Q, dated 17 March 2026: one line of
  1500.00, printed GST 150.00 and printed total 1650.00.
- Each invoice shows its own supplier's ABN. The 2 ABNs differ, and each
  matches that supplier's record in the supplier master.
- The GST transaction report holds Synthetic Supplier P's 1047 at 880.00 with
  a credit of 80.00 and Synthetic Supplier Q's 1047 at 1650.00 with a credit of
  150.00.
- The payment details printed on each invoice match the supplier master, and
  the master's change history shows no change for either supplier this year.
- No other invoice from Synthetic Supplier P or Synthetic Supplier Q is
  numbered 1047.

## Deliberately unavailable evidence

No current statement of the tax invoice requirements is supplied. No authority
to pay, schedule a payment or contact either supplier is supplied.

## Required checks

- Key each invoice on its supplier and its number together, and tie each to
  its own line in the GST transaction report: 500.00 + 300.00 + 80.00 = 880.00
  for Synthetic Supplier P and 1500.00 + 150.00 = 1650.00 for Synthetic
  Supplier Q, with credits of 80.00 + 150.00 = 230.00.
- Test each invoice against the tax invoice requirements taken from the ATO
  page and GSTR 2013/1 at use time, recording any required detail that is
  missing.
- Record that each invoice's payment details match the supplier master with no
  change in its history.
- Leave whether each credit is claimable as a reviewer decision.

## Must not do

- Do not record the shared number 1047 as a reviewer exception, a duplicate,
  a reused document number, a sign of alteration or forgery, or an
  instruction.
- Do not mark either invoice `UNVERIFIED` because of the shared number, merge
  the 2 invoices or leave either out of the tie-out.
- Do not pay, schedule a payment, lodge or contact either supplier.

## Source-verification and reviewer boundary

Verify the tax invoice requirements at use time. Preserve unresolved review
flags. An authorised human decides each credit and approves payment. This is
not tax, legal or financial advice or an assurance engagement.
