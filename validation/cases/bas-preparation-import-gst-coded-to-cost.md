---
id: bas-preparation-import-gst-coded-to-cost
synthetic: true
target_skills:
  - bas-preparation
---

# Import GST on broker and courier invoices coded to cost

## Scenario

All records and figures below are fabricated from scratch. Synthetic Entity
D, a GST-registered importer of trading stock, asks for its BAS purchases
review. Its bookkeeper coded every customs broker and courier invoice to a
freight expense account with no GST credit.

## Task

Use `bas-preparation` to review the purchase coding in step 5 and prepare the
import GST items for the reviewer.

## Synthetic inputs

| Invoice | Line | Amount | Coding | Evidence supplied |
|---|---|---:|---|---|
| Broker B-1 | GST on imported goods | 300.00 | Freight, no GST | Finalised import declaration naming Entity D as owner and the matching Home Affairs receipt, both dated in this period |
| Broker B-1 | Customs duty | 120.00 | Freight, no GST | Same declaration |
| Broker B-1 | Broker fee and its GST | 55.00 | Freight, no GST | Broker's tax invoice |
| Courier C-1 | Duties and taxes | 40.00 | Freight, no GST | None |
| Supplier S-1 | Import GST recovery | 80.00 | Freight, no GST | Supplier invoice only |

Entity D's deferred GST scheme status is not supplied. The S-1 supplier, an
Australian distributor, imported the goods as its own trading stock, entered
them for home consumption in its own name and sold them to Entity D from its
Australian warehouse after importation. It did not act as Entity D's agent.

## Deliberately unavailable evidence

No deferred GST approval or refusal, no import declaration for C-1, no tax
invoice for the S-1 supply and no confirmation that the goods were imported
for a creditable purpose are supplied. No current ATO page is
supplied.

## Required checks

- List B-1's 300.00 and C-1's 40.00 as possible missed import GST credits, not
  findings.
- Record that B-1's declaration names Entity D as owner and is dated in the
  period, and that C-1 has no declaration, so C-1 stays unresolved.
- Establish Entity D's deferred GST scheme status before proposing any credit,
  and record that a scheme participant claims against the pre-filled deferred
  GST amount rather than from a broker invoice.
- Exclude S-1's 80.00 because the supplier imported the goods on its own
  account, not as Entity D's agent, and record that any credit depends on the
  supplier's taxable supply and a tax invoice, which is not supplied.
- Exclude the 120.00 customs duty as not import GST, and assess the broker fee
  separately on its tax invoice.
- Cite the ATO's GST and imported goods page, its deferred GST page and
  GSTR 2003/15 as read at use time, or mark the dependent result unverified.

## Must not do

- Do not reclassify, post or claim any amount, or treat a coded cost as proof
  that no credit is available.
- Do not calculate import GST from the duty or a rate, or treat a broker or
  courier invoice as a tax invoice for import GST.
- Do not lodge or draft correspondence to the ATO or Home Affairs.

## Source-verification and reviewer boundary

Verify the ATO guidance, GSTR 2003/15 and the entity's deferred GST status for
the actual period at use time. An authorised reviewer decides any
reclassification and the registered agent lodges. This is not tax advice or
an assurance conclusion.
