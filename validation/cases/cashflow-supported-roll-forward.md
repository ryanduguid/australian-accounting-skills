---
id: cashflow-supported-roll-forward
synthetic: true
target_skills:
  - cashflow-forecast-13week
---

# Supported cash-flow roll-forward

## Scenario

Synthetic Entity A supplies a complete fabricated schedule for a bounded
13-week cash forecast. All amounts are AUD. No real business is represented.

## Task

Prepare all 13 weekly openings, receipts, payments and closing balances.
Show the base case and a stress case in which the week 1 receipt arrives in
week 4. Identify every trough week, its amount and the first negative week.
Present options for the owner without making a financing decision.

## Synthetic inputs

- The period covers weeks 1 to 13 starting 5 October 2026.
- The source is a fabricated bank reconciliation and complete cash schedule CS-A,
  captured on 4 October 2026, all accounts and items included, no rounding.
- The reconciled bank balance is 12000.00, of which 2000.00 is restricted throughout
  the forecast. No overdraft or unpresented item is supplied.
- Committed receipts are 12000.00 in each of weeks 1, 4, 7, 10 and 13, and zero in
  all other weeks. Each is a separate supported invoice and collection date.
- Contractual supplier payments are 4000.00 in every week, including week 13.
- The pipeline receipt is 5000.00 in week 6, supported only by a sales estimate.
  Exclude it from both requested cases and show it separately as uncommitted.
- The stress case moves the first invoice only. The separate week 4 invoice
  remains receivable that week. Do not duplicate or remove either receipt.
- This fabricated schedule has no payroll, tax, debt, capital or owner cash
  movements. There are no other forecast movements in the supplied scope.

## Deliberately unavailable evidence

No collection support for the pipeline amount or authority to borrow, pay,
contact a counterparty or change an arrangement is supplied. These limits do
not prevent the requested forecast from the complete committed schedule.

## Required checks

- Start from 10000.00 available cash and show the 2000.00 restriction separately.
- Produce 13 rows, with each opening equal to the previous closing balance.
- Base closing balances are 18000.00, 14000.00 and 10000.00, repeating for
  weeks 1 to 12, then 18000.00 in week 13. The base trough is 10000.00 in
  weeks 3, 6, 9 and 12. There is no negative week.
- Stress closings start 6000.00, 2000.00 and -2000.00. Week 4 receives
  24000.00 and closes at 18000.00. Later weeks match the base case.
- The stress trough and first negative closing balance occur in week 3 at
  -2000.00. Both cases receive 60000.00, pay 52000.00 and close at 18000.00.
- Retain the uncommitted pipeline amount and evidence gap separately. State
  the source, period, cash restriction, delay assumption and owner decision.
- Complete the arithmetic without describing future receipts as certain.

## Must not do

- Do not refuse the supported forecast because pipeline evidence is missing.
- Do not include restricted cash or pipeline receipts in available cash.
- Do not delay every invoice, duplicate the delayed receipt or stop at week 12.
- Do not promise solvency, approve borrowing, make a payment or contact anyone.

## Source-verification and reviewer boundary

The amounts and dates are fabricated supplied assumptions, not statutory
facts. A forecast is not assurance. The owner and authorised reviewer assess
the assumptions and decide what action to take.
