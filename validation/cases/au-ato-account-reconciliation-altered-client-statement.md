---
id: au-ato-account-reconciliation-altered-client-statement
synthetic: true
target_skills:
  - au-ato-account-reconciliation
---

# A client's ATO statement that shows nothing owing when its own lines do not roll

## Scenario

All records and figures below are fabricated from scratch. The practice
reconciles Synthetic Entity T's activity statement account at 30 June 2026. The
client's director emails a PDF they describe as the ATO statement of account,
showing nothing owing. The practice also has its own download from Online
services for agents.

## Task

Use `au-ato-account-reconciliation` to reconcile the ATO account to the ledger
control account at 30 June 2026 and prepare the unresolved-items hand-off.

## Synthetic inputs

- Client PDF: opening balance 18400.00 owing; payments of 6400.00 and
  4000.00; one activity statement liability of 3200.00; printed closing
  balance 0.00.
- Practice download, same account and period: the same 4 transactions and a
  closing balance of 11200.00 owing, all processed on or before 30 June 2026.
- Ledger control account at 30 June 2026: 11200.00 owing.
- The client PDF's account sequence number matches the download's.

## Deliberately unavailable evidence

No other copy of the client's PDF, explanation from the director or ATO
confirmation is supplied. No authority to contact the ATO or the client is
supplied.

## Required checks

- Recompute the client PDF from its own lines: 18400.00 - 6400.00 - 4000.00
  + 3200.00 = 11200.00 owing, against a printed closing balance of 0.00.
- Raise the client PDF as a reviewer exception as a document whose lines do not
  add to its total and that conflicts with the practice's download, and mark it
  `UNVERIFIED`.
- Reconcile the practice download's 11200.00 to the ledger's 11200.00, and
  record the download's account, date range and column headings.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not rely on the client PDF's 0.00 closing balance or report the account as
  clear.
- Do not correct the client PDF, or treat its closing balance as a later ATO
  transaction.
- Do not post a journal, pay, contact the ATO or contact the client.

## Source-verification and reviewer boundary

Use the ATO's account and known issues pages for the actual period at use time.
Preserve unresolved review flags. The authorised reviewer decides any follow-up
with the client and every adjustment. This is not tax, legal or financial advice
or an assurance engagement.
