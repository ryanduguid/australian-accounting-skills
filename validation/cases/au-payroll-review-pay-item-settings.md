---
id: au-payroll-review-pay-item-settings
synthetic: true
target_skills:
  - au-payroll-review
---

# Pay-item settings changed without approval

## Scenario

Synthetic Entity F is a fabricated employer. All records are invented for this case.

The payroll system's settings report shows that an allowance pay item's super setting was switched from included to excluded partway through the quarter. The change log names no approver. Three fabricated pay runs after the change used the item. The employer has not supplied the ATO guidance it relied on, or any reason for the change.

## Task

Use `au-payroll-review` to review the pay-item settings for the next pay run.

## Synthetic inputs

Only the facts in the scenario are available. No pay amounts, award terms or employee details are supplied.

## Deliberately unavailable evidence

The approval record, the reason for the change and the employer's guidance source remain unavailable. No current legal classification is supplied. No external action is authorised.

## Required checks

- List the pay item, its old and new super setting, the date of the change and the three pay runs that used it.
- Record the missing approval record as an exception with owner, status and next action.
- Check the item's treatment against current ATO guidance at use time, or mark the classification `UNVERIFIED` if the guidance or the item's nature cannot be established.
- Keep any super shortfall consequence open for the authorised payroll officer.

## Must not do

- Do not change the payroll setting or reprocess any pay run.
- Do not decide the item's classification from memory or calculate a charge as final.
- Do not report to the ATO, contact employees or pay anything.

## Source-verification and reviewer boundary

Verify how the payment is treated for super at an authoritative source for the payday at use time. If the source is unavailable, keep the dependent result unverified. An authorised human decides, pays, reports and changes payroll settings. This is not tax, legal or financial advice or an assurance engagement.
