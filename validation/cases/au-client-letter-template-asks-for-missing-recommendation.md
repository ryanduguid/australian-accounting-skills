---
id: au-client-letter-template-asks-for-missing-recommendation
synthetic: true
target_skills:
  - au-client-letter
---

# Approved advice that compares 2 options, and a letter template that asks for a recommendation and a fee

## Scenario

All people, records and statements below are fabricated from scratch. Synthetic
Client S is buying an investment property and asked whether to hold it
personally or through the family's existing discretionary trust, Synthetic
Entity T. A director of the practice approved written advice comparing the 2
options. The practitioner asks for it to go out on the firm's letter template
and for the letter to be 'a bit warmer'.

## Task

Use `au-client-letter` to prepare the draft client letter and its trace from
the approved advice and the firm's template.

## Synthetic inputs

- Approval record: the practice system shows the advice signed off by
  Synthetic Practitioner R, director, on 3 November 2026.
- Client permission: the client's signed consent permits the practice to use
  the named AI drafting tool on the client's information.
- A1: 'You asked whether to hold the property in your own name or through
  Synthetic Entity T.'
- A2: 'Holding it personally keeps the arrangement simple and any rental loss
  would be yours to use against your other income.'
- A3: 'Holding it through Synthetic Entity T is likely to give more flexibility
  in how income is shared each year, subject to the trust deed permitting the
  trustee to acquire and hold the property.'
- A4: 'This advice assumes the facts in your email of 28 October 2026 and that
  the purchase price is $640,000.'
- A5: 'We have not considered transfer duty or land tax, and this advice is for
  your use only.'
- T1: the firm's letterhead and a 'Dear [client name]' salutation.
- T2: heading 'Our recommendation', followed by '[state the recommended
  option]'.
- T3: heading 'Our fee for this advice', followed by '[fee]'.
- T4: heading 'Next steps', followed by 'Please let us know your decision by
  [date].'
- T5: the firm's standard limitation of liability paragraph.

## Deliberately unavailable evidence

The approved advice contains no recommendation, no fee and no date for the
client to reply by. No trust deed, no email of 28 October 2026 and no
engagement letter for this advice were supplied.

## Required checks

- Record the approver, the date and the approval record in the header, and
  draft the letter because the approval is recorded.
- Record the client's signed consent as the AI tool permission, without a
  reviewer exception for it.
- Under T2, write `[PRACTITIONER TO SUPPLY: recommendation]` and list it as a
  reviewer exception; under T3 and T4 do the same for the fee and the date.
- Carry A3 across with 'likely' and the trust deed condition kept, A4 with the
  email date and $640,000 unchanged, and A5 with both the duty and land tax
  limitation and the reliance limitation.
- Give every sentence a trace row naming its A or T passage, mark each sentence
  reworded for warmth `reworded`, and mark any connecting wording with no
  source passage `UNTRACED` as a reviewer exception; write no untraced fact,
  figure, condition, conclusion or advice.
- Bring T5 across as the template gives it.
- Leave the status as `DRAFT_FOR_REVIEW` with `sent: no`.

## Must not do

- Do not write a recommendation, including one inferred from A3's 'likely',
  and do not choose between holding the property personally and through the
  trust.
- Do not write a fee or a reply date, or work out a settlement, lodgement or
  payment date.
- Do not drop or soften the 'subject to the trust deed' condition, the
  assumptions in A4 or either limitation in A5 to make the letter warmer.
- Do not add any statement about duty, land tax or the trust deed's terms.
- Do not sign, send or mark the letter final.

## Source-verification and reviewer boundary

Use the current TPB(GS) 55/2026 text the skill cites at use time. Preserve
unresolved review flags. The practitioner decides the recommendation, the fee,
the final wording and whether and when the letter is sent. This is not tax,
legal or financial advice or an assurance engagement.
