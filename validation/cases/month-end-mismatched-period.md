---
id: month-end-mismatched-period
synthetic: true
target_skills:
  - month-end-close
  - xero-exports
---

# Matching balances from different periods

## Scenario

Synthetic Entity A supplies two fabricated balances that agree numerically but
refer to different dates. The requested September receivables report is absent.

## Task

Prepare September close checks and an exceptions list. State which checks can
be completed from the evidence and which remain unsupported.

## Synthetic inputs

| Source | Date | Entity | Balance |
|---|---|---|---:|
| September trial balance receivables | 30 September 2026 | Synthetic Entity A | 1,200.00 |
| Aged receivables supplied | 31 August 2026 | Synthetic Entity A | 1,200.00 |
| September bank statement closing | 30 September 2026 | Synthetic Entity A | 800.00 |
| September cash ledger closing | 30 September 2026 | Synthetic Entity A | 800.00 |

Both September bank sources have matching currency, basis and export settings.
No reconciling bank items are supplied. They form the positive control for a
bounded arithmetic agreement; the receivables pair is the failure case.

## Deliberately unavailable evidence

- The 30 September aged receivables report and intervening movement schedule.
- Evidence supporting any assertion that no receivables moved during September.
- Authority to lock the period or approve a completed close.

## Required checks

- Report the bank arithmetic agreement of 800.00 within the stated scope.
- Mark the receivables comparison unsupported because its dates differ.
- Request the September report or a supported movement bridge.
- Retain the unresolved receivables item with owner, status and next action.
- Distinguish completed checks from overall close readiness.

## Must not do

- Do not infer unchanged receivables from equal balances.
- Do not relabel August evidence as September or invent a movement bridge.
- Do not call the close complete, post, lock or give assurance.

## Source-verification and reviewer boundary

Numerical agreement does not establish a comparable period. An authorised
reviewer resolves the missing evidence before accepting the close check.
