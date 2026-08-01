---
name: div7a-compliance
description: Use when reviewing shareholder or associate loans, payments, or debt forgiveness by a private company for Division 7A exposure — building the loan register, checking complying loan agreements, and calculating minimum yearly repayments.
---

# Division 7A Compliance

Build the Div 7A picture for a private company: what's been advanced, what's covered by a complying agreement, what must be repaid by when, and what's at risk of being a deemed dividend.

## Inputs needed

1. GL detail for shareholder/associate loan accounts, drawings, and intercompany accounts for the income year
2. Existing loan agreements (terms, dates, security)
3. Prior year Div 7A schedules and repayment history
4. The company's lodgment day for the year (actual or expected)
5. Trust structures in the group, if any (UPE exposure)

## Workflow

1. **Sweep for Div 7A events.** Loans, payments, and debt forgiveness to shareholders or their associates during the year — including transactions routed through drawings, "temporary" advances, and assets used personally. List every candidate with account, counterparty, and amount.
2. **Classify each event.** Repaid in full before lodgment day / covered by complying agreement / new loan needing an agreement / potential deemed dividend. Note: repayments that are re-borrowed from the company shortly after are disregarded as repayments (s 109R) — they do not reduce the loan or count toward minimum yearly repayments. Treat the loan as still outstanding and flag the round-trip.
3. **Check agreements are complying.** Written, signed before lodgment day, term within the maximum (7 years unsecured; 25 years where properly secured over real property — verify current maximums at ato.gov.au), interest at or above the benchmark rate. Pull the current benchmark interest rate from ato.gov.au — it changes yearly; never use a remembered figure.
4. **Calculate minimum yearly repayments** for each complying loan using the ATO's formula with the current benchmark rate. Compare to actual repayments; shortfall = deemed dividend exposure for the year, capped by distributable surplus. MYR applies from the income year after the loan is made — for loans advanced this year, the action is a complying agreement (or repayment) before lodgment day, not an MYR.
5. **Distributable surplus.** Compute per the statutory formula — a deemed dividend can't exceed it; document the calculation.
6. **Trust UPEs.** Identify unpaid present entitlements owed to corporate beneficiaries. The High Court held in *Bendel* [2026] HCA 18 that a UPE is not of itself a Div 7A loan; the ATO is withdrawing its contrary rulings and a legislative response remains possible — state the current guidance relied on, with citation and date, and flag the position to the reviewer rather than asserting it.
7. **Output the register.** Per counterparty: opening balance, movements, agreement status, minimum repayment vs actual, exposure, action required before lodgment day. Write the register under `output/`, never at repo root — confirm the repo's `.gitignore` covers `output/` and add it if absent; generated workpapers carry client data and never enter version control.

## Checks before handing over

- Benchmark rate cited with ATO source and check date
- Every loan classified — nothing left as "misc drawings"
- Actions dated against lodgment day, the real deadline for most fixes

## Boundaries

- High-consequence area: this skill produces a register and flags, not conclusions. Deemed-dividend positions, UPE treatment, and repair strategies (e.g. converting to complying loans) are reviewer/partner decisions.
- Client data: follow the firm's CLAUDE.md privacy rules; exclude TFNs and any identifier the task does not need; keep exports and generated output out of version control.
- Not tax advice.
