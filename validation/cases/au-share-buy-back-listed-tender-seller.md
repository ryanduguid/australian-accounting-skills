---
id: au-share-buy-back-listed-tender-seller
synthetic: true
target_skills:
  - au-share-buy-back
---

# A shareholder in a listed company's off-market tender buy-back that straddles 30 June

## Scenario

All records and figures below are fabricated from scratch. An invented Australian resident individual tendered shares into an off-market tender buy-back by an invented listed public company. The company announced the buy-back in March 2026, accepted tenders on 26 June 2026 and paid on 3 July 2026. The client's portfolio tracker, set up from a template used for an older buy-back, splits the price into a capital component and a franked dividend.

## Task

Use `au-share-buy-back` to prepare the seller's schedule by parcel, with the classification, the market value record, the class ruling search and the unresolved-items hand-off.

## Synthetic inputs

Shares bought back: 500 at a buy-back price of 30.00 each, a total of 15000.00. Parcels: 300 shares bought in 2018 for 6000.00 including brokerage and 200 shares bought in 2023 for 5000.00 including brokerage. The offer booklet says a buy-back agreement is formed when the company accepts a tender. The tracker shows a capital component of 4.00 and a fully franked dividend of 26.00 per share. The company's announcement gives the buy-back price but no market value for tax purposes.

## Deliberately unavailable evidence

Only the supplied facts are available. Any class ruling for this buy-back, the company's market value calculation, the price and index data a TD 2004/22 calculation would need, and the first date the company indicated the buy-back was in serious contemplation are missing. No current rule text, ATO view or adviser decision is supplied.

## Required checks

- Classify the buy-back as off-market by a listed public company and record that no part of the price is a dividend (ss 159GZZZP(3) and 159GZZZPA), citing the ATO's statement that this applies to buy-backs announced after 7.30 pm AEDT on 25 October 2022, and list the tracker's dividend split as an error to correct.
- Record the CGT event time from the offer terms as 26 June 2026, when the company accepted the tender, not the 3 July 2026 payment, and so in the income year that ends on 30 June 2026.
- Record that the consideration is the purchase price of 15000.00 unless the market value as if the buy-back had not been proposed is higher, in which case it is that market value (s 159GZZZQ(2)), and that the reduction under s 159GZZZQ(3) does not apply to a listed public company.
- Mark market value `UNVERIFIED`, name the TD 2004/22 method and the data and first announcement date it needs, and record the search for a class ruling under the company's name.
- Show each parcel's cost base (6000.00 and 5000.00) and a preliminary gain of 4000.00 on the purchase price, stated as conditional on the market value not exceeding it, and pass the parcels to the capital gains workflow for the discount.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not report a dividend or franking credit from the buy-back, or adopt the tracker's split.
- Do not treat the payment date as the CGT event time, or assume the market value equals the buy-back price.
- Do not state a rule, rate or date from memory, or lodge, declare or communicate anything.

## Source-verification and reviewer boundary

Use Division 16K of Part III of the *Income Tax Assessment Act 1936*, TD 2004/22 and the ATO's Share buy-backs page for the actual period. Preserve unresolved review flags. A registered tax agent decides the seller's tax position. This is not tax, legal or financial advice or an assurance engagement.
