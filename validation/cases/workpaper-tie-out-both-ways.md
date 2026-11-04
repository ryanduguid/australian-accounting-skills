---
id: workpaper-tie-out-both-ways
synthetic: true
target_skills:
  - workpaper-tie-out
---

# A pack that agrees top-down but not from the source up

## Scenario

All records and figures below are fabricated from scratch. Synthetic Entity
E has a draft statement pack in which every statement line agrees to a
workpaper and every workpaper total agrees to the trial balance. The
preparer's covering memo says the pack has no exceptions.

## Task

Use `workpaper-tie-out` to build the tie-out matrix in both directions,
recompute the memo's figures and prepare the exceptions list.

## Synthetic inputs

| Source | Version | Item | Amount |
|---|---|---|---:|
| Trial balance | TB-E | Trade debtors | 260.00 |
| Trial balance | TB-E | Accrued expenses | 35.00 |
| Trial balance | TB-E | Trade debtors, prior year | 320.00 |
| Workpaper | WP-E1 | Trade debtors, linked to TB-E | 260.00 |
| Statement draft | Draft-E | Trade debtors, references WP-E1 | 260.00 |
| Covering memo | Memo-E | 'Trade debtors fell by 50.00 on last year. No exceptions.' | 50.00 |
| Review note | RN-E2 | Open: support for a debtor write-off not yet received | No amount |

No workpaper or statement line uses the trial balance's accrued expenses
of 35.00. Draft-E shows no accrued expenses line.

## Deliberately unavailable evidence

- A workpaper or mapping for accrued expenses, or evidence that it belongs
  in another line.
- Support for the write-off in RN-E2, or any record closing it.
- Approval of the memo or of the statements.

## Required checks

- Agree Draft-E to WP-E1 and WP-E1 to TB-E at 260.00 as the positive control.
- Trace TB-E forward and list accrued expenses of 35.00 as a source total
  that reaches no workpaper or statement line.
- Recompute the memo's movement from 320.00 to 260.00 as a fall of 60.00 and
  list the stated 50.00 as an exception of 10.00.
- Test the memo's 'no exceptions' statement against open RN-E2 and the
  exceptions above, and record it as unsupported.
- Give each exception an owner, status and next action.

## Must not do

- Do not treat top-down agreement as proof that the pack is complete.
- Do not edit the memo, close RN-E2, map accrued expenses to a line or post
  an adjustment.
- Do not call the pack clean, signed off or audited.

## Source-verification and reviewer boundary

Verify only against the sources supplied. An authorised reviewer resolves
the exceptions and signs off. Correct arithmetic does not establish
professional review, and this is not an audit or assurance conclusion.
