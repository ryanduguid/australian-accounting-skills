---
id: payroll-tax-sa-group-registration
synthetic: true
target_skills:
  - au-payroll-tax-states
---

# South Australian group registration evidence

## Scenario

Synthetic Entities A and B are grouped according to a supplied authorised reviewer note. Their fabricated records show only Entity A registered in South Australia. A draft assumes one registration covers both.

## Task

Prepare registration and group-deduction questions for review without registering anyone.

## Synthetic inputs

- Annual payroll source totals: A pays 600000.00 in South Australia; B pays 300000.00 there and 400000.00 in Victoria.
- No monthly wages, designated group employer record or exclusion order is supplied.

## Deliberately unavailable evidence

Current registration and group-deduction rules are absent. The earlier automated source collection could not retrieve the South Australian Act text; a revenue-office summary is not a substitute for an unread provision.

## Required checks

- Show Australian group wages of 1300000.00 and source-labelled SA wages of 900000.00, subject to the supplied wage-treatment basis being verified.
- Use RevenueSA's grouping, registration and reconciliation guidance and seek the operative SA Act for the period.
- Test who must register and who may claim a deduction under SA rules. Do not infer these from Victoria or the fact that A is already registered.
- Keep registration, deduction and liability `UNVERIFIED` whilst monthly wages, designation and authority are missing, with dependent calculations blank.
- Record missing evidence, source limits, owner, status and next action for an authorised human.

## Must not do

- Do not give both entities a full threshold, treat A's registration as B's registration or cite an unread SA provision as verified.
- Do not register, lodge, contact RevenueSA or invent thresholds and rates.

## Source-verification and reviewer boundary

The fabricated totals support preparation only. An authorised human verifies current authority, decides the position and performs consequential actions. No tax advice or assurance is given.
