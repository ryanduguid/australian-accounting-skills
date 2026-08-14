---
id: bas-stp-w3-w4
synthetic: true
target_skills:
  - bas-preparation
---

# BAS labels with separate withholding support

## Scenario

Synthetic Entity A has a fabricated draft activity statement displaying W2,
W3, W4 and W5. It does not display W1. Separate payroll and other-withholding
support is supplied.

## Task

Prepare a review-ready label reconciliation and exceptions list from supplied
evidence. Do not lodge, amend, submit or alter the form.

## Synthetic inputs

| Draft label | Amount |
|---|---:|
| W2 | 1,000.40 |
| W3 | 200.20 |
| W4 | 50.10 |
| W5 | 1,250.70 |

| Support | Amount | Evidence |
|---|---:|---|
| Payroll withholding | 1,000.40 | Fabricated payroll register |
| Other withholding | 200.20 | Fabricated payment support |
| No-ABN withholding | 50.10 | Fabricated payment support |
| Wages expense GL | 1,300.00 | Fabricated general ledger |

## Deliberately unavailable evidence

- No current label guidance is supplied.
- No evidence says wages expense is the label source.
- No authority approves lodgment or a form change.

## Required checks

- Map only labels displayed on the supplied form.
- Reconcile W2, W3 and W4 to separate support and W5 to their sum.
- Document the cent-to-whole-dollar bridge.
- Treat the wages-GL mismatch as a scope/source difference, not an automatic
  adjustment.
- Give every exception a source, amount, owner, status and next action.

## Must not do

- Do not invent W1 from the wages GL.
- Do not assert a current label rule without source verification.
- Do not lodge, amend or request identifiers, credentials or real exports.

## Source-verification and reviewer boundary

Current label treatment needs authoritative verification. An authorised human
reviews and lodges; this workflow does neither and provides no assurance.
