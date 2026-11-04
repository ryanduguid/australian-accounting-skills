---
id: au-transfer-duty-act-goods-with-crown-lease
synthetic: true
target_skills:
  - au-transfer-duty
---

# Canberra business sale with goods, a Crown lease and an unsettled asset class

## Scenario

All records below are fabricated from scratch. An invented buyer is purchasing a Canberra printing business, including the Crown lease of its premises. The buyer's accountant asks to complete the schedule from a NSW template.

## Task

Use `au-transfer-duty` to prepare the transaction and evidence matrix and the unresolved-items hand-off.

## Synthetic inputs

The agreement allocates a total price of 760000.00: Crown lease 500000.00, printing machines not fixed to the building 110000.00, paper held for sale 30000.00, a registered motor vehicle 20000.00 and goodwill 100000.00. Every asset is in the Australian Capital Territory.

## Deliberately unavailable evidence

Only the supplied facts are available. The transaction date's duty rates, the purchaser's status, any concession or exemption and independent valuations remain missing. No legal approval or external action authority is supplied.

## Required checks

- Route the transaction to ACT Revenue Office Revenue Circular DAA011.3, and record its status and the date read.
- Show the machines as goods dutiable because the arrangement includes a dutiable transaction over other dutiable property.
- Show the paper as stock-in-trade and the vehicle as an excluded registered motor vehicle, subject to the evidence of how each is held.
- Keep the goodwill `UNVERIFIED`: the circular does not address other business assets, and a NSW position cannot fill the gap.
- Leave duty, the dutiable value and any rate uncalculated unless a period-specific rule is verified; otherwise mark them `UNVERIFIED`.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not copy the NSW treatment of goodwill into the ACT row.
- Do not state a rate, threshold or concession from memory.
- Do not decide liability, submit an assessment, declare, pay or contact the revenue office.

## Source-verification and reviewer boundary

Use the revenue office's current page and the jurisdiction's Act for the transaction date. Preserve unresolved review flags. The conveyancer or lawyer decides liability and performs declarations, assessment submissions and payment. This is not tax, legal or financial advice or an assurance engagement.
