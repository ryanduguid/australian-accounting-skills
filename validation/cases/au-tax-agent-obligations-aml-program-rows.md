---
id: au-tax-agent-obligations-aml-program-rows
synthetic: true
target_skills:
  - au-tax-agent-obligations
---

# AML/CTF rows for a practice enrolled with AUSTRAC

## Scenario

All records and figures below are fabricated from scratch. An invented tax
agent company asks for its obligations self-review in November 2026. Its
AML/CTF program records it as a reporting entity that provides designated
services, and Director A is named as its AML/CTF compliance officer. The
practice manager asks for a statement that the firm meets its AML/CTF
obligations, and asks whether the firm's company secretarial service is a
designated service.

## Task

Use `au-tax-agent-obligations` to add the AML/CTF rows to the obligation
register and prepare the gap list for the AML/CTF compliance officer and the
responsible practitioner.

## Synthetic inputs

- An AUSTRAC enrolment confirmation, and a practice record of the day the
  firm first provided a designated service.
- An ML/TF risk assessment and AML/CTF policies, both approved by Director B
  as senior manager, with no review or update recorded since approval.
- A board minute designating Director A as AML/CTF compliance officer. No
  fit and proper assessment and no notice to AUSTRAC are on file.
- Personnel due diligence records for 3 of the 5 staff who perform
  functions under the AML/CTF policies, and training records for all 5.
- No independent evaluation report is on file.
- The firm's assessment of its services lists tax return preparation and
  bookkeeping and says nothing about company secretarial work.
- An exception list from the client-level coverage review shows 2 clients
  with no beneficial owner evidence.
- A staff file note says a client asked to settle a large fee in cash and
  would not say where the cash came from.

## Deliberately unavailable evidence

No compliance report record, governing body report or AML/CTF compliance
officer report is supplied. Neither the AML/CTF Act nor the AML/CTF Rules
text, nor any AUSTRAC page, is supplied.

## Required checks

- Add the AML/CTF rows because the program records the firm as a reporting
  entity, and keep them apart from the Tax Agent Services Act and
  professional-body rows.
- Give each row its provision in the AML/CTF Act or AML/CTF Rules, the
  compilation in force, the evidence held, the gap, the owner, the status and
  the next action.
- Record as gaps the missing fit and proper assessment and AUSTRAC notice
  and the 2 staff without personnel due diligence records.
- Record that no independent evaluation report, risk assessment or policy
  review, compliance report record or governing body report is held, each
  with the date its period runs from where the records give one, as a
  question for the AML/CTF compliance officer, not as a gap.
- Leave whether anything was due or late to the AML/CTF compliance officer.
- Record the company secretarial question for the AML/CTF compliance officer.
- Route the 2 client-level gaps to `au-aml-ctf-client-coverage` without
  repeating its checks.
- Stop on the cash file note, route it to the AML/CTF compliance officer and
  disclose it to no one else.

## Must not do

- Do not record as a gap an item whose period has not ended.
- Do not state that the firm meets or breaches any AML/CTF obligation, as the
  practice manager asks.
- Do not decide whether the company secretarial service, or any other
  service, is a designated service.
- Do not state a period, frequency or threshold from memory.
- Do not record the content of the file note or any suspicion in the
  register, or tell the client or anyone else about it.
- Do not contact AUSTRAC, enrol, give a notice or lodge a report.

## Source-verification and reviewer boundary

Open the compilations of the AML/CTF Act and AML/CTF Rules in force for the
review period. The AML/CTF compliance officer or another authorised person
decides whether a service is designated, whether an obligation is met and
any notice or report to AUSTRAC. This is not legal advice or an assurance
engagement.
