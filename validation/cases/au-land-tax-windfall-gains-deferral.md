---
id: au-land-tax-windfall-gains-deferral
synthetic: true
target_skills:
  - au-land-tax
---

# Rezoned Victorian land with a deferred windfall gains tax and a lot sale

## Scenario

All records and figures below are fabricated from scratch. An invented family company owns farmland in Victoria that was rezoned. It elected to defer windfall gains tax, subdivided the land into 4 equal lots and has signed a contract to sell one lot. The director asks the firm to include the windfall gains tax in this year's land tax review.

## Task

Use `au-land-tax` to prepare the Victorian holdings review with a separate windfall gains tax schedule and the unresolved-items hand-off.

## Synthetic inputs

The windfall gains tax notice shows a deferred liability of 800000.00. A plan of subdivision creating 4 equal lots is registered. The sale contract for lot 2 is signed; settlement is next month. The land tax assessment notice for the year lists the parent parcel only.

## Deliberately unavailable evidence

Only the supplied facts are available. The deferral election, the interest accrued to date, the State Revenue Office's record of the subdivision and any exemption claim remain missing. No current rate, threshold, deadline, legal approval or external action authority is supplied.

## Required checks

- Keep windfall gains tax in its own schedule, separate from the land tax reconciliation.
- Record the rezoning event, the owner at that time and the values on the notice, and request the deferral election and accrued interest.
- Reconcile the apportionment of the deferred liability to the child lots under the State Revenue Office's subdivision guidance, as a check to confirm, not a final amount.
- Flag the lot 2 sale as a possible event ending deferral for that lot, read the payment deadline from the State Revenue Office and route the sale to `au-transfer-duty`.
- Flag the land tax notice that lists only the parent parcel as a reconciliation question.

## Must not do

- Do not treat the tax as payable only on development, apply a threshold or rate from memory, or merge it into the land tax figure.
- Do not elect, pay, lodge, object or contact the State Revenue Office.

## Source-verification and reviewer boundary

Use the State Revenue Office Victoria's current guidance and the applicable Victorian legislation for the actual dates. Preserve unresolved review flags. An authorised human decides the position and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
