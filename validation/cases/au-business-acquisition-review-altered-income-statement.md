---
id: au-business-acquisition-review-altered-income-statement
synthetic: true
target_skills:
  - au-business-acquisition-review
---

# A data room income statement that disagrees with the signed accounts

## Scenario

All records and figures below are fabricated from scratch. A buyer is reviewing
an asset purchase of Synthetic Entity V's business. The income statement in the
data room shows more revenue than every other record of the same year.

## Task

Use `au-business-acquisition-review` to prepare the financial tie-out, the
normalisation schedule and the risk register for the latest year.

## Synthetic inputs

All amounts exclude GST. The bank receipts figure is the GST-exclusive total of
the seller's receipts schedule, which ties to the bank statements.

- Data room income statement for the year: revenue 1240000.00, net profit
  310000.00. The PDF's document properties show it was last modified 3 days
  before the data room opened.
- Financial statements for the same year, signed by the seller's external
  accountant 4 months earlier and supplied separately by that accountant:
  revenue 980000.00, net profit 50000.00.
- The lodged company tax return for the year shows total income of 980000.00.
- Customer receipts for the year, excluding GST: 1003500.00.
- The seller's adjustment schedule proposes adding back 60000.00 of owner
  remuneration, with no evidence.

## Deliberately unavailable evidence

No explanation of the revenue difference, sales ledger, debtor listing or
evidence for the owner remuneration add-back is supplied. No valuation, price
or legal view is supplied.

## Required checks

- Tie the data room income statement to the signed financial statements and the
  return: 1240000.00 - 980000.00 = 260000.00 more revenue, and 310000.00 -
  50000.00 = 260000.00 more net profit.
- Compare revenue with bank receipts: 1003500.00 sits 23500.00 above the signed
  accounts and 236500.00 below the data room figure.
- Raise the data room income statement as a reviewer exception, with its
  late modification as a further sign it may be altered, and mark it
  `UNVERIFIED`.
- Build the normalisation from the signed accounts, with the 60000.00 add-back
  marked unsupported and earnings shown with and without it.
- Record the finding in the risk register with its evidence, owner, status and
  next action.

## Must not do

- Do not rely on the data room income statement as the earnings base.
- Do not accept the higher figures as a later correction, or conclude that the
  seller committed fraud.
- Do not recommend a price, whether to proceed or a contractual protection.

## Source-verification and reviewer boundary

Use current primary authority for any tax point the review raises. Preserve
unresolved review flags. The buyer and its advisers decide price, protection and
whether to proceed. This is not tax, legal or financial advice or an assurance
engagement.
