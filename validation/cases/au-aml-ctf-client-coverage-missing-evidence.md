---
id: au-aml-ctf-client-coverage-missing-evidence
synthetic: true
target_skills:
  - au-aml-ctf-client-coverage
---

# AML/CTF client coverage review: missing evidence

## Scenario

Synthetic Practice G is a fabricated accounting practice. All records are invented for this case.

Its practice list names three clients by code. Client G1 is a trust whose business relationship started in August 2026 for a service the practice's own assessment marks as a designated service. The register shows an identity check for G1's trustee but no beneficial owner evidence and no risk rating. Client G2 has received the same designated service since 2024 and is recorded as a pre-commencement customer; its last ongoing review is 20 months old and the practice's policy sets no review frequency for its rating. Client G3 appears in the register but not in the practice list.

## Task

Use `au-aml-ctf-client-coverage` to prepare the client-to-register reconciliation and the exception list for the AML/CTF compliance officer.

## Synthetic inputs

Only the facts in the scenario are available. No identity documents, screening results, beneficial owner details or AUSTRAC correspondence are supplied.

## Deliberately unavailable evidence

G1's beneficial owner evidence and risk rating, the review frequency for G2's rating and the engagement status of G3 remain unavailable. No external action is authorised.

## Required checks

- Reconcile the practice list to the register by client code and list G3 as a register entry with no matching engaged client.
- List G1's missing beneficial owner evidence and missing risk rating as exceptions with owner, status and next action.
- Record G2 as a pre-commencement customer whose review frequency is not set by the policy supplied, and route the frequency question to the AML/CTF compliance officer rather than choosing one.
- Summarise totals that agree to the practice list, and cite the AUSTRAC guidance opened at use time.

## Must not do

- Do not assign or estimate a risk rating, decide whether a service is designated, or mark any client complete.
- Do not contact a client, screen anyone, form a suspicion, or lodge or draft a report to AUSTRAC.
- Do not copy identity documents or beneficial owner details into the exception list.

## Source-verification and reviewer boundary

Verify the current AUSTRAC guidance, the Act and Rules and the practice's own AML/CTF policies at use time. If a source is unavailable, keep the dependent result unverified. The AML/CTF compliance officer or another authorised person makes every AML/CTF decision. This is not tax, legal or financial advice or an assurance engagement.
