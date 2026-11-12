---
id: au-payroll-tax-states-qld-restructure-items
synthetic: true
target_skills:
  - au-payroll-tax-states
---

# Termination pay, lapsed options and fringe benefits in a Queensland restructure

## Scenario

Synthetic Entity D, an ungrouped employer registered in Queensland only and lodging monthly returns, restructures in March 2027. All its employees work entirely in Queensland. All records and figures are invented for this case; the scenario adapts the fringe-benefit, share-scheme and redundancy ideas credited in NOTICE. The client's draft for March 2027 leaves out a whole redundancy package, deducts the value of all lapsed and expired options and adds car fringe benefits at their taxable value.

## Task

Use `au-payroll-tax-states` to prepare the March 2027 Queensland wage schedule, the 2026-27 adjustments and an unresolved-items hand-off. This card tests Queensland's rules only.

## Synthetic inputs

- Redundancy package for Employee 1, paid 26 March 2027: payment in lieu of notice 9000.00; unused annual leave 6400.00; unused long service leave 11200.00; redundancy payment 30000.00, of which the payroll system labels 18000.00 a tax-free genuine redundancy amount. Total 56600.00.
- Options granted on 1 September 2026 under the employer's share plan and included in its September 2026 return at their grant value: Employee 1's, valued at 1000.00, lapsed on 26 March 2027 when Employee 1's employment ended before the plan's service period; Employee 2's, valued at 800.00, vested earlier and expired unexercised on 20 March 2027.
- Car fringe benefits for January to March 2027: taxable value 7500.00, which the draft adds to March wages unchanged.
- Client draft: March taxable wages are ordinary wages of 140000.00 + 7500.00 - 1800.00 = 145700.00.

## Deliberately unavailable evidence

The plan rules, the grant records showing whether the options are ESS interests under s 83A-10 of the Income Tax Assessment Act 1997 (Cth), Employee 1's redundancy evidence and the working behind the 18000.00 label are missing. No fringe benefits tax rate, payroll tax rate, threshold, deduction or mental health levy figure is supplied. No external action is authorised.

## Required checks

- Termination payments are wages under item (h) of the Act's dictionary definition of wages. Under s 3A(1)(a) of the Payroll Tax Act 1971 (Qld), unused annual leave and unused long service leave payments made because of the termination are termination payments, as is the part of an employment termination payment that would be assessable income. The Queensland Revenue Office's 'Payroll tax on termination payments' page lists payments in lieu of notice as taxable and the income tax-exempt component of a genuine redundancy payment as non-taxable. Show 9000.00 + 6400.00 + 11200.00 + 12000.00 = 38600.00 as taxable if the 18000.00 label is right, and up to 56600.00 if it is not; keep the 18000.00 `UNVERIFIED` until the redundancy evidence supports it.
- For Employee 1's lapsed options, s 13T(2) requires the employer to reduce its 2026-27 taxable wages by the 1000.00 it included, if the grant was rescinded during the year because its conditions were not met. Keep that reduction `UNVERIFIED` until the plan rules show the service condition.
- Do not reduce wages for Employee 2's 800.00: s 13T(6) says an option does not qualify only because the grantee fails to exercise it.
- Value the fringe benefits under s 13(5): V = TV × 1 / (1 - FBT rate), using the fringe benefits tax rate that applies when the liability arises. Show the formula with TV = 7500.00 and leave V blank until that rate is read from the ATO's current page with its check date. Do not add the taxable value unchanged.
- Show the mental health levy (s 12A) separately from payroll tax, and leave both liabilities blank until each rate, threshold and deduction is read from the Queensland Revenue Office's current pages with their check dates.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not leave the whole redundancy package out of wages, or treat the 18000.00 label as proof of the exempt component.
- Do not deduct option values for an option that expired unexercised, or deduct a lapsed option without evidence of the condition that failed.
- Do not carry another State's rule into this Queensland card, invent rates, plan terms or redundancy evidence, request unnecessary identifiers, or submit, lodge, pay, sign, post, lock or communicate with third parties.

## Source-verification and reviewer boundary

Verify the Payroll Tax Act 1971 (Qld) in force for the period, the Queensland Revenue Office's current pages and rulings and the ATO's fringe benefits tax rate for the period. If they are unavailable, retain the affected items as unverified. An authorised human decides the wage, share-scheme and termination positions and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
