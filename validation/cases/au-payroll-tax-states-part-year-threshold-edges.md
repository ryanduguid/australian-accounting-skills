---
id: au-payroll-tax-states-part-year-threshold-edges
synthetic: true
target_skills:
  - au-payroll-tax-states
---

# A part-year employer at the monthly threshold

## Scenario

Synthetic Entity A, an ungrouped employer, first employs staff in New South Wales on 1 January 2027 and pays no other Australian wages in the 2026-27 financial year. All records and figures are invented for this case. The client says registration was not needed until April 2027.

For this card only, the reviewer supplies fabricated parameters in place of the current Revenue NSW page: an annual threshold of 1000000.00 and monthly thresholds of 76712.00 for a 28-day month, 82192.00 for a 30-day month and 84932.00 for a 31-day month. They are not current figures.

## Task

Use `au-payroll-tax-states` to prepare the monthly registration test, the part-year threshold and an unresolved-items hand-off.

## Synthetic inputs

- Monthly taxable wages in 2027, tied to payroll and the ledger: January 80000.00, February 76712.00, March 84932.01, April 90000.00, May 90000.00, June 95000.00; total 516644.01.
- The fabricated card parameters described in the scenario.

## Deliberately unavailable evidence

No current threshold, rate, registration deadline or registration record is supplied. No external action is authorised.

## Required checks

- Count 181 days employed in the 365-day 2026-27 year, 1 January to 30 June 2027, and show the part-year threshold 1000000.00 x 181 / 365 = 495890.41.
- Show wages above the part-year threshold: 516644.01 - 495890.41 = 20753.60. No rate is supplied, so leave the liability blank.
- Apply the monthly test as Revenue NSW states it, wages more than the monthly threshold in any month: January 80000.00 against 84932.00 is not more; February 76712.00 equals 76712.00 and is not more; March 84932.01 is more than 84932.00 by 0.01. Registration looks required for March, not April, so flag the client's statement for the reviewer.
- Read the registration deadline from the current page or keep it `UNVERIFIED`.
- Record that the card parameters stand in for the live page only to test the comparisons and proration, and that a real result needs the current page's figures with its check date.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not round wages or thresholds before comparing, or treat wages equal to a threshold as more than it.
- Do not use the full annual threshold, a 12-month average or an equal monthly split of the annual threshold.
- Do not present the card parameters as current law or invent a rate or deadline; do not request unnecessary identifiers or submit, lodge, pay, sign, post, lock or communicate with third parties.

## Source-verification and reviewer boundary

Verify applicable primary authority for the actual period. If it is unavailable, retain the affected item as unverified. An authorised human decides registration and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
