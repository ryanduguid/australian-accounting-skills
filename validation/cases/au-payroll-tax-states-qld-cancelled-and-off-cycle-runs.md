---
id: au-payroll-tax-states-qld-cancelled-and-off-cycle-runs
synthetic: true
target_skills:
  - au-payroll-tax-states
---

# A cancelled Queensland pay run, its rerun and an off-cycle run

## Scenario

Synthetic Entity C, an ungrouped employer registered in Queensland only and lodging monthly returns, supplies a fabricated payroll register for June and July 2027. All its employees work entirely in Queensland. All records and figures are invented for this case; the scenario adapts the cancelled-run and off-cycle-run ideas credited in NOTICE. A pay run dated 25 June 2027 was cancelled when the bank rejected the payment file and was rerun and paid on 1 July 2027. The client's draft counts the cancelled run in June and the rerun in July, and leaves out an off-cycle run because it is not on the pay calendar.

## Task

Use `au-payroll-tax-states` to prepare the June and July 2027 Queensland wage schedules, the effect on the 2026-27 annual reconciliation and an unresolved-items hand-off. This card tests Queensland's rules only.

## Synthetic inputs

- Scheduled run, transferred to employees' accounts on 11 June 2027: 82000.00.
- Off-cycle run, transferred on 18 June 2027: commission 6500.00 and 1500.00 of overtime underpaid for May 2027 work, 8000.00 in total.
- Scheduled run dated 25 June 2027: 84000.00. The bank's notice, also dated 25 June, rejects the whole payment file; no amount was transferred.
- Rerun of the 25 June run, transferred on 1 July 2027: 84000.00.
- Scheduled run, transferred on 9 July 2027: 83000.00.
- Client draft: June taxable wages 166000.00 (11 June and 25 June runs); July taxable wages 167000.00 (rerun and 9 July run).

## Deliberately unavailable evidence

The employment terms or award that set each pay day, and so when the 25 June run's wages and the May overtime became payable, are missing. No current rate, threshold, deduction or mental health levy figure is supplied. No external action is authorised.

## Required checks

- Tie the register by transfer date: June transfers 82000.00 + 8000.00 = 90000.00; July transfers 84000.00 + 83000.00 = 167000.00. Under s 9C(2) of the Payroll Tax Act 1971 (Qld), wages are taken to be paid on the day the amount was transferred or the account credited, so the cancelled 25 June run paid nothing on 25 June.
- Count the 84000.00 once. The Queensland Revenue Office's ruling PTA039.1 on s 9(7) says that when wages are paid in a different month from the month they are payable, liability arises in the earlier of the two months. Because the pay day is missing, show both outcomes without choosing one: June 174000.00 and July 83000.00 if the run was payable in June, or June 90000.00 and July 167000.00 if it was not. Keep the choice `UNVERIFIED`.
- Treat June 2027 as the last periodic return period of 2026-27. Section 20(2A) says s 20(1), the periodic liability, does not apply to that period, so June's wages are taxed through the annual liability in Division 4 (s 30), on the year's annual wages as s 29 defines them: the taxable wages paid or payable during the financial year. Show the effect on the 2026-27 annual reconciliation: its annual wages include 174000.00 for June if the run was payable in June, or 90000.00 if it was not, in which case the 84000.00 falls in July 2027 and the 2027-28 year.
- Include the off-cycle run in June. Commission is wages under the Act's dictionary, whatever the pay calendar says. Show the 1500.00 of May overtime separately, `UNVERIFIED` between May and June until the pay terms show when it became payable.
- Show the mental health levy (s 12A) separately from payroll tax, and leave both liabilities blank until each rate, threshold and deduction is read from the Queensland Revenue Office's current pages with their check dates.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not count the cancelled run and its rerun both, or treat the register's run date as the day a rejected payment was paid.
- Do not leave out the off-cycle run because it is off the pay calendar.
- Do not carry another State's rule into this Queensland card, invent pay days, rates, thresholds or deductions, request unnecessary identifiers, or submit, lodge, pay, sign, post, lock or communicate with third parties.

## Source-verification and reviewer boundary

Verify the Payroll Tax Act 1971 (Qld) in force for the period and the Queensland Revenue Office's current rulings and pages. If they are unavailable, retain the affected items as unverified. An authorised human decides the timing positions and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
