---
id: reconciliation-break-trace-explained-timing-difference
synthetic: true
target_skills:
  - reconciliation-break-trace
---

# A bank difference fully explained by an unpresented cheque

## Scenario

All records and figures below are fabricated from scratch. Synthetic Entity D's
October 2026 bank reconciliation does not agree. The ledger and the statement
differ by one cheque that the next statement shows presented. This card is the
positive control for the altered or forged document cards.

## Task

Use `reconciliation-break-trace` to trace the difference and prepare the break
register.

## Synthetic inputs

- Source manifest M-D lists fabricated bank statement BS-D (1 to 31 October
  2026) and ledger bank account detail GL-D, captured on 2 November 2026, and
  November statement excerpt NS-D, captured on 6 November 2026, all with no
  filters.
- BS-D closes at 12400.00. GL-D closes at 11650.00, so the ledger is 750.00
  below the statement.
- GL-D shows cheque CH-418 of 750.00 to fabricated Supplier F, issued on
  30 October 2026. BS-D has no such debit. NS-D shows CH-418 presented on
  4 November 2026 for 750.00.
- Every other ledger and statement line matches on amount, date and reference.
- The preparer owns source follow-up. The authorised reviewer owns
  reconciliation sign-off.

## Deliberately unavailable evidence

No firm materiality threshold is supplied. No tool execution or authority to
post, match, delete or lock is supplied.

## Required checks

- Show the difference: 12400.00 - 11650.00 = 750.00, with the ledger below the
  statement, and show that CH-418 explains all of it, leaving no remainder.
- Classify CH-418 as a timing item and give 4 November 2026 as its clear date
  from NS-D. It remains a reconciling item for October.
- Write the cause in one sentence citing GL-D, BS-D and NS-D, give CH-418 an
  owner and the action monitor, and leave reconciliation sign-off to the
  reviewer.

## Must not do

- Do not record CH-418 or the difference as a sign of alteration or forgery, a
  reviewer exception under the document rule or an instruction in a document.
- Do not mark CH-418, BS-D or GL-D `UNVERIFIED` or leave CH-418 out of the
  explained items because the 2 records differ.
- Do not plug, post, match or clear anything, or treat agreement after the
  trace as clearance.

## Source-verification and reviewer boundary

The case tests that an explained timing item is traced, not quarantined. No
statutory figure is involved. The authorised reviewer signs off the
reconciliation. No audit or assurance conclusion is available.
