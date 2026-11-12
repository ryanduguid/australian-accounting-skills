---
id: marketplace-settlements-transit-and-carried-balance
synthetic: true
target_skills:
  - marketplace-settlements
---

# A negative settlement carried forward and a month-end payout still in transit

## Scenario

All records and figures below are fabricated from scratch. Synthetic Entity R, an invented GST-registered seller of bicycle parts, sells through one online marketplace, called Platform S here. A chargeback early in the month turned one settlement negative, and the last payout of the month reached the bank after month end. The bookkeeper asks why the clearing account 'won't go to nil' and asks for the difference to be written off.

## Task

Use `marketplace-settlements` to prepare the settlement register, the bank tie and the clearing account roll-forward with its period-end check.

## Synthetic inputs

All amounts are in AUD. The bookkeeper supplies Platform S's written description of each report column, which maps them to gross sales, refunds (including chargebacks), fees (including chargeback fees), balance carried from another settlement and payout. The ledger records sales, refunds and fees when they occur, and records each payout when the bank receives it. The clearing account opened the month at 0.00 with no unsettled items brought forward.

- Settlement U1, days 1 to 10: gross sales 300.00, fees 30.00, a chargeback of 500.00 on an order sold in the previous month and a chargeback fee of 25.00. Rebuilt: 300.00 - 30.00 - 500.00 - 25.00 = -255.00. The report shows a payout of nil and carries the -255.00 to the next settlement. No bank or card debit appears.
- Settlement U2, days 11 to 30: gross sales 2000.00, fees 200.00 and the -255.00 balance carried from settlement U1. Rebuilt: 2000.00 - 200.00 - 255.00 = 1545.00, with a payout date of day 31. The bank shows 1545.00 on day 2 of the next month, carrying the payout reference.
- The report's pending listing at month end shows sales of 400.00 made on day 31, a refund of 40.00 issued on day 31 on one of those orders and fees of 40.00 charged on them, all due in the next settlement: 400.00 - 40.00 - 40.00 = 320.00 not yet in a paid settlement. No reserve is held and the report shows nothing owed to the platform at month end.
- The ledger's month totals are sales 300.00 + 2000.00 + 400.00 = 2700.00, fees 30.00 + 25.00 + 200.00 + 40.00 = 295.00 and refunds 500.00 + 40.00 = 540.00, and it records no payout in the month.
- Clearing roll-forward: 0.00 + 2700.00 - 295.00 - 540.00 = 1865.00. Expected from the reports: 320.00 unsettled, plus 0.00 reserves, plus the 1545.00 payout in transit, less 0.00 owed to the platform: 320.00 + 0.00 + 1545.00 - 0.00 = 1865.00.

## Deliberately unavailable evidence

Only the supplied facts are available. No chargeback dispute papers, current law or ATO guidance is supplied. No posting, write-off or other external action is authorised.

## Required checks

- Rebuild settlement U1 to its -255.00 result and settlement U2 to its 1545.00 payout in exact cents, keeping the chargeback, the chargeback fee and the carried balance as separate components.
- Record that the -255.00 balance carried from settlement U1 stays in the clearing account and is not posted again in settlement U2, and that settlement U1 needs no bank line because the report carries its result forward.
- Treat the 1545.00 payout dated day 31 as in transit at month end, tied to its bank line on day 2 of the next month by amount, date and reference.
- Show that the month-end clearing balance of 1865.00 equals the 320.00 net of the unsettled sales and the refund and fees on the unsettled orders, plus the 1545.00 in transit, with nothing left as an open item.
- Link the chargeback to its order from the previous month and list it for `bas-preparation`, because the 2 fall in different periods, without deciding its GST effect.

## Must not do

- Do not post the -255.00 carried balance as an expense, adjustment or fee in settlement U2.
- Do not write off, plug or post to suspense any part of the 1865.00 clearing balance, or treat the payout in transit as missing from the bank.
- Do not leave the refund and fees on the unsettled orders out of the period-end check.
- Do not assume a report column's meaning beyond Platform S's supplied description, post an entry, lodge anything or contact the platform.

## Source-verification and reviewer boundary

Read any rule at its primary source at use time before describing it; if it is unavailable, keep the dependent lead unverified. An authorised human approves and posts the entries and decides the GST treatment. This is not tax, legal or financial advice or an assurance engagement.
