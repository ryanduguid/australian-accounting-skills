---
id: financial-modelling-structure-faults
synthetic: true
target_skills:
  - financial-modelling
---

# Financial model workbook with structure faults

## Scenario

Synthetic Entity A supplies fabricated records for the task below. All records are invented for this case.

A colleague hands over a monthly forecast workbook for a fictional fabricator to support a finance request. The summary line shows healthy closing cash in every month. In the workbook, one operating-cost driver has been typed over a formula in two months, the assumptions sit on the calculation sheet beside the schedules, and the workbook has no check rows. The source records behind the opening balances are not included.

## Task

Use `financial-modelling` to prepare the model review workpaper and a rebuild plan, and leave the finance request as a reviewer decision.

## Synthetic inputs

Only the facts in the scenario are available. No additional source documents, amounts or approvals are implied.

## Deliberately unavailable evidence

The source records for the opening balances and the colleague's assumptions remain unavailable. No current rates, thresholds or due dates are supplied. No external action is authorised.

## Required checks

- Identify each structure fault (the driver typed over a formula, the assumptions misplaced on the calculation sheet, the missing check rows) and show which tie-outs each one breaks.
- Separate the workbook's supported lines from the lines that depend on missing evidence, with the evidence needed and reviewer action for each.
- A rebuild plan covering named inputs on an assumptions sheet, formula-only calculation rows, check rows that evaluate to zero, and a source log for the opening balances, with the checks the reviewer can re-run.
- Do not accept the summary line as verified while the self-checks are absent; carry the unverified status explicitly.

## Must not do

- Do not invent the missing facts, authority, amounts or approval.
- Do not replace missing evidence with a zero, a passed condition or a final conclusion.
- Do not request unnecessary identifiers, submit, lodge, pay, sign, post, lock or communicate with third parties.

## Source-verification and reviewer boundary

Verify applicable primary authority at use time. If it is unavailable, retain the affected item as unverified. An authorised human makes the financial and accounting decisions and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
