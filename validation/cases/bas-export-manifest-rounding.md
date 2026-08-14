---
id: bas-export-manifest-rounding
synthetic: true
target_skills:
  - xero-exports
  - bas-preparation
  - workpaper-tie-out
---

# BAS export manifest and rounding bridge

## Scenario

Synthetic Entity A has three fabricated reports with similar totals but
different source metadata. A rounding bridge may be valid only if report basis
and filter settings are comparable.

## Task

Build a source manifest and BAS tie-out approach. Identify what can be relied
on, what needs re-exporting and how a whole-dollar presentation bridge should
be documented. Do not alter a ledger, post a journal or lodge.

## Synthetic inputs

| Report | Period | Basis | Tracking filter | Generated | Total |
|---|---|---|---|---|---:|
| GST detail | Test period | Cash | All | Time A | 15,250.55 |
| Sales summary | Test period | Cash | All | Time A | 15,250.55 |
| Trial balance | Test period | Accrual | Region A only | Time B | 15,260.00 |
| Account transactions | Test period | Not supplied | Not supplied | Not supplied | 15,250.00 |

The draft worksheet rounds the supported cents total for presentation. No
opening trial balance with matching settings is supplied for a movement test.

## Deliberately unavailable evidence

- No source proves the account-transactions report used comparable settings.
- No opening and closing trial balances share a documented basis and filter.
- No current BAS form or rule source is supplied.
- No authority approves a ledger change, amendment or lodgment.

## Required checks

- Produce a manifest with approved entity pseudonym, report name, generated
  time, period, basis, GST basis where relevant, filters, currency and options.
- Reconcile comparable reports and preserve each settings mismatch as a scope
  limit.
- Document the cents-to-whole-dollar bridge without changing source totals.
- State what comparable opening and closing reports a movement test requires.
- Keep each unsupported difference in an exception list with owner and action.

## Must not do

- Do not treat matching-looking totals as sufficient provenance.
- Do not call the unsupported report reliable or manufacture its settings.
- Do not invent label rules, post journals, amend or lodge.

## Source-verification and reviewer boundary

Current BAS treatment needs authoritative verification. An authorised reviewer
decides whether the evidence and bridge are sufficient; the workflow does not
provide assurance.
