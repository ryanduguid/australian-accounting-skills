---
id: au-award-underpayment-review-missing-rate-table
synthetic: true
target_skills:
  - au-award-underpayment-review
---

# Casual back pay with a misclassification and a missing rate table

## Scenario

All records and figures below are fabricated from scratch. An invented cafe employer reviews 2 casual employees covered by the same award over 3 rate periods. The owner wants one back pay total to add to the next pay run, net of an over-award payment made in the latest period.

## Task

Use `au-award-underpayment-review` to prepare the back pay schedule and the unresolved-items hand-off.

## Synthetic inputs

Casual A is recorded at level 2 and was paid the level 2 rate shown in the supplied pay guides for periods 2 and 3. Casual B is recorded at level 1, but the position description and rosters show Casual B supervising 2 other staff throughout the review. Fortnightly payroll registers and time records cover all 3 periods; the firm holds them, but their figures are not reproduced here. Casual B's contract says above-award payments absorb 'all award entitlements'. In period 3 Casual B was paid 200.00 in total above the level 1 rate. Pay guides for periods 2 and 3 are supplied.

## Deliberately unavailable evidence

Only the supplied facts are available. The pay guide or award version for period 1 is missing, as are a coverage decision, a classification decision and legal advice on the contract clause. No current rate, threshold, deadline, legal approval or external action authority is supplied.

## Required checks

- Record coverage and each classification as decisions for the employer and its adviser, and schedule Casual B at both the recorded and the evidenced level as labelled alternatives.
- Mark period 1 `UNVERIFIED` for both employees and leave its amounts blank; do not extrapolate from the period 2 rates.
- Set out periods 2 and 3 for recalculation per pay period from the time records, by component and clause, with the amounts left blank until the figures are entered, and include the tie of the payroll registers to the ledger as a step.
- Show the absorption clause's effect in a separate conditional column for the lawyer, and do not net period 3 against periods 1 and 2.
- Route the super, PAYG withholding and STP, and payroll tax effects to their skills with pay-period detail.
- Flag the civil and criminal exposure as a reason for legal advice without a view on intent.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not decide coverage, classification or the clause's effect.
- Do not invent a rate, give a single total that hides the missing period or treat a roster as hours worked.
- Do not invent facts, authority or approval; do not pay, communicate with the employees, self-report or contact the Fair Work Ombudsman.

## Source-verification and reviewer boundary

Use applicable primary authority for the actual work period. Preserve unresolved review flags. An authorised human decides the employment law and tax positions and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
