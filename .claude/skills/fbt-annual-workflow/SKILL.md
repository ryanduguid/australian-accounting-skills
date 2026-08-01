---
name: fbt-annual-workflow
description: Use when preparing FBT year-end work for an Australian employer — identifying fringe benefits, collecting declarations, applying gross-up, calculating reportable fringe benefits amounts, and building the FBT return workpaper. FBT year runs 1 April to 31 March.
---

# FBT Annual Workflow

Work the FBT year (1 April – 31 March) from benefit identification through to a return-ready workpaper and RFBA figures for payroll.

## Inputs needed

1. GL detail for the FBT year — especially motor vehicle, entertainment, expense reimbursement, and employee-benefit-adjacent accounts
2. Motor vehicle details: make/model, cost base, availability days, odometer/logbooks where operating cost method is in play
3. Employee contribution records
4. Prior year FBT return and workpapers
5. Any existing declarations (living-away-from-home, expense payment, no-private-use)

## Workflow

1. **Identify benefit categories.** Sweep the GL for: cars (statutory formula vs operating cost — compare both where logbooks exist), expense payments, entertainment (meal vs recreation; income tax/GST interaction), loans to employees, housing/LAFHA, property/residual benefits. Map each finding to an account and an employee where attributable.
2. **Apply exemptions and reductions — verify each against current ATO guidance.** Minor and infrequent benefits, work-related portable devices, otherwise-deductible rule (declaration required), electric vehicle exemption conditions. Cite the ATO page and date checked for every exemption relied on.
3. **Collect what's missing.** Produce a per-employee list of required declarations and missing logbook/odometer data. Missing declaration = benefit stays taxable until the declaration exists.
4. **Compute.** Taxable value per benefit, less employee contributions. Apply Type 1 vs Type 2 gross-up by GST-creditability of the benefit, using the current year's gross-up factors and FBT rate from ato.gov.au — never from memory.
5. **Reconcile.** Employee contributions to the GL (they're usually income to the employer); FBT expense/payable accounts to the calculated liability; instalments already paid to the ATO account.
6. **RFBA.** Compute reportable fringe benefits amounts per employee against the current reporting threshold, ready for STP finalisation (see `stp-finalisation`).
7. **Assemble the workpaper.** Benefit register by category and employee, calculation schedules, exemption positions with citations, declaration checklist, return-item summary.

## Checks before handing over

- Every gross-up factor and the FBT rate carry an ATO citation with check date
- Car benefits: method choice documented per vehicle, days-available count shown
- Entertainment positions consistent across FBT, income tax deductibility, and GST claims
- RFBA schedule ties to the benefit register

## Boundaries

- Rates, thresholds, gross-up factors, and exemption conditions change — this skill never states them as fixed numbers.
- Method elections and contentious positions (LAFHA, EV conditions) go to the reviewer as flagged decisions, not silent choices.
- Not tax advice; return is lodged by the registered agent.
