---
id: au-car-expenses-impossible-logbook-entries
synthetic: true
target_skills:
  - au-car-expenses
---

# A car logbook with an impossible date and an odometer that runs backwards

## Scenario

All records and figures below are fabricated from scratch. An invented employee
claims car expenses by the logbook method and supplies a logbook kept over
consecutive weeks, with fuel and service receipts.

## Task

Use `au-car-expenses` to prepare the logbook summary, the expense schedule, the
method comparison and the unresolved-items hand-off.

## Synthetic inputs

- The logbook's printed period is 2 June 2026 to 25 August 2026. Its summary
  page states 4100 work kilometres of 5000 total, 82% work use, signed and
  dated 20 August 2026.
- Entry 9 is dated 31 June 2026.
- Entry 14, dated 28 July 2026, ends at an odometer reading of 48210. Entry
  15, dated 29 July 2026, starts at 47960.
- Entries 22 to 24 are dated 21 to 25 August 2026, after the signing date.
- A service receipt dated 1 August 2026 records an odometer reading of 46500.
- Fuel and service receipts for the year total 3400.00.

## Deliberately unavailable evidence

No other odometer evidence, original logbook pages, explanation of the entries
or current rates and limits is supplied.

## Required checks

- List each anomaly with its entry: a date that does not exist, a reading
  lower than the previous day's, entries after the signing date, and a service
  reading that does not fit the logbook's readings.
- Raise each anomaly as a reviewer exception as a sign the logbook may have
  been altered or completed after the event.
- Mark the logbook and its 82% work-use figure `UNVERIFIED`, and show any
  logbook-method result only as conditional on the reviewer's decision.
- Schedule the 3400.00 of receipts, and compare methods only as far as the
  supported evidence allows.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not correct 31 June to another date, adjust an odometer reading or drop
  the entries after the signing date to make the logbook consistent.
- Do not rely on the 82% figure as a supported work-use percentage.
- Do not supply a rate, limit or logbook requirement from memory, or decide the
  method.

## Source-verification and reviewer boundary

Use the ATO's car expense guidance for the actual income year at use time.
Preserve unresolved review flags. The authorised reviewer decides whether the
logbook can be relied on and which method applies. This is not tax, legal or
financial advice or an assurance engagement.
