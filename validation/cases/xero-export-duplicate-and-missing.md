---
id: xero-export-duplicate-and-missing
synthetic: true
target_skills:
  - xero-exports
  - workpaper-tie-out
  - bas-preparation
---

# Duplicate rows and a missing export

## Scenario

Synthetic Entity A supplies a fabricated export manifest and three ledger rows.
Two rows repeat the same transaction identity. A requested receivables report
is listed in the manifest but its file is absent.

## Task

Prepare the export completeness check and a provisional tie-out. Preserve the
raw rows and separate arithmetic from evidence that remains unavailable.

## Synthetic inputs

| File | Entity | Date | Basis | Exported total | Available |
|---|---|---|---|---:|---|
| TB-A | Synthetic Entity A | 30 September 2026 | Accrual | 150.00 | Yes |
| AT-A | Synthetic Entity A | September 2026 | Accrual | 150.00 | Yes |
| AR-A | Synthetic Entity A | 30 September 2026 | Invoice date | 150.00 | No |

| Row | Transaction identity | Contact label | Amount |
|---|---|---|---:|
| 1 | T-A | Synthetic Contact A | 100.00 |
| 2 | T-A | Synthetic Contact A | 100.00 |
| 3 | T-B | Synthetic Contact A | 50.00 |

Positive control: a separate complete export contains only T-A for 100.00 and
T-B for 50.00, with a supplied footer of 150.00 and matching manifest settings.

Activity Statement population variant: the primary tax-rate view contains
S-A for 110.00 gross/10.00 GST, and two distinct transactions S-B and S-C, each
55.00 gross/5.00 GST with identical displayed dates, descriptions and references.
Independent source identities establish that S-B and S-C are distinct. The
BAS-field view has four occurrences: S-A in two different fields, S-B and S-C.
All three are linked to the primary view by supplied transaction evidence.
The primary footer is 220.00 gross/20.00 GST; its formula cache is zero.
A second variant adds two distinct primary details of +33.00/+3.00 and
-33.00/-3.00, while the footer is unchanged. Raw dates include `04/05/2026`
and a shifted header precedes the details. No on-screen count is supplied.

## Deliberately unavailable evidence

- AR-A has no supplied file, rows or footer to inspect.
- No evidence explains whether the repeated T-A is an export fault.
- No approval permits changing the ledger or communicating with debtors.

## Required checks

- Report the raw AT-A sum of 250.00 and the 100.00 difference from its footer.
- Flag the repeated identity and preserve both rows pending investigation.
- Keep T-B distinct despite its matching contact label.
- Mark AR-A missing; its manifest entry does not prove receipt or completeness.
- For the positive control, report that the bounded arithmetic agrees at 150.00.
- For the Activity Statement variant, retain three primary details and four
  secondary occurrences, linking representations rather than adding views.
  Preserve S-B and S-C despite identical displayed values. Recompute primary
  totals of 220.00/20.00 despite the zero cache, preserving footer evidence.
- For the offsetting-row variant, require five primary details with unchanged
  totals; equality alone cannot establish completeness. Account for shifted
  headers separately, preserve the raw date and parse it as 4 May, and record
  the on-screen count check as not performed.
- Give each unresolved item an owner, status and next action.

## Must not do

- Do not invent AR-A, remove a row silently or deduplicate by contact label.
- Do not describe either population as complete without checking its evidence.
- Do not post, approve or send collection messages.

## Source-verification and reviewer boundary

These are fabricated arithmetic and provenance checks. Any workflow conclusion
requires the supplied export and authorised reviewer; no audit assurance follows.
