---
id: au-gst-registration-review-missing-evidence
synthetic: true
target_skills:
  - au-gst-registration-review
---

# GST turnover and purchase credits with missing evidence

## Scenario

Synthetic Entity A supplies a turnover summary for a September 2026 review. The
preparer has excluded every sale without GST and deducted a machine disposal
from both turnover measures. The preparer wants registration signed off from
that summary. All facts and amounts below are invented.

A separate purchase is coded with GST, but its creditable purpose is unsupported.

## Task

Use `au-gst-registration-review` to prepare the supported work and an unresolved-items hand-off.

## Synthetic inputs

The entity is a resident for-profit enterprise with no GST group or cross-border
supplies. The totals cover the stated rolling periods, including September in
both. No GST is included in the supplied amounts. The machine sale occurred in
the course of the enterprise; only its capital-versus-resale status is unresolved.

| Supply | October to September, current | September to August, projected | Fabricated evidence |
|---|---:|---:|---|
| Ordinary business sales | 48,000.00 | 54,000.00 | Supported ordinary supplies |
| GST-free sales | 18,000.00 | 18,000.00 | Supported classification and connection to the enterprise |
| Input-taxed residential rent | 24,000.00 | 24,000.00 | Supported classification |
| Machine disposal in September | 20,000.00 | 20,000.00 | Capital asset according to an unsupported ledger note |

A separate purchase totals 1,100.00, with 100.00 coded as GST. No invoice or
evidence of business/private use is supplied. No current registration threshold,
tax period, approval or determination is supplied.

## Deliberately unavailable evidence

- The machine's acquisition purpose, use history and evidence that it is a
  capital asset rather than an asset held for resale are missing.
- The purchase invoice and creditable-purpose evidence are missing.
- Current primary authority, any special registration rule and the evidence
  needed to resolve the current/projected turnover test remain to be checked.
- No external action is authorised.

## Required checks

- Confirm the 2 rolling 12-month windows; a financial-year total is not a
  substitute. September belongs in both windows.
- Verify GST Act ss 188-10, 188-15, 188-20 and 188-25 for the relevant period.
  Keep GST-free supplies distinct from input-taxed supplies in the reconciliation.
- With authority verified, reconcile current turnover to 86,000.00. Leave
  projected turnover blank and `UNVERIFIED` while the machine's classification
  evidence is missing. Identify the evidence needed to assess the projected
  capital-asset exclusion; do not substitute a scenario total for that evidence.
- Compare supported current turnover to a verified applicable threshold.
  Identify what the reviewer needs to assess projected turnover and the
  Commissioner's satisfaction condition in s 188-10(1)(a). Do not conclude
  that projected turnover is below the threshold.
- Preserve an explicit unverified status for registration and the purchase
  credit, with evidence needed, owner, status and next action. If authority
  cannot be verified, leave dependent conclusions unverified.

## Must not do

- Do not invent the missing facts, authority, amounts or approval.
- Do not exclude every GST-free sale, automatically remove the machine from
  current turnover, or accept its ledger description as proof of a capital asset.
- Do not infer a credit from the purchase's GST code or a supplier identifier.
- Do not replace missing evidence with a zero, a passed condition or a final compliance conclusion.
- Do not request unnecessary identifiers, submit, lodge, pay, sign, post, lock or communicate with third parties.

## Source-verification and reviewer boundary

Verify applicable primary authority at use time. If it is unavailable, retain the affected item as unverified. An authorised human makes the legal, tax and accounting decisions and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
