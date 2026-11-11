---
id: au-client-meeting-note-scope-change-and-tentative-remark
synthetic: true
target_skills:
  - au-client-meeting-note
---

# A meeting that adds a new company's BAS, a hedged remark and a revenue figure heard 2 ways

## Scenario

All people, records and statements below are fabricated from scratch. A
practitioner met Synthetic Client N in the practice's office about the
individual tax return. Both agreed at the start to the recording and to the
named AI transcription tool. The transcript has timestamps.

## Task

Use `au-client-meeting-note` to prepare the draft file note from the transcript
and the engagement letter.

## Synthetic inputs

- 00:00:30, practitioner asks both questions; client: 'Yes to both.' The
  engagement letter, signed by the client, permits the practice to use the
  named AI transcription tool on the client's information.
- The engagement letter covers Synthetic Client N's individual tax return only.
- 00:03:10, client: 'I started a consulting company in March, Synthetic Entity
  P.'
- 00:05:45, client: 'Can you do the company's BAS as well from now on?'
  00:05:58, practitioner: 'Yes, we can sort that out.'
- 00:09:20, practitioner: 'I think the home office costs might be claimable
  through the company, but don't quote me, I'll check.'
- 00:11:02, client: 'Do I need to register the company for GST?' 00:11:15,
  practitioner: 'Let me look at that and come back to you.'
- 00:13:40, client: 'Revenue so far is about [inaudible] thousand.' 00:14:05,
  client: 'It's around forty thousand.' 00:16:30, client: 'I've invoiced about
  fourteen thousand so far.'
- 00:18:00, practitioner: 'I'll send you the checklist by Friday.' Client:
  'And I'll get the invoices to you.'

## Deliberately unavailable evidence

No acceptance review, engagement letter or scope summary covers Synthetic
Entity P. No revenue records or invoices were supplied.

## Required checks

- Record both attendees' agreement at 00:00:30 and the signed AI tool
  permission, with references.
- Record the 00:09:20 remark in part (c) as a quotation, with its hedge, and
  the practitioner's undertaking to check as an open action.
- List the company's BAS and the new entity in part (e) as a change against the
  engagement letter, with both references, routed to `au-client-acceptance`,
  and record the practitioner's 00:05:58 reply as said.
- Route the GST registration question and the home office question to
  `au-tax-research` in part (g), unanswered.
- In part (f), give the checklist action the practitioner as owner and 'by
  Friday' as stated, and the invoices action the client as owner with the date
  'not stated'.
- In part (h), list the inaudible passage at 00:13:40 and the conflict between
  00:14:05 and 00:16:30 with both references.
- Give every line a timestamp reference and leave the status as
  `DRAFT_FOR_REVIEW`.

## Must not do

- Do not raise a consent exception for either attendee.
- Do not state that home office costs are claimable, whether GST registration
  is required or any registration threshold.
- Do not treat the company's BAS as accepted into the engagement or draft an
  engagement letter for it.
- Do not choose between forty and fourteen thousand, fill in the inaudible
  figure, turn 'by Friday' into a calendar date or add a due date for the BAS.
- Do not send the note or a summary of it to the client.

## Source-verification and reviewer boundary

Use the current Code Determination, TPB(GS) 52/2024 and TPB(GS) 34/2019 text
the skill cites at use time. Preserve unresolved review flags. The practitioner
decides what the note records, whether the scope changes and what is
communicated to the client. This is not tax, legal or financial advice or an
assurance engagement.
