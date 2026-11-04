---
id: au-transfer-duty-wa-rent-roll-and-trade-debts
synthetic: true
target_skills:
  - au-transfer-duty
---

# WA property management sale with a rent roll and trade debts

## Scenario

All records below are fabricated from scratch. An invented buyer is purchasing a Western Australian property management business with no land. The seller's schedule treats everything as intangible and therefore outside duty.

## Task

Use `au-transfer-duty` to prepare the transaction and evidence matrix and the unresolved-items hand-off.

## Synthetic inputs

The agreement allocates a total price of 203000.00: rent roll 150000.00, client list 20000.00, trademarks of the business 15000.00, office plant and equipment 10000.00 and trade debts 8000.00. Every asset is in Western Australia.

## Deliberately unavailable evidence

Only the supplied facts are available. The transaction date's duty rates, the purchaser's status, any concession or exemption and independent valuations remain missing. No legal approval or external action authority is supplied.

## Required checks

- Route the transaction to the RevenueWA Duties Fact Sheet on business assets, and record its last-updated date and the date read.
- Show the rent roll and client list as WA business assets.
- Show the trademarks as dutiable only because they are aggregated with other WA business assets, and not as a transaction in intellectual property alone.
- Show the office plant and equipment as chattels dutiable when transferred with other dutiable property.
- Show the trade debts of 8000.00 as outside the WA business asset definition.
- Leave duty, the dutiable value and any rate uncalculated unless a period-specific rule is verified; otherwise mark them `UNVERIFIED`.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not accept the seller's schedule treating every intangible as outside duty.
- Do not state a rate, threshold or concession from memory.
- Do not decide liability, submit an assessment, declare, pay or contact the revenue office.

## Source-verification and reviewer boundary

Use the revenue office's current page and the jurisdiction's Act for the transaction date. Preserve unresolved review flags. The conveyancer or lawyer decides liability and performs declarations, assessment submissions and payment. This is not tax, legal or financial advice or an assurance engagement.
