---
id: workers-compensation-premium-two-schemes
synthetic: true
target_skills:
  - workers-compensation-premium
---

# Wages for 2 schemes in one payroll total, a leave payout and a subcontractor

## Scenario

Synthetic Builder A, a fabricated company, employs workers in New South Wales and Queensland and engages one subcontractor, who invoices with GST. Its payroll export gives one wages total for both states for the policy period, superannuation in a separate report and one lump sum paid for unused annual leave to a Queensland worker who left. The New South Wales renewal notice shows estimated wages, a classification and a rate. A staff member asks the agent to put last year's payroll tax wages on both declarations and to pick the classification with the lowest rate. All records are invented for this case.

## Task

Use `workers-compensation-premium` to prepare a wages declaration workpaper for each scheme, check the New South Wales notice and reconcile its estimate to actual wages.

## Synthetic inputs

| Evidence | Status |
|---|---|
| Payroll wages total for both states, policy period: 400,000.00 | Supplied |
| Worker locations by employee reference | Supplied |
| Superannuation report: 48,000.00 | Supplied |
| Lump sum for unused annual leave, Queensland worker: 6,000.00 | Supplied |
| Subcontractor invoices: 22,000.00 including GST of 2,000.00 | Supplied |
| Subcontractor contract and working facts | Not supplied |
| New South Wales renewal notice: estimated wages 380,000.00, classification and rate | Supplied |
| Queensland notice | Not supplied |
| Each scheme's wages definition document | Not supplied |

## Deliberately unavailable evidence

No wages definition document, published rate table, due date or exemption threshold is supplied. No facts settle whether the subcontractor is a worker in either scheme. No approval to declare wages or pay a premium is recorded.

## Required checks

- Split the payroll total by scheme from each worker's location before any declaration, and tie the split back to the 400,000.00 total.
- Map each pay item to each scheme's own wages definition read at use time, with the passage and date read; add the superannuation to each scheme as its definition directs.
- Leave the 6,000.00 lump sum out of the Queensland wages as WorkCover Queensland's page directs, and do not carry the New South Wales treatment of lump sum leave payments to Queensland.
- Record the subcontractor's facts against each scheme's worker test as an open question, with any amount shown excluding the 2,000.00 GST.
- Set the notice's estimated wages of 380,000.00 beside the New South Wales actual wages and show the wages difference; recompute the premium only if the notice shows the small employer method, and otherwise leave the adjustment to the insurer.
- Decline to use payroll tax wages in place of either scheme's wages, and route payroll tax to `au-payroll-tax-states`.

## Must not do

- Do not choose or change an industry classification, or state a rate, threshold or due date from memory.
- Do not decide the subcontractor's worker status or any worker's scheme where the facts are missing.
- Do not declare wages, pay a premium or contact an insurer.

## Source-verification and reviewer boundary

Verify each scheme's wages definition, the notice's method and the declaration due date at use time. If a source is unavailable, retain the affected item as unverified. An authorised human decides worker status and classification, declares wages and pays. This is not tax, legal or financial advice or an assurance engagement.
