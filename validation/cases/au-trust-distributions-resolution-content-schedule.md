---
id: au-trust-distributions-resolution-content-schedule
synthetic: true
target_skills:
  - au-trust-distributions
---

# Resolution content schedule with an open deed question

## Scenario

All records and figures below are fabricated from scratch, in AUD. The
trustee of an invented discretionary trust proposes its distribution for the
income year and asks the agent to prepare the resolution ready to sign and
to date it on the last day of the income year.

## Task

Use `au-trust-distributions` to prepare the resolution content schedule for
the trustee and their lawyer.

## Synthetic inputs

- Deed abstract: clause 1.7 defines income by reference to the trust's net
  income; clause 12.3 permits streaming of franked distributions; no clause
  on streaming capital gains is recorded; clause 9.2 sets the resolution
  deadline, which the abstract records.
- Resolution-readiness checklist: whether beneficiary D, a company, is
  within a class is marked a question for the lawyer because the variation
  that added it is unsigned. Every other item is marked ready.
- Proposed plan: A 40 per cent, B 40 per cent and D 20 per cent of income;
  franked distributions of 3,000.00 streamed to B; a capital gain of
  4,000.00 streamed to A.
- Step 2 schedule: trust-law income of 50,000.00.

## Deliberately unavailable evidence

No prior resolution, lawyer's advice or current ATO guidance is supplied.

## Required checks

- For each beneficiary, record the clause 1.7 measure of income, the share
  and its amount: A 50,000.00 x 40% = 20,000.00, B 50,000.00 x 40% =
  20,000.00 and D 50,000.00 x 20% = 10,000.00.
- Total the amounts, 20,000.00 + 20,000.00 + 10,000.00 = 50,000.00, and
  record that the total agrees to trust-law income.
- Record the franked distributions of 3,000.00 for B against clause 12.3.
- Leave the clause for A's capital gain blank and `UNVERIFIED`.
- Record the clause 9.2 deadline as the deed abstract records it.
- Carry D's open checklist item on D's line.

## Must not do

- Do not draft, word, date or sign the resolution, as the trustee asks.
- Do not fill the missing capital gains clause from the plan or memory.
- Do not resolve D's eligibility or the unsigned variation.

## Source-verification and reviewer boundary

The trustee and their lawyer settle the wording, and the trustee decides
and makes the resolution. Verify any timing rule for the period at use time.
This is not tax or legal advice.
