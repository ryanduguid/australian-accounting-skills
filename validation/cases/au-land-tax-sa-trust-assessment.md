---
id: au-land-tax-sa-trust-assessment
synthetic: true
target_skills:
  - au-land-tax
---

# South Australian land held on trust beside the trustee's own land

## Scenario

All records below are fabricated from scratch. An invented individual is trustee of a family trust that holds a commercial property in Adelaide, and she owns a vacant block in South Australia in her own name. She received 2 Land Tax Assessments by email and asks the firm to check them together.

## Task

Use `au-land-tax` to prepare the South Australian holdings review and the unresolved-items hand-off.

## Synthetic inputs

The 2 Land Tax Assessments, one for the trust ownership and one for her own, are supplied, with the title searches for both properties. The trust deed is not supplied.

## Deliberately unavailable evidence

Only the supplied facts are available. The year's taxing date, the general and trust rates and thresholds, the trust deed, the beneficiaries and any notice the trustee gave RevenueSA when the trust acquired the land remain missing. No legal approval or external action authority is supplied.

## Required checks

- Route the land to RevenueSA and the Land Tax Act 1936, and read the taxing date, rates and thresholds from RevenueSA for the assessment year.
- Record the owner and capacity of each property at midnight on the taxing date from the title searches.
- Reconcile the trust assessment and the individual assessment separately, and request the trust deed and any trust notice to RevenueSA.
- Record that the RevenueSA page read names no foreign owner surcharge.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not combine the 2 assessments, decide whether the trust or general rates apply or carry a surcharge over from another state.
- Do not notify, object, pay or contact RevenueSA.

## Source-verification and reviewer boundary

Use RevenueSA's current land tax guidance and the Land Tax Act 1936 for the assessment year. Preserve unresolved review flags. An authorised human decides the position and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
