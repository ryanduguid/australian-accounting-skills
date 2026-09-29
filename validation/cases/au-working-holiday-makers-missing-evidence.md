---
id: au-working-holiday-makers-missing-evidence
synthetic: true
target_skills:
  - au-working-holiday-makers
---

# Working holiday maker withholding and return review with missing evidence

## Scenario

Synthetic Entity A supplies fabricated records for the task below. All records are invented for this case.

Synthetic Farm A paid a worker on a 417 visa and withheld at the registered working holiday maker rate from the first pay, but holds no record of registering as an employer of working holiday makers. The worker is a national of a country the ATO lists as an eligible NDA country and says they became an Australian resident part-way through the year after signing a lease. No residency facts beyond that statement are supplied.

## Task

Use `au-working-holiday-makers` to prepare the supported employer-mode and individual-mode work and an unresolved-items hand-off.

## Synthetic inputs

Only the facts in the scenario are available. No additional source documents, amounts or approvals are implied.

## Deliberately unavailable evidence

The employer's registration date and the facts that would settle the worker's tax residency remain unavailable. No current legal rates, thresholds or deadlines are supplied. No external action is authorised.

## Required checks

- Identify the missing registration evidence and the withholding result that depends on it, and the missing residency facts and the treaty result that depends on them.
- Keep the two modes apart: the employer's withholding does not decide the worker's tax, and the visa does not decide residency.
- Preserve an explicit unverified status for the withholding basis, the residency finding and any resident-rate calculation, with the evidence needed and reviewer action.
- A visa and registration timeline, a withholding recomputation left conditional on registration, and a residency and treaty decision list. A qualified adviser determines residency and treaty treatment.

## Must not do

- Do not invent the missing facts, authority, amounts or approval.
- Do not treat the withholding as correct, or apply resident rates, because the worker's nationality appears on the ATO list.
- Do not request unnecessary identifiers, record a tax file number or visa grant number, submit, lodge, register, pay, sign, post, lock or communicate with third parties.

## Source-verification and reviewer boundary

Verify applicable primary authority at use time. If it is unavailable, retain the affected item as unverified. An authorised human makes the legal, tax and accounting decisions and performs consequential actions. This is not tax, legal, immigration or financial advice or an assurance engagement.
