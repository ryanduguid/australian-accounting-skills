---
id: payroll-tax-tas-workbook-defects
synthetic: true
target_skills:
  - au-payroll-tax-states
---

# Tasmanian payroll workbook defects remain visible

## Scenario

Synthetic Employer A supplies an invented workbook extract with a repeated heading, subtotal and unreadable amount. The scenario adapts the messy-workbook idea credited in NOTICE; no upstream rows or identifiers are copied.

## Task

Prepare a Tasmanian wages bridge and exception list.

## Synthetic inputs

| Source row | Description | Amount |
| --- | --- | --- |
| 1 | Heading repeated inside data | Amount |
| 2 | Salary, Tasmania | 4000.00 |
| 3 | Allowance, Tasmania | 300.00 |
| 4 | Subtotal of rows 2 and 3 | 4300.00 |
| 5 | Adjustment, Tasmania | unreadable |

- Ledger total supplied separately: 4400.00. No underlying adjustment document is supplied.

## Deliberately unavailable evidence

There is no corrected export or current Tasmanian wage-treatment, threshold or rate source.

## Required checks

- Retain source-row references. Exclude the repeated heading and subtotal from transaction summation with reasons, without losing their audit trail.
- Show supported transaction arithmetic of 4300.00 and an unresolved 100.00 difference to the ledger. Do not manufacture row 5's amount from that difference.
- Keep the unreadable adjustment visible as an exception and request the corrected source.
- Use Tasmania's own Act, grouping, registration and annual-adjustment-return routes, recording provisions, URLs and check dates before applying rules.
- Leave taxable wages and liability `UNVERIFIED` until the export and primary authority are available; list owner, status and next action.

## Must not do

- Do not count the subtotal twice, coerce unreadable text to zero, silently drop the adjustment or call the return reconciled.
- Do not invent current tax figures, lodge, register or contact third parties.

## Source-verification and reviewer boundary

This fabricated bridge is preparation only. An authorised human reviews source corrections and current authority and performs consequential actions. It gives no tax advice or assurance.
