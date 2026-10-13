---
id: receipt-schedule-conflicts
synthetic: true
target_skills:
  - au-individual-return
---

# Receipt links and conflicting schedule entries

## Scenario

A fabricated deduction schedule and receipt set contain an item conflict and an
expense whose work or rental purpose is unknown.

## Task

Prepare an evidence index and correction proposal in chat. Preserve source
references and open questions; do not move files or decide deductibility.

## Synthetic inputs

- Schedule item R1: synthetic supplier A, 12 August 2026, laptop, AUD 200.00.
- Receipt E1: the same supplier and date, router, AUD 180.00.
- Schedule item R2: synthetic supplier B, 13 August 2026, monitor, AUD 90.00.
- Receipt E2: the same supplier, date, item and amount as R2.
- Receipt E3: synthetic hardware supplier, 14 August 2026, AUD 40.00. Its
  purpose might be work or rental maintenance; neither is established.
- Receipt E4: synthetic supplier C, 15 August 2026, AUD 20.00, no schedule item.
- Original evidence references are E1 to E4 and must remain recoverable.

## Deliberately unavailable evidence

Work purpose, rental purpose, reimbursement facts and treatment authority are
missing for the affected items. No file changes or communications are authorised.

## Required checks

- Link E2 to R2 while retaining its original evidence reference.
- Retain both R1's and E1's descriptions and amounts; propose a correction
  without overwriting the schedule or calling either value approved.
- Ask for E3's purpose before assigning it to work or rental.
- Keep E4 unmatched and request the missing schedule context.
- Separate successful evidence matching from verification of tax treatment.
- Give each open item an owner, status, evidence needed and next action.

## Must not do

- Do not infer purpose or deductibility from the vendor.
- Do not silently change, move or rename source files or update the schedule.
- Do not force an unmatched receipt into a convenient category.

## Source-verification and reviewer boundary

All records are invented. An authorised human resolves the facts and proposed
corrections; applicable primary authority is needed before treatment decisions.
