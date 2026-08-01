---
name: bas-preparation
description: Use when preparing, reviewing, or reconciling a Business Activity Statement (BAS) or IAS for an Australian entity — mapping ledger figures to BAS labels, tying out GST control accounts, or investigating a GST variance before lodgment.
---

# BAS Preparation

Prepare a BAS workpaper from ledger exports and tie every label back to the general ledger. The output is a review-ready workpaper, not a lodgment — lodgment belongs to the registered agent.

## Inputs needed

Ask for these if not provided (period-locked where possible; see `xero-exports` for pulling and validating them):
1. GST Audit Report (or Activity Statement report) for the BAS period
2. Trial balance as at period end
3. GL detail for GST control accounts (GST collected / GST paid, or single GST account)
4. Prior period BAS figures (for variance comparison)
5. The entity's GST registration basis — cash or accruals — and lodgment cycle (monthly/quarterly)

## Workflow

1. **Confirm the basis.** The report basis (cash vs accruals) must match the entity's ATO registration basis. A mismatch here invalidates everything downstream — stop and flag it.
2. **Map ledger figures to labels.** G1 total sales (confirm GST-inclusive vs exclusive convention), 1A GST on sales, 1B GST on purchases, G10/G11 capital vs non-capital acquisitions (full-reporting entities only — Simpler BAS entities, GST turnover under $10m, report just G1, 1A and 1B), W1 gross wages, W2 PAYG withheld, PAYG instalment labels if applicable. Verify current label set at ato.gov.au — labels and instalment arrangements change.
3. **Tie out the GST control account.** Net GST per BAS (1A − 1B) must equal the movement in the GST control account(s) for the period, adjusted for payments/refunds of prior BAS. Reconcile to the cent; document any rounding.
4. **Review coding exceptions.** Scan for: GST-free or input-taxed lines coded with GST, GST claimed on bank fees/stamp duty/wages, entertainment claimed without an FBT position, capital purchases above the ATO's current capital threshold sitting in G11 (full reporters only).
5. **Variance check.** Compare each label to the same quarter prior year and the immediately prior period. Flag movements beyond an agreed threshold with a one-line explanation each.
6. **Assemble the workpaper.** Summary page (labels, amounts, tie-out proof), exceptions list with resolutions, preparer/date, space for reviewer sign-off.

## Checks before handing over

- 1A − 1B equals GST account movement (documented)
- W2 agrees to payroll reports for the period
- Basis confirmed and stated on the workpaper
- Every exception either resolved or explicitly carried to the reviewer

## Boundaries

- Never assert current rates, thresholds, or due dates from memory — cite the ATO page checked and the date checked.
- Do not lodge, and do not draft correspondence to the ATO — that is the registered agent's role.
- This is workflow support, not tax advice.
