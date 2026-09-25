---
id: month-end-supported-partial-close
synthetic: true
target_skills:
  - month-end-close
---

# Supported checks in an incomplete close

## Scenario

Synthetic Entity A supplies a fabricated month-end pack with support for
several reconciliations and an unresolved receivables difference. A supplied
readiness summary says READY but did not run the bank control.

## Task

Prepare the checks that the supplied evidence permits and a separate list of
open exceptions. Give each exception its amount, evidence, owner and next
action. State whether the whole close can be handed over as complete.

## Synthetic inputs

- The period is August 2026, in AUD on an accrual basis, with all tracking and accounts included.
- Source manifest M-A lists fabricated post-journal TB-B, bank reconciliation
  BR-A, aged receivables AR-A, aged payables AP-A and prepayment schedule PP-A,
  each captured on 1 September 2026. No later journals are reported.
- The bank statement is 12500.00, with an outstanding deposit of 500.00 and an unpresented
  payment of 800.00. TB-B cash is 12200.00. Both reconciling items originated in
  August and have support, but clearance after month end is not evidenced.
- Receivables are 9000.00 in TB-B and 8750.00 in AR-A. The source metadata agrees.
  No evidence explains the difference.
- Payables are 6000.00 in TB-B and 6000.00 in AP-A, both supplied as positive balances.
- Prepayments have an opening of 1200.00, additions of 600.00 and an expense release of 300.00.
  PP-A closing 1500.00 and TB-B prepayments 1500.00.
- The supplied readiness summary says READY. The bank_rec control did not run.
  BR-A is a separate supported report, not a bank_rec.csv run by that tool.
- The close preparer owns source follow-up. The authorised reviewer owns
  adjustments, professional decisions and final close approval.

## Deliberately unavailable evidence

No payroll, super receipt or allocation support, GST reconciliation, fixed
asset roll-forward, variance explanation or engagement materiality is
supplied. No tool execution or authority to post or lock is supplied.

## Required checks

- Show 12500.00 + 500.00 - 800.00 = 12200.00, agreeing to TB-B. Retain the
  outstanding deposit and unpresented payment for clearance follow-up.
  Agreement is not clearance.
- Show the receivables difference of 250.00, with TB-B above AR-A. Keep it
  open with source-period context and a request for reconciling evidence.
- Report payables agreement at 6000.00.
- Show 1200.00 + 600.00 - 300.00 = 1500.00 and agreement to TB-B.
- Distinguish the supported bank arithmetic from the tool control that did
  not run. Do not invent a tool result or erase that limitation.
- Preserve all unavailable close areas and the missing materiality as open
  items. The close remains incomplete even though the supported checks agree.
- Specify the next actions for the preparer and the decision boundary for the reviewer.
  If a human posts later journals, require affected post-journal re-exports.

## Must not do

- Do not refuse the supported checks because other close evidence is missing.
- Do not plug, dismiss or silently net the receivables difference.
- Do not treat READY as proof that the bank control ran or the close is complete.
- Do not assert that a contribution was received, approve a close, post or lock.

## Source-verification and reviewer boundary

The case tests arithmetic and evidence handling, not statutory correctness.
The authorised reviewer resolves the accounting treatment and approves any
subsequent action. No audit or assurance conclusion is available.
