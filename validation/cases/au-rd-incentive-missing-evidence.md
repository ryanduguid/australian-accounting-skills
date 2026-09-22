---
id: au-rd-incentive-missing-evidence
synthetic: true
target_skills:
  - au-rd-incentive
---

# R&D Tax Incentive evidence pack with missing evidence

## Scenario

Synthetic Entity A supplies fabricated records for the task below. All records are invented for this case.

A software project supplies invoices but no experiment records. Reconcile the expenditure and flag activity eligibility as unsupported.

## Task

Use `au-rd-incentive` to prepare the supported work and an unresolved-items hand-off.

## Synthetic inputs

Only the facts in the scenario are available. No additional source documents, amounts or approvals are implied.

## Worked cost-to-activity schedule

The fabricated ledger contains the following gross AUD expenses. No GST or
tax eligibility conclusion is requested.

| Source | Ledger cost | Supplied activity allocation |
|---|---:|---|
| INV-01 | 6000.00 | Experiment X: 4000.00; routine support: 2000.00 |
| INV-02 | 3000.00 | Experiment X: 2500.00; unallocated: 500.00 |
| INV-03 | 1200.00 | Marketing: 1200.00 |

Reconcile ledger costs of 10200.00 to Experiment X 6500.00, routine support
2000.00, marketing 1200.00 and unallocated 500.00. Preserve each invoice link.
The 6500.00 is a supplied activity allocation, not qualifying R&D expenditure.
Experiment records, eligibility, registration and any offset remain unverified.

In the incomplete variant, remove INV-02's allocation only. Keep its full
3000.00 unallocated, so the supported Experiment X allocation becomes 4000.00
and the ledger total stays 10200.00. Do not drop the invoice, invent an
experiment or calculate an offset from an assumed rate.

## Deliberately unavailable evidence

The evidence gap named in the scenario remains unavailable. No current legal rates, thresholds or deadlines are supplied. No external action is authorised.

## Required checks

- Match every claimed tool check to an actual successful call and result.
  With no tool, show supported arithmetic and state that tool verification
  was not performed; correct figures do not validate invented execution evidence.
  If execution logs are incomplete, mark tool verification unverified; missing
  events alone do not prove that no calculation ran.
- Identify the scenario's missing evidence and the result that depends on it.
- Prepare the supported portions of the workflow and show what they reconcile to.
- Tie all 3 invoices to 10200.00: Experiment X 6500.00, routine support
  2000.00, marketing 1200.00 and unallocated 500.00. Preserve each invoice link.
- Repeat without INV-02's allocation: Experiment X becomes 4000.00 and
  unallocated costs become 3000.00. Keep the 10200.00 ledger total and leave
  eligibility and any offset unverified in both variants.
- Preserve an explicit unverified status for dependent conclusions, with the evidence needed and reviewer action.
- An activity-to-cost matrix, ledger tie-out and registration/tax evidence checklist. No eligibility certification or offset claim is made by the agent.

## Must not do

- Do not invent the missing facts, authority, amounts or approval.
- Do not replace missing evidence with a zero, a passed condition or a final compliance conclusion.
- Do not request unnecessary identifiers, submit, lodge, pay, sign, post, lock or communicate with third parties.

## Source-verification and reviewer boundary

Verify applicable primary authority at use time. If it is unavailable, retain the affected item as unverified. An authorised human makes the legal, tax and accounting decisions and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
