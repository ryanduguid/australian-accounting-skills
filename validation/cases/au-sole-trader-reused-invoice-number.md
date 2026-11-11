---
id: au-sole-trader-reused-invoice-number
synthetic: true
target_skills:
  - au-sole-trader
---

# 2 supplier invoices with the same number and different amounts

## Scenario

All records and figures below are fabricated from scratch. An invented sole
trader supplies the year's expense records and business bank statements. Two
invoices from the same supplier carry the same invoice number, different dates
and different amounts, and both are in the expense list.

## Task

Use `au-sole-trader` to reconcile business costs to the ledger and bank records
and prepare the unresolved-items hand-off.

## Synthetic inputs

- Expense list: materials invoices from Synthetic Supplier W totalling
  6350.00, of which 2 are numbered W-311.
- W-311 dated 2 February 2026: 900.00. The business bank statement shows one
  payment of 900.00 to Synthetic Supplier W on 9 February 2026.
- W-311 dated 9 May 2026: 1450.00, in a different layout from the supplier's
  other invoices. No bank or card payment matches it.
- The other Synthetic Supplier W invoices, totalling 4000.00, each match a
  bank payment.

## Deliberately unavailable evidence

No supplier statement, credit note or explanation of the second W-311 is
supplied. No current deduction rule is supplied.

## Required checks

- Show the supplier's invoices as 900.00 + 1450.00 + 4000.00 = 6350.00, and
  the bank-supported amount as 900.00 + 4000.00 = 4900.00.
- Raise the reused number W-311 as a reviewer exception, with the layout
  difference and the missing payment as further signs the 9 May invoice may be
  altered or forged.
- Mark the 9 May W-311 for 1450.00 `UNVERIFIED` and keep it out of the
  supported business costs until the reviewer resolves it.
- Request a supplier statement for the year.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not accept both W-311 invoices as separate supported expenses.
- Do not delete either invoice, renumber one, or decide which is genuine.
- Do not rely on the 9 May invoice in the profit bridge or the BAS
  reconciliation.

## Source-verification and reviewer boundary

Verify deduction and substantiation rules for the actual income year at use
time. Preserve unresolved review flags. The authorised reviewer decides the
treatment and any follow-up with the client. This is not tax, legal or financial
advice or an assurance engagement.
