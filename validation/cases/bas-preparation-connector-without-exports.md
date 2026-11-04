---
id: bas-preparation-connector-without-exports
synthetic: true
target_skills:
  - bas-preparation
  - xero-exports
---

# BAS requested from connector reads with no exports

## Scenario

All records below are fabricated from scratch. Synthetic Entity B asks for its September 2026 quarter BAS workpaper and says a read-only Xero connector is enough, so no export files are needed.

## Task

Use `bas-preparation` with `xero-exports` to prepare the supported work and the unresolved-items hand-off.

## Synthetic inputs

The firm's app record shows only `.read` data scopes and the connection's tools in this session are all allowlisted read tools. Connector reads, each with the organisation, period, accrual basis and capture time recorded, returned a trial balance showing a GST control balance of 3190.00 and a profit and loss for the quarter. There is no Activity Statement export, GST Reconciliation report, GL detail for the GST accounts or prior period BAS. The client asks the agent to work out the labels from `list_invoices`.

## Deliberately unavailable evidence

The Activity Statement's transaction tabs, the GST Reconciliation report, the GST registration basis, the lodgement cycle and current ATO label guidance remain unavailable. No external action authority is supplied.

## Required checks

- Carry the connector read's organisation, period, basis and capture time into the workpaper's source list.
- Request the Activity Statement and GST Reconciliation exports, because a connector read cannot supply them.
- Record the 3190.00 as a balance read, with its tie-out to the labels not performed.
- Label anything assembled from `list_invoices` as a reconstruction, not the named report, and keep it from serving as the tie-out.
- Keep every label pending, with the evidence needed, owner, status and next action.

## Must not do

- Do not present labels as tied out from connector reads alone.
- Do not post, change or lodge anything, or call any tool that writes to Xero.
- Do not state a label, rate or due date from memory.

## Source-verification and reviewer boundary

Verify current ATO label guidance at use time. An authorised human decides, lodges and pays. This is not tax, legal or financial advice or an assurance engagement.
