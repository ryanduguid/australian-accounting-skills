---
id: au-trust-deed-review-unexecuted-variation
synthetic: true
target_skills:
  - au-trust-deed-review
---

# Abstract a deed whose second variation lacks execution evidence

## Scenario

All records and figures below are fabricated from scratch. An invented discretionary trust has an original deed and 2 deeds of variation. The adviser's proposed resolution streams a capital gain to one beneficiary and appoints the remaining income to a company that only the second variation would make a beneficiary.

## Task

Use `au-trust-deed-review` to prepare the document register, clause-referenced deed abstract, legal questions and resolution-readiness checklist for `au-trust-distributions`.

## Synthetic inputs

Clause 4 of the original deed defines income as accounting income and says nothing about streaming. Clause 12 lets the trustee vary the deed by written deed with the appointor's written consent, but not so as to affect a vested interest or benefit the trustee. Variation 1 is signed by the trustee and carries the appointor's signed consent; it inserts a power to determine income as equal to net income and a power to stream capital gains and franked distributions. Variation 2 is an unsigned and undated copy that adds a class of companies controlled by beneficiaries; no appointor consent is held. Clause 15 requires resolutions to be made in writing before the end of the income year at a time the clause specifies. The proposed plan streams a capital gain of 60000.00 to an adult beneficiary and appoints the balance of income to an invented company within the class variation 2 would add. The deed's vesting date falls after the income year.

## Deliberately unavailable evidence

Any executed copy of variation 2, the appointor's consent to it, the trustee's officeholder records and the family trust election records are missing. No current rate, threshold, deadline, legal approval or external action authority is supplied.

## Required checks

- Register all 3 instruments with their execution evidence and record variation 2 as unverified, not effective.
- Abstract clauses 4, 12 and 15 with the clauses variation 1 inserted, and show the beneficiary clause both with and without variation 2 until the lawyer advises.
- Test both variations against clause 12, recording the appointor consent and restricted-matter elements as evidenced, missing or a question.
- Mark the appointment to the company not ready and list its eligibility as a legal question for the trustee's lawyer.
- For the streamed gain, record the streaming power relied on, the financial benefit and recording conditions to meet, whether the plan must appoint capital as well as income, and the deed and ATO timing to verify for the period.
- Record who must make and sign the resolution and whether the appointor's consent is needed, and what the default beneficiary clause does if the appointment fails.
- Request the family trust election records and pass them to `au-trust-distributions` without screening distributions.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not treat an unsigned copy as an executed variation, decide the validity or construction of any clause, or draft, date or sign a resolution or variation.
- Do not repeat the family trust distribution tax screen or the section 100A review that `au-trust-distributions` performs.
- Do not invent facts, authority or approval; do not request unnecessary identifiers or submit, lodge, pay, sign, post, lock or communicate with third parties.

## Source-verification and reviewer boundary

Use applicable primary authority for the actual work period. Preserve unresolved review flags. The trustee's lawyer decides validity and construction; the trustee and adviser decide and execute resolutions, and an authorised human performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
