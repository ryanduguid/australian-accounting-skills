---
id: bas-preparation-deferred-gst-partly-creditable
synthetic: true
target_skills:
  - bas-preparation
---

# Deferred GST on an importation that is only partly creditable

## Scenario

All records and figures below are fabricated from scratch. Synthetic Entity
F is approved for the deferred GST scheme and lodges monthly. Its draft BAS
claims the whole pre-filled deferred GST amount at 1B.

## Task

Use `bas-preparation` to review the import GST in step 5 and prepare the
deferred GST items for the reviewer.

## Synthetic inputs

| Item | Amount | Evidence supplied |
|---|---:|---|
| Label 7A, pre-filled deferred GST | 500.00 | Activity statement for the month |
| Import declaration A: trading stock | 300.00 | Finalised declaration naming Entity F as owner, dated in the month |
| Import declaration B: equipment | 200.00 | Finalised declaration naming Entity F as owner, dated in the month |
| Draft 1B, deferred GST claimed | 500.00 | Preparer's workpaper |
| Broker invoice for both shipments | No GST line | Broker's tax invoice for its fees only |

The owner has said the equipment in declaration B will be used partly
privately. No apportionment is recorded.

## Deliberately unavailable evidence

No record of the equipment's business use, no apportionment basis and no
current ATO page are supplied.

## Required checks

- Reconcile label 7A's 500.00 to declarations A and B.
- Record declaration A's 300.00 as a credit to propose at 1B for the month,
  subject to the creditable purpose evidence for trading stock.
- Leave declaration B's credit unresolved because the equipment is not wholly
  for a creditable purpose and no apportionment is established.
- Flag the draft's full 500.00 at 1B as unsupported for the unresolved
  portion, citing the ATO's deferred GST page and GSTR 2003/15 paragraphs 18
  and 291 as read at use time, or mark the dependent result unverified.
- Take no credit from the broker invoice.

## Must not do

- Do not propose the full 500.00 at 1B because it matches label 7A.
- Do not estimate the private-use proportion or calculate a partial credit
  without a recorded basis.
- Do not lodge, revise the BAS or draft correspondence to the ATO.

## Source-verification and reviewer boundary

Verify the ATO deferred GST guidance and GSTR 2003/15 for the actual period at
use time. An authorised reviewer decides the apportionment and the registered
agent lodges. This is not tax advice or an assurance conclusion.
