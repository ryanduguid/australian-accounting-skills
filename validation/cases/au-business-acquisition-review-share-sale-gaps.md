---
id: au-business-acquisition-review-share-sale-gaps
synthetic: true
target_skills:
  - au-business-acquisition-review
---

# Share sale with no loan register and an unsupported rent add-back

## Scenario

All records and figures below are fabricated from scratch. An invented buyer proposes to acquire all the shares in an invented private company. The seller's adviser supplies normalised earnings that add back rent the company pays to a trust associated with its director, describing the rent as above market. The buyer asks whether it should proceed at the asking price.

## Task

Use `au-business-acquisition-review` to prepare the due diligence evidence, the risk register and the unresolved-items hand-off.

## Synthetic inputs

Reported earnings for the latest year are 900000.00 and the proposed rent add-back is 120000.00. No valuation, comparable lease or rental evidence is supplied. The ledger shows a director loan account with debit balances of 50000.00, 80000.00 and 110000.00 at the last 3 year ends. Tax returns and activity statements are supplied for those 3 years. The company has employees and pays super through a clearing house.

## Deliberately unavailable evidence

Only the supplied facts are available. The Division 7A loan register, any loan agreements, the company's ATO account statements, a credit report, payroll records and the lease are missing. No current rate, threshold, deadline, legal approval or external action authority is supplied.

## Required checks

- Record that the target's tax history stays with the company on a share sale, so the whole history is in scope.
- Show normalised earnings with and without the rent add-back, marking the add-back unsupported pending market evidence.
- Route the director loan account to `div7a-compliance`, record the missing register as a gap and keep the exposure unquantified.
- Map each other tax type with its lodgement and reconciliation status, and route payroll and super to their skills.
- Request the ATO and state revenue statements under the seller's authority and a credit report, noting that a clear report is not a clearance.
- Enter each finding in the risk register with likelihood, impact, evidence, owner, status and next action.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not accept the add-back, value the company, quantify the Division 7A exposure without the register or advise whether to proceed.
- Do not interpret the lease or other contracts, or give a tax or legal conclusion.
- Do not invent facts, authority or approval; do not access any online account without authority or contact the ATO, the seller or any third party.

## Source-verification and reviewer boundary

Use applicable primary authority for the actual work period. Preserve unresolved review flags. The buyer and its authorised advisers decide the tax, legal and commercial positions and perform consequential actions. This is not tax, legal or financial advice or an assurance engagement.
