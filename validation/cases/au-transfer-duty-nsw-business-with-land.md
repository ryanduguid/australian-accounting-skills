---
id: au-transfer-duty-nsw-business-with-land
synthetic: true
target_skills:
  - au-transfer-duty
---

# NSW business sale with freehold premises, goods and goodwill

## Scenario

All records below are fabricated from scratch. An invented buyer is purchasing an operating bakery in NSW and its freehold premises under one sale agreement. The buyer's accountant asks for the asset schedule and a list of what is still needed before duty is worked out.

## Task

Use `au-transfer-duty` to prepare the transaction and evidence matrix and the unresolved-items hand-off.

## Synthetic inputs

The agreement allocates a total price of 900000.00: land and building 600000.00, fixtures described as such in the agreement 80000.00, loose plant and furniture 60000.00, stock-in-trade 30000.00, a registered delivery van 20000.00, goodwill 90000.00 and debtor receivables 20000.00. Every asset is in NSW.

## Deliberately unavailable evidence

Only the supplied facts are available. The transaction date's duty rates, the purchaser's status, any concession or exemption and independent valuations remain missing. No legal approval or external action authority is supplied.

## Required checks

- Route the transaction to Revenue NSW and its business purchases page, and record the page and the date read.
- List all 7 allocated items with their location and amount, and tie them to 900000.00.
- Show the land and fixtures as dutiable property and the loose plant and furniture as goods the agreement brings in because it includes land.
- Show the stock-in-trade and the registered van as excluded goods, and the goodwill and receivables as non-dutiable business assets, each with the page relied on.
- Leave duty, the dutiable value and any rate uncalculated unless a period-specific rule is verified; otherwise mark them `UNVERIFIED`.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not treat the loose goods as non-dutiable because they would not be dutiable alone.
- Do not state a rate, threshold or concession from memory.
- Do not decide liability, submit an assessment, declare, pay or contact the revenue office.

## Source-verification and reviewer boundary

Use the revenue office's current page and the jurisdiction's Act for the transaction date. Preserve unresolved review flags. The conveyancer or lawyer decides liability and performs declarations, assessment submissions and payment. This is not tax, legal or financial advice or an assurance engagement.
