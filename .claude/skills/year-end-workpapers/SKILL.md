---
name: year-end-workpapers
description: Use when building a review-ready annual workpaper pack from a trial balance — lead schedules per statement area, movement analysis, analytical review, and an indexed pack a reviewer can sign without hunting.
---

# Year-End Workpapers

Turn a year-end trial balance into an indexed, review-ready workpaper pack. The reviewer should never have to ask "where's the support for this?"

## Inputs needed

1. Trial balance as at year end (and prior year TB or signed statements) — see `xero-exports` for export and completeness checks
2. GL detail for the year
3. Subledger and supporting exports: aged AR/AP, bank recs, fixed asset register, loan statements, payroll year summaries
4. Prior year workpaper pack (for structure and carried-forward positions)
5. The firm's workpaper index convention, if one exists — otherwise use the default below

## Workflow

1. **Index the pack.** Default convention: A cash and cash equivalents, B receivables, C inventory/WIP, D other assets and prepayments, E fixed assets, F payables and accruals, G tax accounts (GST, PAYG, income tax), H payroll liabilities, I loans and borrowings, J equity, P&L analytical section. One lead schedule per section.
2. **Lead schedules.** Each shows: prior year closing, current year closing, movement, workpaper references to support. Section total agrees to the TB — to the cent.
3. **Support each section.** Bank agrees to recs and statements; AR to aged listing with collectability noted for old balances; fixed assets to the register with additions/disposals/depreciation reconciled; payables to aged listing plus accrual schedule; GST to the December/June BAS position (see `bas-preparation`); payroll liabilities to the STP year-end position (see `stp-finalisation`); loans to statements with current/non-current split; equity rolls from prior year signed accounts plus profit and distributions.
4. **Journals.** One schedule of all proposed adjusting journals with reasons; mark posted vs pending. Re-run the TB after posting — the pack is built on the *final* TB.
5. **Analytical review.** P&L year-on-year by line: movement %, one-line commentary for anything past the engagement materiality. Gross margin, wage ratio, and interest cover sanity checks.
6. **Carry-forwards and completeness.** Prior year review points addressed; comparatives agree to signed accounts; every TB line mapped to a section (a completeness check — unmapped lines are the classic hole).

## Checks before handing over

- Sum of lead schedules = TB = draft statements
- Every section either supported or flagged, none silent
- Pack index up front, references used consistently

## Boundaries

- Accounting policy choices (revenue recognition, ECL approach, depreciation rates) are engagement decisions — apply the firm's existing positions, flag anything new.
- Run `workpaper-tie-out` as the verification pass after drafting statements.
