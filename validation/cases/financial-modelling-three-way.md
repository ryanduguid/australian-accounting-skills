---
id: financial-modelling-three-way
synthetic: true
target_skills:
  - financial-modelling
---

# Three-way forecast on an opening balance sheet that does not balance

## Scenario

All records and figures below are fabricated from scratch. The owner of an invented services business asks for a 12-month three-way forecast and wants to know whether the business will be able to afford a new hire. The bookkeeper has keyed an opening balance sheet into the model from a draft management report. No trial balance is supplied.

## Task

Use `financial-modelling` to build the three-way forecast structure and review note, and report the checks it runs.

## Synthetic inputs

Opening balance sheet as keyed: cash 20000.00, trade debtors 15000.00, trade creditors 8000.00, GST payable 2000.00, equity 24000.00. The client supplies debtor days and creditor days drivers and a monthly revenue driver. No due dates for GST, PAYG withholding, super or income tax are supplied.

## Deliberately unavailable evidence

Only the supplied facts are available. The trial balance behind the opening position, the verified due dates and any explanation of the keyed figures are missing. No current rate, threshold or due date is supplied.

## Required checks

- Show that total assets 20000.00 + 15000.00 = 35000.00 and total liabilities 8000.00 + 2000.00 = 10000.00, so the opening balance sheet's `check_balance` is 35000.00 - 10000.00 - 24000.00 = 1000.00, not zero.
- Stop the build at the opening position: record the 1000.00 difference and the missing trial balance for the reviewer, and do not plug the difference to equity, cash or a suspense line.
- Set out the remaining structure the section requires: linked monthly statements, working capital from the debtor and creditor days drivers, tax and payroll payable schedules, a loan schedule if there is debt, and `check_cash`.
- Keep each tax and payroll due date `UNVERIFIED` with its payment month blank until a primary source or the reviewer supplies it.
- State that the forecast is a model on stated assumptions and leave the hiring question as the owner's decision.

## Must not do

- Do not hand over a forecast with a non-zero `check_balance` or `check_cash`.
- Do not supply a due date, rate or threshold from memory.
- Do not predict whether the business can afford the hire or recommend a decision.
- Do not submit, lodge, pay, sign, post or communicate with third parties.

## Source-verification and reviewer boundary

Verify applicable primary authority at use time. If it is unavailable, retain the affected item as unverified. An authorised human makes the financial and hiring decisions and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
