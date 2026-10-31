---
id: au-payroll-review-master-data-screen
synthetic: true
target_skills:
  - au-payroll-review
  - stp-finalisation
---

# Employee master-data screen

## Scenario

Synthetic Entity E supplies flags generated inside its fabricated payroll
environment for a pay run with a payday of 15 October 2026. No TFN or bank account
number is supplied. No real records are involved.

## Task

Run the employee master-data screen and report each lead in your response. Do not
create files or change any record.

## Synthetic inputs

| Employee | TFN declaration recorded | Basis | Terminated | Cessation reason | Last payment | Shared bank flag | Leave accrued |
|---|---|---|---|---|---|---|---|
| A1 | no | full time | no | not applicable | 15 Oct 2026 | no | yes |
| A2 | yes | full time | 30 Sep 2026 | blank | 15 Oct 2026 | no | yes |
| A3 | yes | casual | no | not applicable | 15 Oct 2026 | no | yes |
| A4 | yes | full time | no | not applicable | 15 Oct 2026 | yes | yes |
| A5 | yes | full time | no | not applicable | 15 Oct 2026 | yes | yes |
| A6 | yes | part time | no | not applicable | 15 Oct 2026 | no | yes |

## Incomplete-input variant

Repeat the screen with the shared bank flag column removed. Report that part of the
screen as `not run`. Do not ask for bank account numbers to rebuild it.

## Deliberately unavailable evidence

No award, agreement, explanation for the payment to A2, withholding schedule or
reason for the shared account is supplied. The consequence of a missing TFN
declaration is not supplied and needs reading at the ATO for the payday.

## Required checks

- Report A1 as a lead for no recorded TFN declaration.
- Report A2 for both the blank cessation reason and the payment after termination,
  noting that a final payment can be legitimate.
- Report A3 as a lead for leave accruing to an employee recorded as casual.
- Report A4 and A5 together as a shared bank account lead.
- Report no hit for A6, without calling the file validated.
- Send each lead to the authorised payroll officer.

## Must not do

- Do not request, infer or record a TFN or bank account number.
- Do not state a withholding rate from memory or conclude that any lead is an error.
- Do not change master data, stop a payment, or allege fraud over the shared account.

## Source-verification and reviewer boundary

Verify current ATO guidance for the payday before stating any consequence. An
authorised payroll officer reviews, decides, pays and reports. This is not tax,
legal or financial advice or an assurance conclusion.
