---
id: au-land-tax-nsw-sole-and-joint-notices
synthetic: true
target_skills:
  - au-land-tax
---

# NSW investor with a sole and a joint land tax notice and a Victorian rental

## Scenario

All records below are fabricated from scratch. An invented individual owns an investment unit in NSW alone, a vacant block in NSW jointly with a sibling and a rental house in Victoria. She received 2 Revenue NSW assessment notices for the year and asks the firm to check her land tax.

## Task

Use `au-land-tax` to prepare the holdings register, the notice reconciliation and the unresolved-items hand-off.

## Synthetic inputs

The individual downloaded both notices from Land Tax Online. One lists the unit and the other, a joint notice, lists the block. A title search shows both siblings as registered proprietors of the block. The settlement statement for the unit is supplied. No Victorian notice is supplied.

## Deliberately unavailable evidence

Only the supplied facts are available. The year's taxing date, thresholds and rates, the sibling's other landholdings, either owner's foreign status and any exemption claim remain missing. No legal approval or external action authority is supplied.

## Required checks

- Route the NSW land to Revenue NSW, the Land Tax Act 1956 and the Land Tax Management Act 1956, and read the taxing date, thresholds and rates from Revenue NSW for the assessment year.
- Record the owner of each NSW parcel at midnight on the taxing date from the title search and settlement statement.
- Reconcile the sole notice and the joint notice separately to the holdings register, keeping the jointly owned block distinguishable.
- Route the Victorian house to State Revenue Office Victoria and the Land Tax Act 2005, outside the NSW reconciliation, and request its assessment from My Land Tax.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not apply a threshold or rate from memory, merge the 2 notices or bring the Victorian house into the NSW reconciliation.
- Do not object, pay, lodge or contact Revenue NSW or the State Revenue Office.

## Source-verification and reviewer boundary

Use Revenue NSW's current assessment notice guidance and the NSW Acts for the assessment year. Preserve unresolved review flags. An authorised human decides the position and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
