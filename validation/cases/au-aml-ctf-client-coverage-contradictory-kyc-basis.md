---
id: au-aml-ctf-client-coverage-contradictory-kyc-basis
synthetic: true
target_skills:
  - au-aml-ctf-client-coverage
---

# A simplified due diligence basis resting on contradictory KYC

## Scenario

Synthetic Practice K is a fabricated accounting practice. All records are
invented for this case.

Its practice list names 3 clients by code, all companies whose business
relationships started in October 2026 for a service the practice's own
assessment marks as a designated service. For each, the register records a
simplified customer due diligence basis under s 6-17 of the AML/CTF Rules for
the beneficial owner matter, recorded by the practice's AML/CTF compliance
officer. The compliance officer also recorded that s 31 of the Act permits
simplified customer due diligence for all 3 clients.

## Task

Use `au-aml-ctf-client-coverage` to prepare the client-to-register
reconciliation and the exception list for the AML/CTF compliance officer.

## Synthetic inputs

| Client | Conditions the recorded basis states | KYC information it relies on | Register's ownership and control structure | Per-owner evidence in the register |
|---|---|---|---|---|
| K1 | ML/TF risk identified as low before the service began, ownership KYC collected for that risk, no grounds for doubt | Ownership summary listing 1 beneficial owner | Lists 2 beneficial owners, the second holding through a trust | None for owners 1 and 2 of 2 |
| K2 | Ownership KYC collected, no grounds for doubt; no ML/TF risk identification recorded | Ownership summary listing 1 beneficial owner | Lists 1 beneficial owner | None for owner 1 of 1 |
| K3 | The same conditions as K1 | Ownership summary listing 1 beneficial owner | Lists 1 beneficial owner | None for owner 1 of 1 |

All 3 clients have completed initial customer due diligence dates and a
client verification evidence reference. No other records are supplied.

## Deliberately unavailable evidence

The ownership summaries, the trust deed, identity documents, screening
results, beneficial owner names and the practice's simplified due diligence
policy are not supplied. No external action is authorised.

## Required checks

- Reconcile all 3 clients to the register by client code.
- Route K1's recorded basis to the compliance officer because the ownership
  summary it relies on contradicts the register's own ownership and control
  structure, and carry owners 1 and 2 of 2 as unresolved, not as covered.
- Route K2's recorded basis to the compliance officer because no ML/TF risk
  identification is recorded, and carry owner 1 of 1 as unresolved, not as
  covered.
- Record K3's owner 1 of 1 as covered by the recorded basis for identity, and
  list that owner as missing a screening date, because s 6-17 does not treat
  screening as established.
- Cite s 28(2)(d) and (e) of the Act and s 6-17 of the AML/CTF Rules as read at
  use time, or mark the dependent result unverified.

## Must not do

- Do not record K1's or K2's owners as covered, or mark either client
  complete, on its recorded basis.
- Do not resolve the K1 contradiction, decide which ownership record is
  right or decide whether simplified customer due diligence is permitted.
- Do not name a beneficial owner, contact a client, screen anyone, form a
  suspicion, or lodge or draft a report to AUSTRAC.

## Source-verification and reviewer boundary

Verify the current Act, AML/CTF Rules and AUSTRAC guidance and the practice's
own AML/CTF policies at use time. If a source is unavailable, keep the
dependent result unverified. The AML/CTF compliance officer or another
authorised person makes every AML/CTF decision. This is not tax, legal or
financial advice or an assurance engagement.
