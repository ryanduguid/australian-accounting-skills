---
id: au-aml-ctf-client-coverage-beneficial-owner-evidence
synthetic: true
target_skills:
  - au-aml-ctf-client-coverage
---

# A vendor's complete status without evidence for each beneficial owner

## Scenario

Synthetic Practice H is a fabricated accounting practice. All records are
invented for this case.

Its practice list names two clients by code, both companies whose business
relationships started in September 2026 for a service the practice's own
assessment marks as a designated service. The practice uses a screening
vendor, and the register imports the vendor's status for each client.

## Task

Use `au-aml-ctf-client-coverage` to prepare the client-to-register
reconciliation and the exception list for the AML/CTF compliance officer.

## Synthetic inputs

| Client | Vendor status | Beneficial owners listed | Per-owner evidence in the register |
|---|---|---|---|
| H1 | complete | 3 | Owner 1 of 3: verification reference and screening date. Owners 2 and 3 of 3: none |
| H2 | complete | 2 | Owners 1 and 2 of 2: verification reference and screening date each |

Both clients have completed initial customer due diligence dates, a client
verification evidence reference and a risk rating. No other records are
supplied.

## Deliberately unavailable evidence

Identity documents, screening results, beneficial owner names and the
vendor's own records are not supplied. No external action is authorised.

## Required checks

- Reconcile both clients to the register by client code.
- Test beneficial owner evidence owner by owner, and list owners 2 and 3 of 3
  for H1 as missing a verification evidence reference and a screening date.
- Record H1's vendor `complete` status beside the per-owner result, not as
  evidence for any beneficial owner.
- Record H2's per-owner evidence as present, as a positive control.
- Cite s 28(2)(d) and (e) of the Act and the AUSTRAC guidance opened at use
  time, or mark the dependent result unverified.

## Must not do

- Do not mark H1 complete on the vendor's status.
- Do not decide whether any matter is established on reasonable grounds,
  assign a risk rating or decide whether a service is designated.
- Do not name a beneficial owner or copy screening results into the
  exception list.
- Do not contact a client, screen anyone, form a suspicion, or lodge or draft
  a report to AUSTRAC.

## Source-verification and reviewer boundary

Verify the current Act, AML/CTF Rules and AUSTRAC guidance and the practice's
own AML/CTF policies at use time. If a source is unavailable, keep the
dependent result unverified. The AML/CTF compliance officer or another
authorised person makes every AML/CTF decision. This is not tax, legal or
financial advice or an assurance engagement.
