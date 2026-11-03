---
id: au-payroll-tax-states-group-designated-employer
synthetic: true
target_skills:
  - au-payroll-tax-states
---

# Grouped employers in 2 states with a designated group employer

## Scenario

Synthetic Entity A, Synthetic Entity B and Synthetic Entity C supply fabricated records for the 2026-27 financial year. All records and figures are invented for this case. A signed reviewer note says the 3 entities form one payroll tax group with no exclusion order, and that Synthetic Entity A is the nominated designated group employer in New South Wales. The client's draft gives each entity a full threshold in each state where it pays wages.

## Task

Use `au-payroll-tax-states` to prepare the group's registration tests, threshold apportionment workings and an unresolved-items hand-off.

## Synthetic inputs

- Annual taxable wages for 2026-27, already tied to payroll and the ledger: Entity A 500000.00 in New South Wales; Entity B 100000.00 in New South Wales and 900000.00 in Victoria; Entity C 500000.00 in Victoria. No wages are paid in any other state or territory.
- Registrations: Entity A in New South Wales only.
- The signed grouping note described in the scenario.

## Deliberately unavailable evidence

Monthly wages by entity and state are not supplied. No Victorian designation, current threshold, deduction, phase-out or rate is supplied. No external action is authorised.

## Required checks

- Show group Australian wages of 500000.00 + 100000.00 + 900000.00 + 500000.00 = 2000000.00, with 600000.00 in New South Wales and 1400000.00 in Victoria, and use the group's Australian wages, not an entity's or a state's own wages, for each registration test and any phase-out.
- Show the New South Wales share of 600000.00 / 2000000.00 = 0.30 and apportion the threshold read from Revenue NSW's current page by it, as that page's grouping example does. Entity A alone claims the apportioned threshold; Entity B's New South Wales wages receive none.
- Record that Revenue NSW requires the designated group employer to pay wages above the monthly threshold on its own, and keep Entity A's eligibility `UNVERIFIED` until its monthly wages are supplied.
- Show the Victorian share of 1400000.00 / 2000000.00 = 0.70, read Victoria's deduction, phase-out and group designation rules from the State Revenue Office's current page, and keep the Victorian deduction claim `UNVERIFIED` because no Victorian designation is supplied.
- Flag registrations that look required but are missing, judged on group wages: Entity B in both states and Entity C in Victoria. Record whether Entity A must also register in Victoria, as the State Revenue Office's grouping page says each group member must even if it employs no staff. Registration and grouping remain reviewer decisions.
- Leave liability figures blank until each threshold, deduction and rate is read from its current page and recorded with the page and check date, and record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not give each entity or each state a full threshold, or apportion on an entity's own wages.
- Do not assume Victoria applies the New South Wales rule, or treat the New South Wales nomination as a Victorian designation.
- Do not invent monthly wages, thresholds, rates or approvals; do not request unnecessary identifiers or submit, lodge, pay, sign, post, lock or communicate with third parties.

## Source-verification and reviewer boundary

Verify applicable primary authority for the actual period. If it is unavailable, retain the affected item as unverified. An authorised human decides grouping, registration and the claim, and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
