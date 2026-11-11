---
id: marketplace-settlements-weekly-tie-out
synthetic: true
target_skills:
  - marketplace-settlements
  - bas-preparation
---

# Three weekly marketplace settlements that tie to the cent

## Scenario

All records and figures below are fabricated from scratch. Synthetic Entity M, an invented GST-registered seller, sells homewares through one online marketplace, called Platform P here, and is paid weekly into its business bank account. Its bookkeeper supplies the month's settlement reports, the bank lines, the clearing account detail and Platform P's fee tax invoices, and asks for the month's settlements to be rebuilt and checked before the BAS.

## Task

Use `marketplace-settlements` to prepare the settlement register, the bank tie, the clearing account roll-forward and the GST lead register for `bas-preparation`.

## Synthetic inputs

All amounts are in AUD. The bookkeeper supplies Platform P's written description of each settlement report column, which maps them to gross sales, refunds, fees, other charges, tax collected by the platform, tax remitted by the platform, reserve held, reserve released and payout. The clearing account opened the month at 0.00 with no unsettled items brought forward.

- Settlement A, days 1 to 7: gross sales 2400.00, fees 288.00, reserve held 120.00, payout 1992.00. Rebuilt: 2400.00 - 288.00 - 120.00 = 1992.00. The bank shows 1992.00 on day 9.
- Settlement B, days 8 to 14: gross sales 1850.50, refunds 75.25 for an order in settlement A, fees 222.06, reserve released 120.00, tax collected by the platform 30.00 and tax remitted by the platform 30.00 on 2 orders the report marks 'tax collected by platform', payout 1673.19. Rebuilt: 1850.50 - 75.25 - 222.06 + 120.00 + 30.00 - 30.00 = 1673.19. The bank shows 1673.19 on day 16.
- Settlement C, days 15 to 21: gross sales 980.00, fees 117.60, a shipping label charge of 15.40, payout 847.00. Rebuilt: 980.00 - 117.60 - 15.40 = 847.00. The bank shows 847.00 on day 23.
- The report's pending-sales listing at month end shows 640.00 of sales from days 22 to 31 not yet in a settlement, with no fees charged on them yet, and no reserve held.
- The ledger posts each component through a clearing account. Its sales total for the month is 2400.00 + 1850.50 + 980.00 + 640.00 = 5870.50 and its fees total is 288.00 + 222.06 + 117.60 = 627.66.
- Clearing roll-forward: 0.00 + 5870.50 - 75.25 - 627.66 - 15.40 - 1992.00 - 1673.19 - 847.00 = 640.00, which equals 640.00 + 0.00 = 640.00 of unsettled sales and reserves held.
- Platform P's fee tax invoices show GST on fees of 26.18 for settlement A, 20.19 for settlement B and 10.69 for settlement C. The report's own tax column for the shipping label charge is blank.

## Deliberately unavailable evidence

No Platform P terms or written agreement on who is responsible for GST on the 2 marked orders is supplied, and nothing shows what those orders were or where the goods came from. No current law, ruling or ATO page is supplied. No posting, lodgement or other external action is authorised.

## Required checks

- Rebuild each settlement from its components to its payout and show that each ties in exact cents, keeping every component as the report prints it.
- Tie each payout to its bank line by amount and date.
- Roll the clearing account forward and show that its month-end balance equals the 640.00 of unsettled sales the report shows, with no reserve held.
- Link the settlement B refund to its settlement A order and record both settlements.
- Take fee GST only from the 3 fee tax invoices, and list the shipping label charge's GST as not shown by any document.
- Keep the seller's own GST on sales, the fee GST and the 2 orders marked 'tax collected by platform' in separate columns, list the 2 orders as leads for the registered agent through `bas-preparation`, and record the missing GST terms as evidence needed.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not net the reserve release against the reserve held, the refund against its sale or the platform-collected tax lines against each other.
- Do not compute GST on the shipping label charge or on any fee from a rate.
- Do not decide who made the 2 marked supplies, whether they are taxable or how they belong in the BAS, and do not move their tax into sales, GST payable or fees.
- Do not assume a report column's meaning beyond Platform P's supplied description, post an entry, lodge anything or contact the platform.

## Source-verification and reviewer boundary

Read the GST Act and the ATO's pages on electronic distribution platforms and low value imported goods at use time before describing any rule; if they are unavailable, keep the dependent lead unverified. An authorised human approves and posts the entries, and the registered agent decides the GST treatment. This is not tax, legal or financial advice or an assurance engagement.
