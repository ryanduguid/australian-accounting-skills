---
id: au-transfer-duty-sa-fixed-items-and-old-rule
synthetic: true
target_skills:
  - au-transfer-duty
---

# South Australian business sale with a lease and an out-of-date goods rule

## Scenario

All records below are fabricated from scratch. An invented buyer is purchasing a South Australian cafe in 2026, including an assignment of the premises lease. A note from the seller's adviser says the loose furniture is dutiable because it has a significant connection with the premises.

## Task

Use `au-transfer-duty` to prepare the transaction and evidence matrix and the unresolved-items hand-off.

## Synthetic inputs

The agreement allocates a total price of 180000.00: lease assignment 20000.00, a fixed coolroom and shop fittings fixed to the building 40000.00, loose tables and chairs 15000.00, goodwill 90000.00 and intellectual property 15000.00. Every asset is in South Australia.

## Deliberately unavailable evidence

Only the supplied facts are available. The transaction date's duty rates, the purchaser's status, any concession or exemption and independent valuations remain missing. No legal approval or external action authority is supplied.

## Required checks

- Route the transaction to RevenueSA Information Circular 99, and record its status and the date read.
- Show the lease and the fixed items as land, because land there includes interests in land, fixtures and items fixed to land.
- Show the loose tables and chairs, goodwill and intellectual property as non-dutiable.
- Reject the adviser's note for a 2026 transaction: the prescribed goods rule it describes was removed from 1 July 2016. Record that as a finding for the reviewer.
- Leave duty, the dutiable value and any rate uncalculated unless a period-specific rule is verified; otherwise mark them `UNVERIFIED`.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not apply a rule that ended in 2016 to a 2026 transaction.
- Do not state a rate, threshold or concession from memory.
- Do not decide liability, submit an assessment, declare, pay or contact the revenue office.

## Source-verification and reviewer boundary

Use the revenue office's current page and the jurisdiction's Act for the transaction date. Preserve unresolved review flags. The conveyancer or lawyer decides liability and performs declarations, assessment submissions and payment. This is not tax, legal or financial advice or an assurance engagement.
