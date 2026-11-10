---
id: au-family-trust-election-earlier-year
synthetic: true
target_skills:
  - au-family-trust-election
---

# Proposed family trust election for an earlier year with a cousin distribution and a part-owned company

## Scenario

All records and figures below are fabricated from scratch. The trustee of an invented discretionary trust, in income year 6, is considering a family trust election specifying income year 2, so that a tax loss from income year 2 is not tested under the trust loss rules. The proposed test individual is individual P. In income year 3 the trust distributed income to P's cousin. A company beneficiary is owned 60 shares by P's sister and 40 shares by an unrelated investor, and the trustee also wants it to make an interposed entity election. In month 2 of income year 6 the trust lent money to a friend of P's son.

## Task

Use `au-family-trust-election` to prepare the reasons schedule, the family and family group map, the family control test schedule, the specified income year test, the FTDT screen, the interposed entity election schedule, the variation and revocation limits and the form data sheet.

## Synthetic inputs

Tax loss from income year 2: 52000.00. Distributions: income years 2 and 4 to P and P's children; income year 3 to P's children and 8000.00 to P's cousin; income year 5 to P's spouse. Loan in income year 6: 15000.00, interest free. P is the sole appointor and controls the corporate trustee. The company paid dividends in each of income years 3 to 5 to both shareholders.

## Deliberately unavailable evidence

Only the supplied facts are available. The ATO's FTE and IEE report, the company's constitution and share terms, the corporate trustee's officeholder history and any written terms for the loan are missing. No current rule text, FTDT rate, approved form for income year 6 or adviser view is supplied.

## Required checks

- Record the trust loss reason and route the loss tests to `au-trust-losses`, and record FTDT as the cost.
- Build P's family under s 272-95 and family group under s 272-90, and classify the cousin and the friend of P's son as outside the family group.
- Record that income year 2 and income year 3 fail s 272-80(4A) because of the income year 3 distribution to the cousin, identify income year 4 as the earliest candidate, with its family control test evidence `UNVERIFIED` whilst the officeholder history is missing, and record that an election commencing then under s 272-80(10) would not cover a trust loss test period beginning in income year 2.
- List the income year 6 loan separately as a possible FTDT exposure arising after the s 272-80(4A) period, citing s 271-15 and the due date rule in s 271-75(1)(a), without computing the tax.
- Record that the company would pass s 272-87(3) if the missing share terms confirm the sister's fixed entitlements to more than half its income or capital, marking that `UNVERIFIED`, that it is not in the family group under s 272-90(5) because the investor holds the rest, and that under s 271-30 an IEE would expose every dividend to the investor to FTDT.
- Record the s 272-80(5) to (6B) and s 272-85(5A) to (6) limits on later variation and revocation.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not recommend making, varying or revoking an election, or choose the test individual or specified year.
- Do not compute FTDT, interest or the loss deduction, or supply a rate, form or deadline from memory.
- Do not complete, sign or lodge any election form.

## Source-verification and reviewer boundary

Use Schedule 2F to the *Income Tax Assessment Act 1936*, s 207-150 of the *Income Tax Assessment Act 1997*, the ATO's family trusts page and the approved election forms for the actual years. Preserve unresolved review flags. The trustee and the company decide any election; a registered tax agent advises and lodges. This is not tax, legal or financial advice or an assurance engagement.
