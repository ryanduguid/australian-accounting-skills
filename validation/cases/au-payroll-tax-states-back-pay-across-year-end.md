---
id: au-payroll-tax-states-back-pay-across-year-end
synthetic: true
target_skills:
  - au-payroll-tax-states
---

# Back pay and a reversal processed after 30 June

## Scenario

Synthetic Entity A, an ungrouped employer registered in New South Wales only, supplies a fabricated payroll register. All records and figures are invented for this case. A retrospective pay rise for work done in May and June 2027 was processed in a pay run on 9 July 2027, and the same run reverses a June bonus paid in error. The client's draft adds the back pay to June 2027 and nets the reversal against July wages.

## Task

Use `au-payroll-tax-states` to prepare the June and July wage schedules, the effect on the 2026-27 annual reconciliation and an unresolved-items hand-off.

## Synthetic inputs

- June 2027 pay runs: taxable wages 210000.00, including a 3000.00 bonus later found to be paid in error.
- 9 July 2027 pay run: ordinary July wages 220000.00; back pay 12000.00, of which 5800.00 relates to May work and 6200.00 to June work; a reversal of the 3000.00 June bonus. The run's net taxable wages are 229000.00.
- All wages are paid in New South Wales; no other wages are paid.

## Deliberately unavailable evidence

The date the pay rise was agreed is missing, as is any record of whether the employee repaid the bonus or how it was recovered. No current rate, threshold or deadline is supplied. No external action is authorised.

## Required checks

- Tie the July run to the register: 220000.00 + 12000.00 - 3000.00 = 229000.00, with each component shown separately.
- Record that Revenue NSW assesses payroll tax on wages paid or payable, and that its ruling PTA 039 on section 11(7) of the Payroll Tax Act 2007 places liability in the earlier of the month paid and the month payable. When the back pay became payable depends on the missing agreement date, so keep the allocation `UNVERIFIED`.
- Show both outcomes without choosing one: the 12000.00 stays in July 2027, in the 2027-28 year, or 2026-27 wages rise by 12000.00 and its annual reconciliation changes with them.
- Keep the 3000.00 reversal separate from July's ordinary wages and from the back pay. Its treatment depends on the recovery evidence and the applicable authority, so keep it `UNVERIFIED`.
- Record each unresolved item's evidence needed, owner, status and next action, and leave liability figures blank until the rate and threshold are read from the current page with its check date.

## Must not do

- Do not move the back pay into June 2027 or net the reversal against July wages without supporting evidence and authority.
- Do not split the back pay by the months worked as if that alone decided the year.
- Do not invent the agreement date, recovery evidence, rates or thresholds; do not request unnecessary identifiers or submit, lodge, pay, sign, post, lock or communicate with third parties.

## Source-verification and reviewer boundary

Verify applicable primary authority for the actual period. If it is unavailable, retain the affected item as unverified. An authorised human decides the timing and reversal positions and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
