---
id: au-main-residence-spouses-acreage-foreign-resident
synthetic: true
target_skills:
  - au-main-residence
---

# Spouses with different homes, a block over 2 hectares and an owner who has moved overseas

## Scenario

All records and figures below are fabricated from scratch. Invented spouses P and Q own a farmhouse on a 6 hectare block as tenants in common, P with a 60 part interest and Q with a 40 part interest out of 100. Q also owns a city apartment outright. From the purchase of the block both lived in the farmhouse; for a later period P lived in the farmhouse and Q in the apartment, neither living permanently separately and apart. Three years before the farmhouse sale contract, P took a job overseas, and P's records describe P as a foreign resident from that date. Q remained an Australian resident. Around the farmhouse, 1.5 hectares is garden and house paddock; the other 4.5 hectares has been leased to a neighbour for grazing throughout.

## Task

Use `au-main-residence` to prepare each spouse's eligibility and residency record, the dwelling and land schedule, the period schedule with the spouses' choices, and the unresolved-items hand-off for the farmhouse sale.

## Synthetic inputs

Farmhouse and block: contract and settlement dates for the purchase and the sale are supplied, as are the lease to the neighbour, a title plan with the land areas and the land under the farmhouse of 0.05 hectares. P's employment contract overseas and P's arrival records abroad are supplied. No document records which home either spouse nominated for the period they lived apart.

## Deliberately unavailable evidence

Only the supplied facts are available. A residency determination for P, any evidence of a life events test item, the dates of the period the spouses lived in different homes, any nomination or choice by the spouses, and a valuation splitting the sale price between the farmhouse with its chosen land and the rest of the block are missing. No current rule text, ATO view or adviser decision is supplied.

## Required checks

- Record each spouse's residency at the CGT event with its evidence, route P's residency to the residency workflow, and record that if P is a foreign resident who does not satisfy the life events test, s 118-110(3) denies P the exemption and s 118-185(3) denies a partial exemption, as does the ATO page for the first income use rule.
- List the life events test items and mark P's position `UNVERIFIED`; do not assume P's foreign residency or its length from the job alone.
- Record that the grazing land was used to produce income, so it is not covered even within 2 hectares, and that the private land covered is capped at 2 hectares less the land under the dwelling, chosen to include that land.
- Mark the valuation needed to apportion the gain between the farmhouse with its chosen land and the rest `UNVERIFIED`, and leave the apportionment blank.
- For the period the spouses lived apart, set out the s 118-170 choice: one dwelling for both, or different nominations under which a dwelling counts for the whole period where the nominating spouse's interest is not more than half and for half the period otherwise, applying it to P's 60 and Q's 40 part interests and Q's apartment without choosing.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not decide P's residency, assume a life events test item, or make or recommend a nomination or land choice.
- Do not treat the whole 6 hectare block or the grazing land as exempt, or compute an exempt amount without a valuation.
- Do not state a rule, area limit or period from memory, or lodge, declare or communicate anything.

## Source-verification and reviewer boundary

Use Subdivision 118-B of the *Income Tax Assessment Act 1997* and the ATO's main residence and foreign resident pages for the actual income year. Preserve unresolved review flags. The spouses make any nomination or choice and the reviewer decides the exemption. This is not tax, legal or financial advice or an assurance engagement.
