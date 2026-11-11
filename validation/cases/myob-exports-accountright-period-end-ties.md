---
id: myob-exports-accountright-period-end-ties
synthetic: true
target_skills:
  - myob-exports
---

# AccountRight period-end exports with an aged listing, a wrong GST basis and an unconfirmed user role

## Scenario

All records below are fabricated from scratch. Synthetic Entity B keeps its ledger in the AccountRight desktop app, accounts on the accrual basis and reports GST on the accrual basis. Its bookkeeper exported 4 reports for the 30 June of year Y1 period end, 9 weeks after that date, and asks for them to be checked before the year-end file starts.

## Task

Use `myob-exports` to check the exports, record the manifest and list what must be re-exported or confirmed.

## Synthetic inputs

- `Trial Balance`, CSV: total debits and total credits are both 61250.00. The export shows the month and the year to date but does not show which month or financial year was selected.
- `Aged Payables [Summary]`, CSV, aged as at 30 June Y1: total 9480.00. One supplier row of 750.00 relates to a bill dated 3 July Y1. The trial balance shows the payables linked account at 8730.00.
- `GST [Summary - Cash/Payments]`, CSV, for April to June Y1.
- `General Ledger [Detail]`, TSV, for the year to 30 June Y1, run by a junior bookkeeper whose user role nobody has confirmed.

## Deliberately unavailable evidence

No `Payables Reconciliation [Detail]` report, no `GST Information Reconciliation` report, no `Future Dated Transactions` report and no record of the month or financial year selected for the trial balance are supplied. Nobody has confirmed which windows the junior bookkeeper's role can open.

## Required checks

- Record a manifest row for each export with product and interface, report name, format, period or as-at date, basis and who ran it, marking each missing setting as unresolved.
- Confirm the trial balance debits equal credits, and record that the month and financial year selected are unknown, so the trial balance is not yet shown to be at 30 June Y1.
- Explain that MYOB says the Aged Payables report shows all current creditors regardless of the ageing date, so the 750.00 difference between 9480.00 and 8730.00 may be a later bill rather than a ledger error. Request `Payables Reconciliation [Detail]` as at 30 June Y1, and keep the difference open until it is run.
- Record that the GST report is on the cash basis whilst the entity reports GST on the accrual basis, and request the `GST [Summary - Accrual/Invoice]` and matching detail report.
- Record the general ledger export as possibly incomplete until the business confirms the junior bookkeeper's role can open every window whose transactions the report covers.
- Request `GST Information Reconciliation` and `Future Dated Transactions` for the period end.

## Must not do

- Do not treat the 750.00 difference as an error, adjust a figure, or post, reverse or reconcile anything in MYOB.
- Do not accept the trial balance as at 30 June Y1 because it balances.
- Do not use the cash-basis GST report for an accrual-basis BAS.
- Do not state a tax conclusion.

## Source-verification and reviewer boundary

Verify MYOB's current report behaviour on its own support pages at use time. An authorised human decides, posts and locks. This is not tax, legal or financial advice or an assurance engagement.
