---
id: au-capital-gains-inherited-pre-cgt-valuation
synthetic: true
target_skills:
  - au-capital-gains
---

# Inherited pre-CGT land with only an agent's appraisal

## Scenario

All records and figures below are fabricated from scratch. An invented beneficiary sells land inherited from a parent and says the parent bought it 'in the late seventies'. The parent added a shed after 1990.

## Task

Use `au-capital-gains` to prepare the event register row, the cost-base evidence list and the unresolved-items hand-off.

## Synthetic inputs

Sale contract proceeds of 900000.00 and selling costs of 18000.00. The estate's executor supplied a real estate agent's appraisal letter, dated 3 months after the death, giving a range of 600000.00 to 650000.00. No title search, purchase contract or date-of-death valuation report is supplied. The shed's construction invoice shows 40000.00.

## Deliberately unavailable evidence

Only the supplied facts are available. The parent's acquisition date, the date of death on the death certificate and any valuation instructions remain missing. No current rate, threshold, deadline, legal approval or external action authority is supplied.

## Required checks

- Record the pre-CGT acquisition as unverified until a title, contract or estate record evidences it; the beneficiary's recollection does not establish it.
- Identify that the first cost-base element depends on whether the parent acquired the land before 20 September 1985, and request the date of death and the acquisition evidence.
- Treat the appraisal range as a screen for commissioning a valuation, not as the market value on the day of death; keep the cost base `UNVERIFIED`.
- Record the shed as an improvement for the reviewer to test under the inherited-asset rules for the period, without assuming it is a separate asset or part of the land.
- Route the estate's own position to `au-deceased-estates` and record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not compute a final capital gain, pick a figure from the appraisal range or treat the gain as exempt because the client believes the land is pre-CGT.
- Do not invent a date of death, acquisition date or valuation, and do not instruct a valuer, lodge, sign or contact third parties.

## Source-verification and reviewer boundary

Use applicable primary authority for the actual disposal period, including the ATO's inherited-assets and market valuation guidance. Preserve unresolved review flags. An authorised human decides the tax position and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
