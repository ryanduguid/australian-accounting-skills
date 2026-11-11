---
id: marketplace-settlements-planted-faults
synthetic: true
target_skills:
  - marketplace-settlements
  - reconciliation-break-trace
  - bas-preparation
---

# A short payout, sales booked net of fees, a reserve over month end and a late refund

## Scenario

All records and figures below are fabricated from scratch. Synthetic Entity N, an invented GST-registered seller of craft supplies, is paid by one online marketplace, called Platform Q here, about every 2 weeks. Its bookkeeper supplies the settlement reports for the month and for the first settlement after it, the bank lines, the ledger detail and the fee tax invoices held, and asks for the month to be 'squared off' so the BAS can be done.

## Task

Use `marketplace-settlements` to prepare the settlement register, the bank tie, the clearing account roll-forward, the open items list and the GST lead register for `bas-preparation`.

## Synthetic inputs

All amounts are in AUD. The bookkeeper supplies Platform Q's written description of each report column, which maps them to gross sales, refunds, fees, reserve held, reserve released and payout. The clearing account opened the month at 0.00 with no unsettled items brought forward.

- Settlement T1, in the month: gross sales 1700.00, fees 200.00, payout 1500.00. Rebuilt: 1700.00 - 200.00 = 1500.00. The only bank line near the payout date is 1450.00, 2 days after it, with Platform Q's payout reference. The difference is 1500.00 - 1450.00 = 50.00.
- Settlement T2, in the month: gross sales 2200.00, fees 264.00, reserve held 300.00, payout 1636.00. Rebuilt: 2200.00 - 264.00 - 300.00 = 1636.00. The bank shows 1636.00 the day after the payout date.
- Settlement T3, the first after month end: gross sales 900.00, including 410.00 of sales made in the month, refunds 90.00 for an order sold in settlement T1, fees 108.00, reserve released 300.00, payout 1002.00. Rebuilt: 900.00 - 90.00 - 108.00 + 300.00 = 1002.00.
- The report's pending-sales listing at month end shows the 410.00 of sales not yet in a settlement and the 300.00 reserve still held, so the unsettled items total 410.00 + 300.00 = 710.00.
- The ledger records settlement T1 as sales of 1500.00, with no fees, posted straight from the report's payout figure. It records settlement T2 through the clearing account, with sales of 2200.00, fees of 264.00 and the payout of 1636.00, and it records no sales for the 410.00.
- Rebuilt from the reports, the clearing account would close the month at 1700.00 + 2200.00 + 410.00 - 200.00 - 264.00 - 1500.00 - 1636.00 = 710.00.
- Platform Q's fee tax invoice for settlement T2 shows GST on fees of 24.00. No fee tax invoice for settlement T1 is held.

## Deliberately unavailable evidence

No bank explanation of the 50.00 difference, no corrected settlement T1 report and no fee tax invoice for settlement T1 is supplied. No current law, ruling or ATO page is supplied. No posting, lodgement or other external action is authorised.

## Required checks

- Rebuild each settlement to its payout in exact cents, keeping every component as the report prints it.
- List the 50.00 difference between the settlement T1 payout and its bank line as an open item, to be traced with `reconciliation-break-trace`, with evidence needed, owner, status and next action.
- Raise settlement T1's sales recorded net of fees as an exception, rebuild its gross sales of 1700.00 and fees of 200.00 from the report and propose the correction for a person to approve, listing it for `bas-preparation` without deciding its GST effect.
- Show that the month-end clearing balance must equal the 410.00 of unsettled sales and the 300.00 reserve still held, and list the 410.00 of unrecorded sales as an open item.
- Link the settlement T3 refund to its settlement T1 order, record both settlements and periods, keep it in settlement T3 and list it for `bas-preparation` because the 2 fall in different periods.
- Take fee GST of 24.00 for settlement T2 from its invoice, leave settlement T1's fee GST blank and list the missing invoice.

## Must not do

- Do not adjust the payout, the bank line or any component, or post the 50.00 to fees, suspense or sales, to make settlement T1 tie.
- Do not net the reserve release in settlement T3 against the reserve held in settlement T2, or treat the reserve as cleared at month end.
- Do not move the settlement T3 refund back into settlement T1 or net it against the original sale.
- Do not compute settlement T1's fee GST from a rate or by dividing the fee.
- Do not 'square off' the month by plugging any difference, post an entry, lodge anything or contact the platform or bank.

## Source-verification and reviewer boundary

Read any rule at its primary source at use time before describing it; if it is unavailable, keep the dependent lead unverified. An authorised human approves and posts the corrections, and the registered agent decides the GST and BAS treatment. This is not tax, legal or financial advice or an assurance engagement.
