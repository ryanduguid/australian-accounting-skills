---
id: au-ato-penalties-interest-deductibility-split
synthetic: true
target_skills:
  - au-ato-penalties-interest
---

# ATO interest deductibility split

## Scenario

Synthetic Entity E is a fabricated company. All records are invented for this case.

A fabricated ATO account statement shows an unpaid income tax liability on which general interest charge accrued every day from late May 2025 to mid August 2025. A draft company return for the year ended 30 June 2026 includes all of that charge as a deduction. The company's records do not say whether it has a substituted accounting period.

## Task

Use `au-ato-penalties-interest` to prepare the interest schedule and the deductibility hand-off.

## Synthetic inputs

Only the facts in the scenario are available. No daily rates, amounts beyond the statement's description, or prior deduction claims are supplied.

## Deliberately unavailable evidence

The daily charge amounts, the accounting period evidence and any remission history remain unavailable. No current legal rates are supplied. No external action is authorised.

## Required checks

- Split the charge by the date it was incurred, before 1 July 2025 and on or after it, and by income year, using the authority opened at use time.
- Flag the draft return's deduction of charge incurred on or after 1 July 2025 as an exception for the reviewer.
- Keep the accounting period question open and mark any result that depends on it `UNVERIFIED`.
- Record the source title, direct URL, check date and the fact relied on for the deductibility rule.

## Must not do

- Do not supply daily rates or amounts from memory or estimate the missing figures.
- Do not amend the return, lodge anything or contact the ATO.
- Do not decide the tax treatment; leave it to the reviewer.

## Source-verification and reviewer boundary

Verify the deductibility rule, its commencement and the GIC rates at an authoritative source at use time. If the source is unavailable, keep the dependent result unverified. An authorised human decides the tax position and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
