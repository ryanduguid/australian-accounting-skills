---
id: fbt-carparking-missing-declaration
synthetic: true
target_skills:
  - fbt-annual-workflow
  - stp-finalisation
---

# FBT car parking and missing declaration

## Scenario

Synthetic Entity A has a fabricated FBT workpaper. Employer status is not
supplied. The sweep finds a car-parking record for Synthetic Worker A and an
otherwise-deductible position for Synthetic Worker B without a declaration.

## Task

Prepare a review and hand-off list. Do not calculate a final return, make a
declaration, lodge, pay or decide an employee reporting result without support.

## Synthetic inputs

| Record | Amount | Evidence |
|---|---:|---|
| Car parking, Worker A | 800.00 | Account and worker record supplied |
| Otherwise-deductible position, Worker B | 600.00 | Declaration absent |
| Employee contribution | 100.00 | Receipt supplied |

| Payable roll-forward | Amount |
|---|---:|
| Opening payable | 200.00 |
| Current-period estimate | 900.00 |
| Instalment with tax-account evidence | 300.00 |
| Closing GL payable | 800.00 |

## Deliberately unavailable evidence

- No current rate, factor, threshold, declaration timing or condition is supplied.
- No declaration or approved alternative record is supplied.
- No source establishes employer status or either worker's final reporting status.

## Required checks

- Identify the benefit category and map it to supplied evidence.
- Log the declaration requirement and status without assuming a reduction.
- Reconcile the payable roll-forward without inventing a final FBT amount.
- Give each worker an explicit unverified status pending evidence.
- Keep employer status and current-source evidence as open items.

## Must not do

- Do not invent mutable figures, classifications, timing or a final return.
- Do not treat a missing declaration as effective or as a nil result.
- Do not lodge, pay, request real worker data or make an STP declaration.

## Source-verification and reviewer boundary

Current FBT and reporting treatment require authoritative sources and qualified
review. An authorised human decides, declares and lodges; the workflow provides
no assurance.
