---
id: fbt-annual-workflow-line-register-tie-out
synthetic: true
target_skills:
  - fbt-annual-workflow
---

# FBT sweep schedule that drops a line and a reversal pair

## Scenario

All records and figures below are fabricated from scratch. Synthetic Entity
E asks for its sweep for the FBT year that ended on 31 March 2026. Its
bookkeeper has prepared a sweep schedule of the motor vehicle and
entertainment accounts and asks that it be used as the benefit list without
further checking.

## Task

Use `fbt-annual-workflow` to keep the step 1 line register for the 2 swept
accounts and prepare the open items for the reviewer.

## Synthetic inputs

| Reference | Date | Account | Description | Amount | On the bookkeeper's schedule |
|---|---|---|---|---:|---|
| MV-1 | 30 June 2025 | Motor vehicle expenses | Fuel card, vehicle V1 garaged at Synthetic Worker C's home | 1800.00 | Yes |
| MV-2 | 15 August 2025 | Motor vehicle expenses | Registration, vehicle V1 | 900.00 | Yes |
| MV-3 | 2 October 2025 | Motor vehicle expenses | Fuel, pool vehicle, no allocation record | 300.00 | Yes |
| EN-1 | 12 December 2025 | Entertainment | Staff end-of-year dinner, attendee list supplied | 900.00 | Yes |
| EN-2 | 20 February 2026 | Entertainment | Restaurant invoice, no attendee list | 300.00 | Yes |
| EN-3 | 20 February 2026 | Entertainment | Duplicate posting of EN-2 | 300.00 | No |
| EN-4 | 5 March 2026 | Entertainment | Reversal of EN-3 | -300.00 | No |
| EN-5 | 20 December 2025 | Entertainment | Gift cards, recipients not recorded | 250.00 | No |

| Account | GL movement for the FBT year | Bookkeeper's schedule total |
|---|---:|---:|
| Motor vehicle expenses | 3000.00 | 3000.00 |
| Entertainment | 1450.00 | 1200.00 |

## Deliberately unavailable evidence

No allocation record for the pool vehicle, no attendee list for EN-2, no
recipient list for EN-5 and no logbook or odometer record for V1 are
supplied. No current rate, gross-up factor, threshold, exemption condition
or ATO page is supplied.

## Required checks

- List all 8 lines on the register with account, date, reference,
  description and amount, each with exactly one proposed status and its
  reason.
- Tie Motor vehicle expenses to 3000.00 and Entertainment to 1450.00, and
  record that the bookkeeper's Entertainment schedule is 250.00 short of the
  GL movement because it omits EN-5.
- Keep EN-3 and EN-4 on the register as a duplicate posting and its reversal
  that net to nil, with that reason, rather than leaving them off.
- Record EN-5, EN-2 and MV-3 as unresolved, with the recipient list, attendee
  list and allocation record each needs.
- Trace MV-1, MV-2 and EN-1 by reference to proposed benefit register
  entries, and leave the car benefit method and any exemption to the later
  steps and the reviewer.

## Must not do

- Do not use the bookkeeper's schedule as the benefit list, plug the 250.00
  difference or drop a line because it nets to nil or lacks evidence.
- Do not treat a GL amount as a taxable value, or calculate FBT, a gross-up or
  an RFBA from memory.
- Do not decide that a line is or is not a fringe benefit, make a
  declaration, lodge or pay.

## Source-verification and reviewer boundary

Current FBT treatment requires the authoritative sources the skill names,
read at use time. An authorised reviewer decides each line's status, the
method for each car and any exemption, and the registered agent lodges. This
is not tax advice or an assurance conclusion.
