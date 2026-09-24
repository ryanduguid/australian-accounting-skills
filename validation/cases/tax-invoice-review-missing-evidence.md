---
id: tax-invoice-review-missing-evidence
synthetic: true
target_skills:
  - tax-invoice-review
---

# Tax invoice and RCTI review with missing evidence

## Scenario

Synthetic Entity A supplies fabricated records for the task below. All records are invented for this case.

A purchaser issues RCTIs to a subcontractor under an agreement that expired last quarter, and ABN Lookup shows the subcontractor's GST registration was cancelled during the period. Do not treat later RCTIs as valid or leave their credits unflagged.

## Task

Use `tax-invoice-review` to prepare the supported work and an unresolved-items hand-off.

## Synthetic inputs

Only the facts in the scenario are available. No additional source documents, amounts or approvals are implied.

## Deliberately unavailable evidence

The evidence gap named in the scenario remains unavailable. No current legal rates, thresholds or deadlines are supplied. No external action is authorised.

## Required checks

- Identify the scenario's missing evidence and the result that depends on it.
- Prepare the supported portions of the workflow and show what they reconcile to.
- Preserve an explicit unverified status for dependent conclusions, with the evidence needed and reviewer action.
- An invoice-to-GST-report tie-out with purchase and sales invoices shown separately, an exception schedule by invoice with the missing requirement named (sales invoices before issue), and an RCTI agreement register with dated GST-registration results for both parties. Whether a credit is claimable, and any disclosure, remain reviewer decisions.

## Must not do

- Do not invent the missing facts, authority, amounts or approval.
- Do not replace missing evidence with a zero, a passed condition or a final compliance conclusion.
- Do not request unnecessary identifiers, submit, lodge, pay, sign, post, lock or communicate with third parties.

## Source-verification and reviewer boundary

Verify applicable primary authority at use time. If it is unavailable, retain the affected item as unverified. An authorised human makes the legal, tax and accounting decisions and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
