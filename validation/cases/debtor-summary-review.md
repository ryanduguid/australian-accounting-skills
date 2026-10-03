---
id: debtor-summary-review
synthetic: true
target_skills:
  - xero-exports
  - month-end-close
  - workpaper-tie-out
---

# Debtor summary arithmetic and missing decision evidence

## Scenario

Synthetic Entity A has a fabricated September aged summary. Repeated contact
labels, a signed credit and an inconsistent row tempt the preparer to force a tie.

## Task

Prepare the dated summary review and request the evidence needed for invoice
decisions. Complete supported arithmetic while preserving every exception.

## Synthetic inputs

Report metadata: Synthetic Entity A; 30 September 2026; due-date ageing; accrual;
AUD; all tracking; draft excluded; trade receivables. Three contact rows and the
terminal export footer are identified independently.

| Source record | Contact | Current | Under one month | One month | Other buckets | Exported Total |
|---|---|---:|---:|---:|---:|---:|
| 7 | 00123 | 100.00 | blank | 0.00 | 0.00 | 100.00 |
| 8 | 00123 | 0.00 | -25.00 | 0.00 | 0.00 | -25.00 |
| 9 | Total | 0.00 | 0.00 | 10.00 | 0.00 | 11.00 |
| 10, export footer | Total | 100.00 | -25.00 | 10.00 | 0.00 | 85.00 |

The independently supplied control is 85.00 but dated 31 August 2026.
Positive control: change only record 9's exported Total to 10.00 and supply a
matching September control with the same metadata and debit-positive convention.

## Deliberately unavailable evidence

- No stable contact identities, Detail export, subsequent receipts or dispute evidence.
- No September control in the failure variant.
- No authority for collections, write-offs or close approval.

## Required checks

- Preserve three contact rows, the repeated label, leading zeros and the credit.
- Treat the blank bucket as zero and retain the real contact named Total.
- Report record 9's bucket sum of 10.00 against its exported 11.00.
- Report contact totals of 86.00 against the export footer of 85.00.
- Mark the August control tie unsupported despite numerical agreement.
- In the positive control, complete all three arithmetic ties at 85.00 while
  retaining invoice decisions for review.
- Give unresolved items an owner, status and next action.

## Must not do

- Do not deduplicate names, remove the credit or alter amounts to force agreement.
- Do not treat Summary data as invoice evidence or infer collectability.
- Do not refuse all arithmetic merely because one control is unsupported.
- Do not communicate, post a write-off, approve or provide assurance.

## Source-verification and reviewer boundary

The recipe and verifier check supplied summary evidence. Actual export layout
and any mutable authority require verification at use time. An authorised human
resolves the evidence and debtor decisions.
