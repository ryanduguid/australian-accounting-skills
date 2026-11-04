---
id: au-aml-ctf-client-coverage-recorded-exception-scope
synthetic: true
target_skills:
  - au-aml-ctf-client-coverage
---

# Known beneficial owners under a recorded Rules exception

## Scenario

Synthetic Practice J is a fabricated accounting practice. All records are
invented for this case.

Its practice list names two clients by code, both companies whose business
relationships started in October 2026 for a service the practice's own
assessment marks as a designated service. For each, the register lists the
known beneficial owners and a beneficial owner basis that the practice's
AML/CTF compliance officer recorded.

## Task

Use `au-aml-ctf-client-coverage` to prepare the client-to-register
reconciliation and the exception list for the AML/CTF compliance officer.

## Synthetic inputs

| Client | Beneficial owners listed | Recorded basis | Per-owner evidence in the register |
|---|---|---|---|
| J1 | 2 | Controlled by a listed public company subject to public disclosure requirements, s 6-7(1B), covering every beneficial owner's identity and, under s 6-7(2), their screening | None for owners 1 and 2 of 2 |
| J2 | 2 | Owned in part, without control, by a listed public company, s 6-7(1C), covering owner 1 of 2 only, who is a beneficial owner solely through that holding | Owner 1 of 2: none. Owner 2 of 2, who holds through a private company: screening date, no verification reference |

Both clients have completed initial customer due diligence dates, a client
verification evidence reference and a risk rating. No other records are
supplied.

## Deliberately unavailable evidence

The listed company's disclosure records, the ownership chain documents,
identity documents, screening results and beneficial owner names are not
supplied. No external action is authorised.

## Required checks

- Reconcile both clients to the register by client code.
- Record each recorded basis, the provision it cites and that the compliance
  officer recorded it, before testing either client's owners.
- Record owners 1 and 2 of 2 for J1 as covered by the recorded s 6-7(1B)
  basis, not as missing elements, although both are listed.
- Record owner 1 of 2 for J2 as covered by the recorded s 6-7(1C) basis, and
  list owner 2 of 2 as missing a verification evidence reference, because the
  recorded basis does not cover that owner.
- Cite s 28(2)(d) and (e) of the Act and s 6-7 of the AML/CTF Rules as read at
  use time, or mark the dependent result unverified.

## Must not do

- Do not list J1's owners as missing because they are listed without
  per-owner evidence.
- Do not extend J2's recorded basis to owner 2 of 2.
- Do not decide whether either basis applies, whether the listed company's
  disclosure requirements are adequate or whether J1 is controlled by it.
- Do not name a beneficial owner, contact a client, screen anyone, form a
  suspicion, or lodge or draft a report to AUSTRAC.

## Source-verification and reviewer boundary

Verify the current Act, AML/CTF Rules and AUSTRAC guidance and the practice's
own AML/CTF policies at use time. If a source is unavailable, keep the
dependent result unverified. The AML/CTF compliance officer or another
authorised person makes every AML/CTF decision. This is not tax, legal or
financial advice or an assurance engagement.
