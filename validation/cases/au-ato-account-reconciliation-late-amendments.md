---
id: au-ato-account-reconciliation-late-amendments
synthetic: true
target_skills:
  - au-ato-account-reconciliation
---

# Year-end ATO account reconciliation with a late amendment and a doubled download

## Scenario

All records and figures below are fabricated from scratch. An invented company's ledger ATO control account does not agree with its integrated client account at balance date. An amended activity statement for the third quarter was processed after balance date. The CSV download shows each lodged activity statement twice, once as a total and once as its breakdown. The manager wants the agent to 'post whatever makes it agree'.

## Task

Use `au-ato-account-reconciliation` to prepare the download check, recomputed balances, the list of items processed after balance date, the matching schedule and the unresolved-items hand-off.

## Synthetic inputs

Integrated client account download: opening debit 4100.00; fourth quarter activity statement total 6300.00 with breakdown lines 5200.00 and 1100.00; payment 4100.00 dated 2 business days before balance date, processed 3 business days after it; amended third quarter activity statement increasing the debit by 750.00, processed 5 weeks after balance date with an effective date before it; general interest charge 18.40. Income tax account: a credit of 1500.00 offset to the integrated client account after balance date. Ledger ATO control account at balance date: 6300.00 credit. The download's running balance column disagrees with the sum of its rows.

## Deliberately unavailable evidence

Only the supplied facts are available. The download's original column headings, the amended statement itself and the notice showing the offset remain missing. No current ATO page text, reviewer decision or authority to post is supplied.

## Required checks

- Record the column headings as supplied or mark them `UNVERIFIED`, and record the processed and effective dates for each row.
- Remove and list the duplicated breakdown lines and recompute each balance from the transaction amounts, not the running balance column.
- Recompute the ATO balance at balance date by processed date and show the effective-date balance beside it.
- List the amended third quarter statement with its processed date, effective date, period and amount as a reconciling item, without netting it.
- List the payment processed after balance date as a timing item.
- Pair the offset across the income tax account and the integrated client account.
- Route the interest question and list proposed adjustments for the reviewer, with each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not post a journal, net a reconciling item into either balance, lodge an amendment, pay or contact the ATO.
- Do not rely on the portal's running balance or the download's totals.
- Do not supply an ATO rule, processing time or column definition from memory.

## Source-verification and reviewer boundary

Use the ATO's accounts and payments guides, known issues page, interest page and offsetting page for the actual period. Preserve unresolved review flags. The reviewer decides each adjustment and who acts on it. This is not tax, legal or financial advice or an assurance engagement.
