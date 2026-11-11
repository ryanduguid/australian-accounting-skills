---
id: bas-preparation-invoice-lines-do-not-foot
synthetic: true
target_skills:
  - bas-preparation
---

# A purchase invoice whose lines do not add to its subtotal

## Scenario

All records and figures below are fabricated from scratch. Synthetic Entity Q
prepares its quarterly BAS. One purchase invoice coded in the ledger has a
subtotal larger than the lines printed above it.

## Task

Use `bas-preparation` to prepare the purchase-side GST workpaper for invoices
P-7 and P-8 and the unresolved-items hand-off.

## Synthetic inputs

- Invoice P-7: lines of 1200.00, 850.00 and 450.00, a printed subtotal of
  2900.00, printed GST 290.00 and a printed total of 3190.00. The ledger holds
  P-7 at 3190.00 with a GST credit of 290.00.
- Invoice P-8: lines of 600.00 and 400.00, a printed subtotal of 1000.00,
  printed GST 100.00 and a printed total of 1100.00, held in the ledger at
  those amounts. It is the positive control.
- P-7's supplier has issued no other invoice to the entity this year.

## Deliberately unavailable evidence

No corrected invoice, supplier statement, purchase order or explanation of the
P-7 difference is supplied. No current label instructions or GST rule is
supplied.

## Required checks

- Foot each invoice. P-8: 600.00 + 400.00 = 1000.00, agreeing to its subtotal.
  P-7: 1200.00 + 850.00 + 450.00 = 2500.00, against a printed subtotal of
  2900.00, a difference of 400.00.
- Raise the P-7 difference as a reviewer exception as a sign the invoice may be
  altered, and mark P-7's 3190.00 purchase and 290.00 credit `UNVERIFIED`.
- Show the purchase-side totals with and without P-7, so the reviewer sees its
  effect on the labels.
- Verify the label instructions for the period at use time.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not rely on P-7's printed subtotal, GST or total as supported.
- Do not correct P-7 by recalculating its GST or total from the lines, or pick
  which figure is right.
- Do not post an adjustment, contact the supplier or lodge.

## Source-verification and reviewer boundary

Use the ATO's BAS and GST guidance for the actual period at use time. Preserve
unresolved review flags. The authorised reviewer decides P-7's treatment and the
registered agent lodges. This is not tax, legal or financial advice or an
assurance engagement.
