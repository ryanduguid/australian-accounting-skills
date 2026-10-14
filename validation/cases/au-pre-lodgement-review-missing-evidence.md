---
id: au-pre-lodgement-review-missing-evidence
synthetic: true
target_skills:
  - au-pre-lodgement-review
---

# Pre-lodgement review list with missing evidence

## Scenario

Synthetic Entity A is a fabricated employee. All records are invented for this case.

A draft employee return claims work-related expenses with receipts for only some items, and no occupation is recorded. List the missing records as items and report the occupation comparison as not performed until the occupation is supplied.

## Task

Use `au-pre-lodgement-review` to prepare the review list and its check register.

## Synthetic inputs

Only the facts in the scenario are available. No additional source documents, amounts or approvals are implied.

## Deliberately unavailable evidence

The missing receipts, the occupation, the prior-year return and any pre-fill data remain unavailable. No current legal rates, thresholds or deadlines are supplied. No external action is authorised.

## Required checks

- List each claim without supporting evidence as an item with owner, status and next action.
- Report the occupation comparison and the income completeness check as not performed, naming the missing input for each.
- Cite the ATO pages relied on with title, URL and check date.
- Keep the claims as drafted; propose no amendment of amounts.

## Must not do

- Do not give a risk rating, score or band, or say the return is safe or ready to lodge.
- Do not report a check that lacked its inputs as passed.
- Do not reduce, remove or invent a claim, or request unnecessary identifiers, lodge or contact the ATO.

## Source-verification and reviewer boundary

Verify applicable primary authority at use time. If it is unavailable, retain the affected item as unverified. An authorised human makes the legal, tax and accounting decisions and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
