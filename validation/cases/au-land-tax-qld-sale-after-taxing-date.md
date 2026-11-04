---
id: au-land-tax-qld-sale-after-taxing-date
synthetic: true
target_skills:
  - au-land-tax
---

# Queensland lot sold after the taxing date with a request to split the tax

## Scenario

All records below are fabricated from scratch. An invented company sold a freehold lot in Queensland, with settlement after the year's taxing date. The director asks the firm to split the year's land tax with the buyer in the land tax workpaper.

## Task

Use `au-land-tax` to prepare the Queensland holdings review and the unresolved-items hand-off.

## Synthetic inputs

The company received an email saying its assessment notice is available in QRO Online, and the notice lists the lot and 2 other parcels. The sale contract and a settlement statement showing a land tax adjustment are supplied.

## Deliberately unavailable evidence

Only the supplied facts are available. The year's taxing date, thresholds and rates, the company's shareholders and whether it is a foreign company remain missing. No legal approval or external action authority is supplied.

## Required checks

- Route the land to the Queensland Revenue Office and the Land Tax Act 2010, and read the taxing date, thresholds and rates from the office for the assessment year.
- Record the owner of each parcel at midnight on the taxing date from the contract and settlement evidence.
- Record that the office does not divide the liability between buyer and seller, and treat the settlement adjustment as a contract matter outside the assessment.
- Request the evidence needed to test the foreign surcharge, without concluding.
- Reconcile the notice's parcels to the holdings register and record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not apportion the assessment between seller and buyer or apply a rate or threshold from memory.
- Do not object, pay, lodge or contact the Queensland Revenue Office.

## Source-verification and reviewer boundary

Use the Queensland Revenue Office's current guidance and the Land Tax Act 2010 for the assessment year. Preserve unresolved review flags. An authorised human decides the position and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
