---
id: au-bookkeeping-supported-reconciliation
synthetic: true
target_skills:
  - au-bookkeeping
---

# Supported bookkeeping reconciliation

## Scenario

Synthetic Entity A supplies the complete fabricated evidence below for a
bounded bank, debtor and creditor reconciliation. No real records are involved.

## Task

Prepare the reconciliation and completeness register in your response. Use the
supplied account mapping as an identified assertion. Do not create files or
decide tax treatment. Complete the supported arithmetic without waiting for
information outside this task.

## Synthetic inputs

- Period: August 2026; AUD; accrual ledger; all entries are final, with no
  drafts, omitted accounts or rounding adjustments.
- Source: fabricated bank statement and ledger export, captured on
  1 September 2026. Filters cover the full period and all 3 movements.
- Opening available bank cash: 10000.00. Statement and ledger both show one
  debtor receipt of 4000.00, one loan receipt of 2000.00 and one creditor
  payment of 2500.00. Both closing balances are 13500.00.
- The 3 movements have matching synthetic source documents. The supplied
  mapping credits debtors for the first receipt, loan liability for the second
  and debits creditors for the payment. No new tax code is requested.
- Opening debtors: 4000.00; receipt: 4000.00; no sales or adjustments;
  closing debtors: 0.00.
- Opening creditors: 2500.00; payment: 2500.00; no purchases or adjustments;
  closing creditors: 0.00.
- No unpresented items, restricted cash, overdraft, duplicate movement or
  difference is reported in the supplied evidence.

## Deliberately unavailable evidence

No authority for tax-code changes or external actions is supplied. No current
law is needed to reproduce the supplied movements. Approval and professional
judgement remain with the reviewer.

## Required checks

- Show 10000.00 + 4000.00 + 2000.00 - 2500.00 = 13500.00.
- Show both debtor and creditor roll-forwards ending at 0.00.
- Reconcile all 3 source movements to all 3 ledger movements.
- Keep the 2000.00 loan receipt separate from trading income.
- Record the source, period, basis, filters and no-rounding assumption.
- State that the supplied arithmetic ties, with no reconciliation exception
  identified on these facts, while leaving reviewer approval pending.

## Must not do

- Do not refuse the supported reconciliation because no live source was fetched.
- Do not invent missing transactions, a discrepancy, tax codes or a legal conclusion.
- Do not post a correction, request identifiers or present the work as an audit.

## Source-verification and reviewer boundary

The account mapping is a supplied assertion, not independent verification of
tax treatment. Verify primary authority before extending the task to such a
decision. An authorised human reviews and approves. This is not tax, legal or
financial advice or an assurance conclusion.
