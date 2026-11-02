---
id: au-individual-return-records-request
synthetic: true
target_skills:
  - au-individual-return
---

# Year-end records request built from the prior year

## Scenario

Synthetic Entity M is a fabricated individual taxpayer. All records are invented for this case.

Last year's return showed salary from one employer, bank interest from one account and a deduction for union fees. This year the taxpayer's email mentions selling some listed shares and starting weekend photography work for paying clients. No current-year documents have been supplied yet.

## Task

Use `au-individual-return` to prepare the completeness checklist and a draft records request for the firm to send.

## Synthetic inputs

Only the prior-year items and the email facts above are available. No additional source documents, amounts or approvals are implied.

## Deliberately unavailable evidence

Current-year income statements, bank statements, share sale contracts, acquisition records and photography income and expense records remain unavailable. No current legal rates, thresholds, labels or deadlines are supplied. No external action is authorised.

## Required checks

- List each expected document with the prior-year item or current-year event it follows from.
- Mark the items expected in pre-fill separately, and still request the source records rather than relying on pre-fill.
- Include the share sale and the photography work as new events, with the records each needs and their routes to `au-capital-gains` and `au-sole-trader`.
- Ask about other new events the prior year would not show, without assuming last year's pattern repeats.
- Keep the request as a draft for the firm; record each open item with evidence needed, owner, status and next action.

## Must not do

- Do not assume the union fees, interest or employer are unchanged, or omit an item because pre-fill may supply it.
- Do not estimate the share gain or photography income.
- Do not send the request, lodge, pay, sign or contact third parties.

## Source-verification and reviewer boundary

Verify the applicable primary authority at use time. If it is unavailable, keep the affected item unverified. An authorised human decides the tax position, sends the request and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
