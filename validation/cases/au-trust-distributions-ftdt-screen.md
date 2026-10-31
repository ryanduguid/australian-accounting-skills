---
id: au-trust-distributions-ftdt-screen
synthetic: true
target_skills:
  - au-trust-distributions
---

# Family trust distribution tax screen

## Scenario

Fabricated Trust T1 has a family trust election recorded with a
specified individual, Synthetic Person F. The fabricated year has resolved
distributions and other movements. No real records are involved.

## Task

Prepare the family trust distribution tax screen in your response. Do not create
files or compute a tax amount.

## Synthetic inputs

| Item | Recipient | Fabricated relationship supplied | Movement | Amount | Evidence |
|---|---|---|---|---|---|
| 1 | Synthetic Person G | Spouse of Person F | Resolved distribution | 40000.00 | Resolution |
| 2 | Synthetic Person H | Child of Person F | Resolved distribution | 20000.00 | Resolution |
| 3 | Synthetic Person J | Business partner of Person H | Interest-free loan | 15000.00 | Ledger only |
| 4 | Synthetic Entity K | Not supplied | Resolved distribution | 10000.00 | Resolution |
| 5 | Synthetic Person L | Not supplied | Rent-free use of a trust asset | Not valued | Note in the file |
| 6 | Synthetic Trust T3 | Discretionary trust of Person H, with its own election specifying Person H | Resolved distribution | 5000.00 | Resolution |

A second fabricated trust, T2, is mentioned in the file. The file calls it a family
trust in its name and holds no election record for it.

## Deliberately unavailable evidence

The lodged election form, ATO record, interposed entity election for Entity K, the
current family group definition, tax rate and due date are not supplied. Nor is any
evidence of the years before the fabricated year.

## Required checks

- List all 6 items for screening, including the loan and the use of the asset.
- Record the election as unverified until the lodged form or ATO record is seen.
- Record items 1 and 2 as inside the family group on the supplied relationships,
  subject to verifying Schedule 2F for the period.
- Record item 3 as outside or `UNRESOLVED` and flag it for specialist review.
- Record items 4 and 5 as `UNRESOLVED`, asking for the interposed entity election
  and for the relationship and valuation evidence.
- Record item 6 as outside or `UNRESOLVED` and flag it for specialist review,
  because T3's election specifies a different individual even though Person H is
  family of Person F.
- Ask whether consideration was given for items 3 and 5.
- State that the name given to T2 establishes no election.
- State that the screen covers only the conferrals the evidence shows and says
  nothing about earlier years.

## Must not do

- Do not state or compute the tax rate, liability or due date from memory.
- Do not suggest a variation, a revocation or a back-dated election.
- Do not treat the loan or use of the asset as outside the screen because no
  resolution exists.

## Source-verification and reviewer boundary

Verify Schedule 2F to the Income Tax Assessment Act 1936 and current ATO guidance
for the period. The trustee and adviser decide. This is not tax, legal or financial
advice or an assurance conclusion.
