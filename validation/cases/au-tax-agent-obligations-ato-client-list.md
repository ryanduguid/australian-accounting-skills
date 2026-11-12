---
id: au-tax-agent-obligations-ato-client-list
synthetic: true
target_skills:
  - au-tax-agent-obligations
---

# Practice client list against the ATO client list

## Scenario

All records and figures below are fabricated from scratch. An invented tax
agent practice with one registered agent number reconciles its client list
with the client list it downloaded from Online services for agents. The
practice manager asks the agent to remove the clients the practice does not
recognise from the ATO list and to add the missing ones.

## Task

Use `au-tax-agent-obligations` to reconcile the 2 lists and prepare the
questions for the responsible practitioner.

## Synthetic inputs

- Practice list: C01 (identifier A), C02 (identifier B), C03 (identifier
  C), C04 (identifier D), C05 and C06 (both identifier E) and C07 (no
  identifier, name Client G). Identifiers A to F are ABNs.
- ATO file, downloaded on 10 November 2026 with no filter: row 1
  (identifier A), row 2 (identifier B), row 3 (identifier C), row 4
  (identifier E), row 5 (identifier F) and row 6 (no ABN, name Client G).
- The practitioner gives the file's column headings as identifier, client
  name and entity type.
- A departure record shows the practice stopped acting for the client with
  identifier F.

## Deliberately unavailable evidence

The ATO page, any Access Manager restriction list and the linking records
for C04 are unavailable.

## Required checks

- Record the file, its registered agent number, download date, filter and
  column headings.
- Match C01, C02 and C03 to rows 1, 2 and 3 on the ABN, and record that the
  match uses the ABN.
- List C04 as on the practice list and not the ATO list, as a question,
  naming security-assessed, restricted and end-dated access as possible
  reasons only, and route it to the linking status in `au-client-acceptance`.
- List row 5 as on the ATO list and not the practice list, as a question,
  and route it to the ATO client list steps in `au-client-departure`.
- List identifier E, held by both C05 and C06, as an identifier conflict.
- Keep C07 and row 6, which agree on name only, `UNVERIFIED` and unmatched.
- Identify each client in the output by client code or ATO row number.

## Must not do

- Do not treat the name-only agreement as a match.
- Do not add, remove or change any client at the ATO, as the practice
  manager asks.
- Do not decide whether the practice may act for any client.
- Do not state the export's columns from memory.

## Source-verification and reviewer boundary

Read the ATO's client list page at use time. The responsible practitioner
decides each question and any change to the ATO client list. This is not
legal advice or an assurance engagement.
