---
id: payroll-tax-qld-mid-month-transfer
synthetic: true
target_skills:
  - au-payroll-tax-states
---

# Queensland mid-month transfer with a wide payroll extract

## Scenario

Synthetic Employer A supplies an invented monthly pivot for a worker who transferred from Queensland to New South Wales. The month-end master record shows only New South Wales. The scenario adapts the mid-month transfer and wide-pivot ideas credited in NOTICE; the data below is newly fabricated.

## Task

Prepare traceable monthly state-wage workings and a source/evidence handoff for Synthetic Employer A. Separately, screen Synthetic Employer B's Queensland registration position without registering or lodging anything.

## Synthetic inputs

- Pivot rows for the same worker and month: Queensland salary 3000.00 and allowance 200.00; New South Wales salary 2800.00 and allowance 100.00.
- Ledger total: 6100.00. Transfer date and detailed service-location records are missing.
- Separate decision variant: Synthetic Employer B is an unregistered Queensland group member with taxable wages already payable for Queensland services but no wages paid yet. Its and its group's wages are below every relevant wage threshold.

## Deliberately unavailable evidence

No current nexus provisions, taxable-wage decisions, thresholds or rates are supplied.

## Required checks

- Show Queensland source-labelled payments of 3200.00 and NSW source-labelled payments of 2900.00, reconciling to 6100.00. These are source totals, not verified taxable wages.
- Preserve both rows and the wage-code breakdown. Request the transfer date and monthly service evidence; do not allocate the entire month using the closing master record.
- Read each jurisdiction's own Act and revenue-office guidance for monthly nexus and wage treatment. Keep the legal allocation and dependent calculations `UNVERIFIED` until supported.
- Use Queensland's own grouping, registration and annual-return routes if those questions arise, recording URLs, provisions and check dates.
- For Synthetic Employer B, read ss 9, 52(b) and 53(1) of the Queensland Act and carry the registration lead independently of wage thresholds; do not screen it out because payment has not occurred. If the payable-wage evidence is missing, keep that lead unresolved and ask for it.
- List evidence needed, owner, status and next action.

## Must not do

- Do not duplicate or drop a state row, substitute home state for service evidence or infer legal allocation from the supplied amounts alone.
- Do not invent tax figures, register, lodge or communicate with third parties.

## Source-verification and reviewer boundary

Current primary authority and an authorised human decide the allocation and liability. This invented case is preparation only, without tax advice or assurance.
