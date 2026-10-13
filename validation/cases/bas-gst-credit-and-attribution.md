---
id: bas-gst-credit-and-attribution
synthetic: true
target_skills:
  - bas-preparation
---

# Supply GST, buyer credits and period amounts

## Scenario

Synthetic Entity A supplies fabricated purchase evidence for a transaction GST
review. The arithmetic assumptions below are explicit test inputs, not current
law. Applicable treatment and attribution require primary-source verification.

## Task

Keep supply GST, eligible credit and attributable amount separate. Show signed
differences without netting away opposing errors.

## Synthetic inputs

All amounts are AUD. Entity A and suppliers are registered; ordinary domestic
services and supplied invoices are fully described. Cash basis, no special
restrictions beyond the stated use facts. For arithmetic, 10% is supplied.

| Row | Gross | Supply GST | Recorded period credit | Use/evidence |
|---|---:|---:|---:|---|
| A | 1,100.00 | 100.00 | 100.00 | Fully paid in period; valid invoice held/supplied; 100% creditable use |
| B | 1,100.00 | 100.00 | 100.00 | Fully paid in period; valid invoice held/supplied; supported 60% creditable use |
| C | 1,100.00 | 100.00 | 100.00 | Fully paid in period; valid invoice held/supplied; established wholly private use |
| D | 110.00 | 10.00 | 10.00 | Prior-period invoice held/supplied; 100% creditable; only 55.00 paid this period |
| E | -22.00 | -2.00 | 0.00 | Matched credit note and refund in period; original credit claimed; 100% creditable |
| F | 110.00 | 10.00 | 10.00 | Invoice not supplied to reviewer; possession and use proportion unknown |
| G | 1,100.00 | 100.00 | 60.00 | Fully paid in period; valid invoice held/supplied; 100% creditable use |

Payment-date mutations move B's payment after the reviewed period, then remove
its payment date. A separate basis mutation supplies accrual-basis report detail
for this cash-basis entity, with independently supported supply/use facts and D's
documented payment retained. F's payment timing remains unknown.

## Deliberately unavailable evidence

- No evidence of whether Entity A holds F's invoice, or F's business use.
- No primary authority packet or current label set is supplied.
- No authority for posting, amendment or lodgement.

## Required checks

- Preserve the supply GST separately for each row. Verify the legal predicates
  rather than treating the supplied rate as proof of credit eligibility.
- On verified predicates, retain A's 100.00 credit and show B's 60.00 credit
  and -40.00 difference, and C's zero credit and -100.00 difference.
- Assess cash-basis attribution independently: D's conditional period credit
  is 5.00 and difference -5.00; its full supply GST remains 10.00.
- Verify E's adjustment and timing; retain its negative sign, with conditional
  -2.00 period amount and difference rather than treating the refund as a sale.
- Keep F's entitlement and attribution unresolved, not zero; distinguish
  missing reviewer evidence from established non-possession or deficient invoice.
- On verified predicates, G has a +40.00 difference. Show G and B separately
  with their evidence even though their combined correction is zero.
- In B's date mutations, retain the 60.00 conditional entitlement while assessing
  period attribution separately; a missing date is unresolved, not numeric zero.
- In the basis mutation, account for every occurrence and retain independently
  supported supply/use assessments. Preserve the discrepancy, assess documented
  events separately, and leave unsupported period totals/completeness unresolved.
- Show the supported/conditional subtotal separately from F and state its limits.

## Must not do

- Do not use income-tax deductibility or capitalisation to decide a GST credit.
- Do not treat all invoices as attributable to the report period.
- Do not invent F's use fraction, invoice possession or numeric corrected BAS.

## Source-verification and reviewer boundary

Current primary authority must support credit and attribution conclusions.
An authorised reviewer confirms facts, treatment and proposed amounts; passing
arithmetic alone provides no assurance.
