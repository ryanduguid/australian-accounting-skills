---
id: stp-current-vs-overdue-sg
synthetic: true
target_skills:
  - month-end-close
  - stp-finalisation
---

# SG ageing, liability roll-forward and STP mismatch

## Scenario

Synthetic Entity A has two fabricated SG balances with different evidence
status: one current pay-run liability and one earlier-period balance. A
worker-level mismatch also exists between two reports.

## Task

Prepare SG ageing, separate PAYG/SG liability roll-forwards and an exceptions
list. Do not declare, pay, correct or lodge.

## Synthetic inputs

| Liability | Amount | Period status supplied by fixture | Receipt evidence |
|---|---:|---|---|
| Current item | 600.00 | Applicable due date has not passed | Not yet expected |
| Legacy item | 900.00 | Applicable due date has passed | Not supplied |

A fabricated bank reference exists for the legacy item but does not prove fund
or clearing-house receipt.

| Liability | Opening | Current-period amount | Payments/reversals | Closing GL |
|---|---:|---:|---:|---:|
| PAYG withholding | 200.00 | 1,000.00 | 900.00 | 300.00 |
| SG payable | 100.00 | 500.00 | 300.00 | 300.00 |

Synthetic Worker A differs between the payroll register and STP report.

## Deliberately unavailable evidence

- No current legal due-date rule is embedded in the card.
- No receipt or allocation evidence exists for the legacy item.
- No evidence resolves the worker-level mismatch.
- No declaration or lodgment authority is supplied.

## Required checks

- Age each SG balance using its relevant payment period and supported due-date
  status, not GL posting date alone.
- Keep the current item open/monitored rather than automatically overdue.
- Flag the legacy item because its supplied due-date status has passed and
  receipt evidence is missing.
- Produce separate PAYG and SG roll-forwards agreeing to closing balances.
- Give the worker mismatch evidence, owner, status and next action.

## Must not do

- Do not compare annual expenses directly with a closing payable.
- Do not call a current item overdue solely because it remains open.
- Do not make a declaration, correction, payment, journal or lodgment.

## Source-verification and reviewer boundary

Current SG timing needs authoritative verification. An authorised reviewer
decides unresolved treatment and acts; the workflow supplies no assurance.
