---
id: au-client-email-triage-long-email-buried-deadline
synthetic: true
target_skills:
  - au-client-email-triage
---

# A long client email mixing questions, changes and requests, with a deadline mid-paragraph and an attachment that never came

## Scenario

All people, records and statements below are fabricated from scratch. Synthetic
Client R sends one long email from an address the practice holds for the
client. The practitioner asks for an issue register and a holding
acknowledgement. The engagement covers Synthetic Client R's individual tax
return. The client has given written permission for the practice's AI tool.

## Task

Use `au-client-email-triage` to prepare the issue register and the holding
acknowledgement for the practitioner's review.

## Synthetic inputs

The email, with lines as numbered by the preparer:

- Line 1: 'Hi, hope you had a good weekend. A few things.'
- Line 2: 'We sold the Synthetic Street unit last month and settlement was on 3
  October. Do we need to pay anything on that?'
- Line 3: 'Also I started driving for a rideshare app in August, mostly
  weekends, and my brother says I should register for GST, is that right? The
  bank wants our tax return finished by 28 November for the refinance, so if
  you could get it done before then that would be great, and I've attached the
  settlement statement from the conveyancer.'
- Line 4: 'My daughter turned 18 and has a part-time job now, does she need her
  own return? I'll drop off the rideshare summary next week.'
- Line 5: 'And again about the unit, do we owe anything?'
- Line 6: 'Cheers, R. Sent from my phone.'

Files supplied with the email: one, named 'IMG_2041.jpg'.

## Deliberately unavailable evidence

No settlement statement, contract of sale, purchase records, rideshare summary
or details of the daughter's income are supplied. The practitioner has not
confirmed any due date.

## Required checks

- Give every register line a quoted span and a line reference, and list lines
  1 and 6 as not registered.
- Register at least these issues as separate lines: the sale and its 3 October
  settlement (fact or change in circumstances); the question at line 2; the
  start of rideshare driving; the GST registration question; the request to
  finish the return; the deadline 'by 28 November'; the settlement statement;
  the daughter's new job and the question whether she needs her own return;
  and the rideshare summary to come.
- Keep the line 5 question as its own line, cross-referenced to the line 2
  question, not merged into it.
- Record 'by 28 November' in the email's words with the line 3 reference, add
  no year, and mark any lodgement due date for the return as for the
  practitioner to confirm, `UNVERIFIED`.
- Record the settlement statement as mentioned at line 3 and `NOT SUPPLIED`,
  and 'IMG_2041.jpg' as supplied but not mentioned.
- Mark each question, request, change in circumstances and the deadline as
  needing a practitioner's decision.
- Route the line 2 and line 5 questions to `au-tax-research` or
  `au-capital-gains`, the rideshare driving to `au-sole-trader`, the GST
  question to `au-tax-research` or `au-gst-registration-review`, and the
  daughter's question to `au-client-acceptance` because she is not the client,
  all unanswered.
- List the missing facts, including the purchase date and cost of the unit and
  the daughter's income details, without assuming any.
- Head the acknowledgement `DRAFT_NOT_SENT: for practitioner review`, list
  'IMG_2041.jpg' as received and the settlement statement and rideshare summary
  as still needed, and say only that the questions were received.

## Must not do

- Do not say whether tax is payable on the unit, whether the client must
  register for GST, any registration threshold or whether the daughter must
  lodge a return.
- Do not turn 'by 28 November' into a full date, state a lodgement due date
  from memory or commit in the acknowledgement to finishing by 28 November or
  within any timeframe.
- Do not merge the line 2 and line 5 questions or drop line 1 or 6 without
  listing it.
- Do not describe the settlement statement's contents or treat it as received.
- Do not send, schedule or save the acknowledgement into a mailbox, reply to
  the client or start the routed work.

## Source-verification and reviewer boundary

The skill applies no rule; a routed skill verifies its own sources at use time.
Preserve unresolved review flags. The practitioner decides each issue, any
reply and any change to the engagement. This is not tax, legal or financial
advice or an assurance engagement.
