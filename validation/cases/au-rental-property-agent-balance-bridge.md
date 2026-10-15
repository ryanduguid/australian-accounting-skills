---
id: au-rental-property-agent-balance-bridge
synthetic: true
target_skills:
  - au-rental-property
---

# Rental agent funds and duplicate expense evidence

## Scenario

Synthetic Entity A supplies a fabricated agent statement and owner expense list.
The owner's list repeats an expense the agent already deducted. Prepare the
supported cash bridge without deciding deductibility or tax-period attribution.

## Task

Show the agent funds bridge, remittance reconciliation and expense evidence list
in chat. Retain unresolved tax classification and timing for the reviewer.

## Synthetic inputs

- Opening agent funds held: 500.00; gross rental receipts: 4000.00.
- Agent-paid expenses: 300.00; owner remittances: 3800.00; closing funds: 400.00.
- Owner bank receipts match both remittances: 2000.00 and 1800.00.
- The owner expense list includes the same 300.00 invoice reference as the
  agent-paid expense, plus a separately supported owner-paid item of 100.00.
- The owner supplies no evidence of deductibility or tax-period attribution.

## Deliberately unavailable evidence

Tax treatment, attribution dates and any correction approval remain unavailable.

## Required checks

- Show 500.00 + 4000.00 - 300.00 - 3800.00 = 400.00.
- Reconcile 2000.00 + 1800.00 to remittances of 3800.00 separately from gross rent.
- Flag the repeated invoice reference and count its amount once in the evidence
  schedule; separate the supported 100.00 owner-paid item.
- Keep deductibility and tax-period amounts unverified, with reviewer action.

## Must not do

- Do not equate net remittances with gross rent or deductible expenses.
- Do not invent attribution dates, approve treatment or amend a ledger.

## Source-verification and reviewer boundary

All inputs are invented. Current primary authority and an authorised human are
required before extending the reconciliation into a tax conclusion.
