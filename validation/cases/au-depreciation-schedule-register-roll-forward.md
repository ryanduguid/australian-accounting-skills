---
id: au-depreciation-schedule-register-roll-forward
synthetic: true
target_skills:
  - au-depreciation-schedule
---

# Register roll-forward with a disposed asset, a double-counted pooled asset and a missing start time

## Scenario

All records and figures below are fabricated from scratch. An invented trading business, not a small business entity, supplies its draft closing fixed asset register and asks for the tax depreciation schedule to be finalised from it as it stands.

## Task

Use `au-depreciation-schedule` to prepare the corrected register, individual asset schedule, low-value pool roll-forward, balancing adjustment schedule, tax-to-accounting reconciliation and unresolved-items hand-off.

## Synthetic inputs

Asset A has an opening adjustable value of 5000.00 and was sold in the seventh month of the income year for 3000.00, supported by a sale invoice, yet the draft register still lists it and claims a full-year decline in value of 1000.00. Asset B was allocated to the low-value pool in a prior year according to the prior-year schedule, but the draft register also claims an individual decline in value of 150.00 for it. Asset C cost 8000.00 under a supplier invoice dated in the last month of the year; the register claims 400.00 calculated from the invoice date. No delivery, installation or first-use record exists for Asset C. The draft register's total decline in value is 1550.00. Effective life choices are recorded for A and C, but the method used for A is not stated.

## Deliberately unavailable evidence

Only the supplied facts are available. The missing records remain missing. The accounting fixed asset register and its carrying amounts are not supplied. No current threshold, rate, car limit, legal approval or external action authority is supplied.

## Required checks

- Show that all 1550.00 of the draft decline in value is unsupported as recorded: 1000.00 for A, 150.00 for B and 400.00 for C.
- Record a balancing adjustment event for A, comparing the 3000.00 termination value with the adjustable value just before the sale; keep the part-year decline in value and the resulting adjustment conditional until the method is confirmed, then remove A from the closing register.
- Keep B in the low-value pool only, remove its individual claim and roll the pool forward without stating any pool rate from memory.
- Leave C's decline in value blank and `UNVERIFIED`; the invoice date does not establish the start time.
- Lay out the reconciliation of the corrected tax values to the accounting register, leaving the accounting values blank until that register is supplied, and list A's disposal, B's pooling and C's start time as potential differences to explain.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not finalise the schedule from the draft register, depreciate a disposed asset for the full year or claim the same asset in two regimes.
- Do not infer a first-use date from the invoice or supply a rate, threshold or effective life from memory.
- Do not post journals, lodge, submit, sign or communicate with third parties.

## Source-verification and reviewer boundary

Use applicable primary authority for the actual work period. Preserve unresolved review flags. An authorised human decides the effective life, method and regime choices and the tax position, and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
