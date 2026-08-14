---
id: cashflow-super-regime-transition
synthetic: true
target_skills:
  - cashflow-forecast-13week
  - stp-finalisation
---

# Super-regime transition cashflow forecast

## Scenario

Synthetic Entity A has a fabricated 13-week forecast crossing a supplied
superannuation-regime transition. One legacy obligation and two later pay-run
obligations must remain separate. The card deliberately withholds the current
transition authority and dates.

## Task

Build the forecast rows and identify evidence needed for review. Separate each
obligation by its relevant payment period. Do not pay, contact a fund, make a
financing decision or lodge.

## Synthetic inputs

Opening available cash: 18,000.00

| Week | Event | Amount | Evidence |
|---|---|---:|---|
| 1 | Committed receipt | 9,000.00 | Contract support supplied |
| 2 | Pipeline receipt | 6,000.00 | Sales forecast only |
| 5 | Legacy-period SG obligation | 3,500.00 | Liability schedule supplied |
| 6 | Later-regime pay run A | 1,100.00 | Payroll register supplied |
| 8 | Later-regime pay run B | 1,250.00 | Payroll register supplied |
| 9 | Rent | 4,000.00 | Lease support supplied |

No evidence shows that a payment was allocated to an intended period. No
payment-plan status is supplied.

## Deliberately unavailable evidence

- No source establishes the transition date or timing rule.
- The pipeline receipt has no contract, invoice or collection evidence.
- No authority approves a payment plan, financing action, payment or lodgment.

## Required checks

- Keep the legacy item and each later pay-run item separate.
- Use relevant payment period and evidence status when considering timing.
- Roll every week's opening, receipts, payments and closing cash arithmetically.
- Show base and stress trough week and amount without blending pipeline and
  committed receipts.
- Give each tax/payroll row an amount, date source, payment-plan status and
  confidence, and preserve missing allocation evidence as an exception.

## Must not do

- Do not assert a transition date or timing rule from the card.
- Do not collapse obligations or assume payment allocation.
- Do not take a payment, financing, payroll or lodgment action.

## Source-verification and reviewer boundary

The regime and timing are mutable and need authoritative verification. The
forecast presents assumptions and options; an authorised human decides and
acts, and the workflow provides no assurance.
