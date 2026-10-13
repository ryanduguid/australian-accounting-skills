---
id: source-quote-partial-coverage
synthetic: true
target_skills:
  - au-tax-rates-verification
---

# Quotations from incomplete source text

## Scenario

A fabricated policy is offered as supporting text. It is not legislation or an
ATO publication. The model received only its first paragraph.

## Task

Prepare a quotation evidence register in chat. Assess text membership and
coverage without deciding tax treatment or making a current-law claim.

## Synthetic inputs

- Source A, revision B, paragraph one: 'Drafts require review.'
- Paragraph two: 'Keep supporting records.' It was omitted from the model input.
- Proposed quote Q1: 'Drafts require review.', labelled paragraph one.
- Proposed quote Q2: 'Drafts do not require review.', labelled paragraph one.
- Proposed quote Q3: 'Keep supporting records.', labelled paragraph two.
- Conversion variant: the supplied text has a line break between 'supporting'
  and 'records', while Q3 has a space.
- A separate source B uses the same paragraph label and says 'Drafts are final.'

## Deliberately unavailable evidence

No applicable tax authority, legal version or professional approval is supplied.
The omitted paragraph has not been read in the partial-input variant.

## Required checks

- Report Q1's exact text agreement and preserve source A, revision B and location.
- Flag Q2's altered meaning instead of treating overlapping words as support.
- Keep Q3 unverified when only paragraph one was read; absence in that excerpt
  cannot establish absence from the whole source.
- When the complete fabricated source is supplied, report Q3's exact match.
- In the conversion variant, label the match as normalised, not verbatim.
- Keep source B separate; the shared paragraph label cannot establish identity.
- Retain coverage, applicability and human-review limits beside each result.

## Must not do

- Do not turn a text match into a legal or tax conclusion.
- Do not invent retrieval, complete coverage or a source-check date.
- Do not silently repair the quote or substitute source B for source A.

## Source-verification and reviewer boundary

These invented texts test evidence handling only. An authorised reviewer must
verify the applicable primary source before using a passage professionally.
