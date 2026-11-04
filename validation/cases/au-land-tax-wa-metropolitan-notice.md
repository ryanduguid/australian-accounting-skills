---
id: au-land-tax-wa-metropolitan-notice
synthetic: true
target_skills:
  - au-land-tax
---

# Perth investment land with a second tax line on the notice

## Scenario

All records below are fabricated from scratch. An invented individual owns a rental house in Perth alone and a second Perth lot jointly with a partner. Her Notice of Assessment arrived by email and shows land tax and a metropolitan region improvement tax line. She asks the firm to check it.

## Task

Use `au-land-tax` to prepare the Western Australian holdings review and the unresolved-items hand-off.

## Synthetic inputs

The Notice of Assessment for the individual and a screen capture of the land holdings in the land tax online services portal are supplied. Title searches for both lots are supplied. No notice for the jointly owned lot is supplied.

## Deliberately unavailable evidence

Only the supplied facts are available. The year's taxing date, thresholds and rates, the partner's other land and any exemption claim remain missing. No legal approval or external action authority is supplied.

## Required checks

- Route the land to RevenueWA, the Land Tax Assessment Act 2002 and the Land Tax Act 2002, and read the taxing date, rates and thresholds from RevenueWA for the assessment year.
- Record the owner of each lot at midnight on the taxing date from the title searches.
- Keep the sole and the joint ownership as separate assessments, and request the joint notice.
- Keep metropolitan region improvement tax on its own line of the reconciliation.
- Compare the notice with the portal's land holdings and record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not merge metropolitan region improvement tax into land tax, aggregate the sole and the joint lot or apply a foreign owner surcharge from another state.
- Do not object, pay or contact RevenueWA.

## Source-verification and reviewer boundary

Use RevenueWA's current land tax guidance and the Western Australian Acts for the assessment year. Preserve unresolved review flags. An authorised human decides the position and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
