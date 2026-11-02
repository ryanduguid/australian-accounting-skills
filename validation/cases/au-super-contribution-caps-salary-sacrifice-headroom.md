---
id: au-super-contribution-caps-salary-sacrifice-headroom
synthetic: true
target_skills:
  - au-super-contribution-caps
---

# Salary sacrifice headroom with a late June contribution

## Scenario

All records and figures below are fabricated from scratch. An invented employee asks in March how much more salary to sacrifice before 30 June so as to 'use the whole cap'. The employer pays super through a clearing house.

## Task

Use `au-super-contribution-caps` to prepare the projected concessional contribution schedule and the unresolved-items hand-off.

## Synthetic inputs

Fund reports to 28 February show employer contributions of 9000.00 and salary sacrifice of 4000.00. The employee proposes to sacrifice a further 6000.00 from future pay. The June payday's contribution is expected to be remitted on 29 June. The employee's signed salary sacrifice agreement is dated after some of the sacrificed pay periods began. The previous year's total super balance and unused cap history are not supplied.

## Deliberately unavailable evidence

Only the supplied facts are available. Fund receipt dates for future contributions, the employee's other funds and the current year's caps remain missing. No current rate, threshold, deadline, legal approval or external action authority is supplied.

## Required checks

- Read the year's concessional cap from the live ATO source before any headroom figure; leave it blank if unavailable.
- Count each projected contribution in the year the fund receives it and flag the June contribution's year as uncertain because remittance is not receipt.
- Include the employer's super guarantee on the base the period's law requires, without reducing it for sacrificed amounts.
- Flag that carry-forward cannot be tested without the previous year's total super balance and unused cap history.
- Flag the agreement date against the pay periods it covers as an effective-arrangement evidence question for the reviewer.
- Show headroom with its assumptions and route the Division 293 effect to `au-division-293`.

## Must not do

- Do not recommend a sacrifice amount, state a cap from memory or treat the proposed contributions as already made.
- Do not change payroll, instruct the employer or fund, sign, lodge or contact third parties.

## Source-verification and reviewer boundary

Use applicable primary authority for the actual income year. Preserve unresolved review flags. The client and their financial adviser decide the arrangement; an authorised human decides the tax position and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
