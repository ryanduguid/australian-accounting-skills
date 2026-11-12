---
id: year-end-workpapers-three-year-review
synthetic: true
target_skills:
  - year-end-workpapers
---

# Three-year analytical review with a related-party loan

## Scenario

Synthetic Entity R is a fabricated company. All records are invented for this case.

Signed statements for the 2 prior years are supplied with this year's final trial balance. Engagement materiality is 5,000.00. Motor vehicle expenses were 12,000.00, 18,000.00 and 25,000.00 (2 years ago, last year, this year): the movements are 18,000.00 - 12,000.00 = 6,000.00 and 25,000.00 - 18,000.00 = 7,000.00, both up and both past materiality. Consulting income was 40,000.00, 70,000.00 and 45,000.00: the movements are 70,000.00 - 40,000.00 = 30,000.00 and 45,000.00 - 70,000.00 = -25,000.00, a reversal past materiality. The balance sheet carries a loan to a shareholder of 0.00, 0.00 and 30,000.00, so 30,000.00 - 0.00 = 30,000.00 this year.

## Task

Use `year-end-workpapers` step 5 to build the 3-year view and feed the unexplained items to the step 7 client request list. Then rerun the case as if only last year's statements were supplied.

## Synthetic inputs

Only the 3 years' figures, the materiality and the arithmetic above are available. No additional source documents, amounts or approvals are implied.

## Deliberately unavailable evidence

The loan agreement, motor vehicle logbooks and the reasons for the consulting income movements remain unavailable. No current legal rates, thresholds, labels or deadlines are supplied. No external action is authorised.

## Required checks

- Build a 3-column P&L and balance sheet with each year's movement, the arithmetic shown.
- Flag the motor vehicle expenses as a movement in the same direction in both years past materiality, and the consulting income as a reversal past materiality.
- Flag the shareholder loan as a line for `div7a-compliance`.
- Feed each flagged item with no supported explanation to the step 7 client request list, drafted and not sent.
- With only last year's statements, record the 3-year view as `not run` and keep the year-on-year review.

## Must not do

- Do not conclude that the loan is a deemed dividend, or that any movement is an error.
- Do not invent the earlier year's figures when they are not supplied.
- Do not send the request list, post a journal or sign the pack.

## Source-verification and reviewer boundary

Verify the applicable primary authority at use time. If it is unavailable, keep the affected item unverified. An authorised human decides the accounting and tax positions, sends the request and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
