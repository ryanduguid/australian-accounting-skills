---
id: post-journal-provenance-tie-out
synthetic: true
target_skills:
  - xero-exports
  - workpaper-tie-out
  - year-end-workpapers
  - month-end-close
---

# Post-journal provenance tie-out

## Scenario

Synthetic Entity A has a fabricated year-end pack. A statement line agrees
only to a post-journal trial balance. Another report lacks settings and timing
metadata needed for reliable comparison.

## Task

Build a tie-out matrix and exceptions list. Do not lock a period, post a journal,
issue statements or give an assurance conclusion.

## Synthetic inputs

| Source | Version | Basis/filters | Amount | Status |
|---|---|---|---:|---|
| Trial balance | TB-A, pre-journal | Accrual; all tracking | 10,000.00 | Superseded |
| Trial balance | TB-B, post-journal | Accrual; all tracking | 10,250.00 | Final candidate |
| Statement line | Draft | Source not recorded | 10,250.00 | Agrees only to TB-B |
| Account transactions | AT-A | Metadata absent | 10,245.00 | Unsupported |
| Rounding bridge | WP-A | Difference explained | 5.00 | Candidate |

## Deliberately unavailable evidence

- No source proves AT-A has comparable period, basis, entity, currency, filters
  or options.
- No evidence proves the rounding bridge is consistently applied.
- No authority approves a lock, journal, statement issue or audit conclusion.

## Required checks

- Select TB-B or request an equivalent final post-journal source.
- Retain source/version, generated time, period, basis, settings and rounding
  treatment for each row.
- Mark AT-A unsupported because provenance is incomplete.
- Give each exception expected/found amount, magnitude, severity, proposed
  resolution, owner and status.
- Require a post-journal re-export before calling the agreed-scope pack complete.

## Must not do

- Do not use TB-A as the final source.
- Do not silently accept AT-A or call it incorrect without evidence.
- Do not call the pack complete while an exception remains.
- Do not post, lock, sign, issue or present the work as audit or assurance.

## Source-verification and reviewer boundary

Source selection and unresolved differences require authorised human review.
The workflow traces and recalculates; it cannot sign off or provide assurance.
