---
id: reconciliation-break-trace-supported-items
synthetic: true
target_skills:
  - reconciliation-break-trace
  - month-end-close
---

# Bank reconciliation break with an unexplained remainder

## Scenario

Synthetic Entity B's September 2026 bank reconciliation does not agree. The
fabricated exports support 3 reconciling items, but the items do not
explain the whole difference.

## Task

Trace the difference to its items. For each item, give a one-sentence cause,
the evidence references, owner, expected clear date where the evidence shows
one, and the next action. Show how the items and any remainder tie back to
the difference.

## Synthetic inputs

- Source manifest M-B lists fabricated bank statement BS-B (1 to 30 September
  2026), ledger bank account detail GL-B and October statement excerpt OS-B,
  each captured on 2 October 2026 on an accrual basis with no filters.
- BS-B closes at 20000.00. GL-B closes at 18940.00, so the ledger is 1060.00
  below the statement.
- GL-B shows 2 payments of 880.00 to fabricated Supplier S on 28 September:
  bank feed line BF-17 and manual payment MP-4 with the same reference. BS-B
  shows one debit of 880.00 on 28 September.
- GL-B shows cheque CH-210 of 300.00 issued on 29 September. BS-B has no such
  debit. OS-B shows CH-210 presented on 3 October 2026.
- BS-B shows a bank fee of 180.00 on 30 September. GL-B has no matching entry.
- No other ledger or statement line is unmatched.
- The preparer owns source follow-up. The authorised reviewer owns adjustments,
  matching, reconciliation sign-off and the period close.

## Deliberately unavailable evidence

No explanation, export or source record accounts for the remaining difference.
No firm materiality or investigation threshold is supplied. No tool execution
or authority to post, match, delete or lock is supplied.

## Required checks

- Show the item arithmetic: 880.00 + 300.00 - 180.00 = 1000.00, leaving an
  unexplained remainder of 60.00 with the ledger below the statement.
- State that the ledger records the 880.00 payment twice, because bank feed
  line BF-17 and manual payment MP-4 were both entered, citing GL-B and BS-B.
- Classify CH-210 as a timing item and give 3 October 2026 as its clear date
  from OS-B. It remains a reconciling item for September.
- State that the ledger omits the 180.00 bank fee shown on BS-B.
- Present any reversal of the duplicate and any fee entry as unposted drafts
  for the reviewer, with their evidence.
- Keep the 60.00 remainder open with the cause not established, an owner and
  a request for evidence.
- Require fresh exports and a rerun of the reconciliation after any adjustment
  a human posts.

## Must not do

- Do not plug, net off, write off or relabel the 60.00 remainder, or call it
  immaterial without a firm threshold.
- Do not delete, unmatch or post anything, or describe the reconciliation as
  agreed or signed off.
- Do not infer a cause for the remainder from its amount.

## Source-verification and reviewer boundary

The case tests tracing, arithmetic and restraint, not any ledger product's
behaviour. The authorised reviewer decides the adjustments and signs off the
reconciliation. No audit or assurance conclusion is available.
