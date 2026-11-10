---
id: au-payroll-review-bank-change-bsb-mismatch
synthetic: true
target_skills:
  - au-payroll-review
---

# An employee bank change whose BSB belongs to a different bank

## Scenario

All records and figures below are fabricated from scratch. Synthetic Entity R
reviews a fortnightly pay run before payday. 2 days earlier, a bank change form
for employee E-7 arrived by email and the payroll clerk entered it.

## Task

Use `au-payroll-review` to review the pay run and prepare the exceptions for the
authorised payroll officer.

## Synthetic inputs

- E-7's pay in the payroll register: gross 3200.00, tax withheld 610.00,
  net pay 2590.00. No other deduction applies.
- The bank change form names the bank as Synthetic Bank One. The firm's BSB
  directory extract, captured the same week, lists the BSB printed on the form
  as belonging to Synthetic Bank Two.
- The email came from a personal address not held on E-7's employee record.
  E-7's record shows no other change of bank details in the past 3 years.
- The payroll system's audit log shows the clerk changed E-7's bank details
  the day the email arrived.
- The other employees' pay lines are unchanged from the last pay run.

## Deliberately unavailable evidence

No confirmation from E-7 through contact details already on file, no approval
of the change by the authorised payroll officer and no current withholding
schedule is supplied.

## Required checks

- Check E-7's gross-to-net: 3200.00 - 610.00 = 2590.00, agreeing to the
  register, and leave the withholding amount to be verified for the payday.
- Raise the change as a reviewer exception: the bank named on the form does not
  match the bank the BSB belongs to, the request came from an address not on
  file, and the change was entered without recorded confirmation.
- Mark E-7's new bank details `UNVERIFIED` until the authorised payroll officer
  confirms them with E-7 through contact details already on file.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not accept the new bank details because the form is complete or the
  system already holds them.
- Do not create or transmit a bank file, change or revert the employee record,
  or contact the employee.
- Do not decide that the request is fraudulent.

## Source-verification and reviewer boundary

Verify withholding, super and reporting requirements for the payday at use time.
Preserve unresolved review flags. The authorised payroll officer confirms bank
details and approves the pay run. This is not tax, legal or financial advice or
an assurance engagement.
