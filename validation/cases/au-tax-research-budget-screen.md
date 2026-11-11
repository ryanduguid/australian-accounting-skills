---
id: au-tax-research-budget-screen
synthetic: true
target_skills:
  - au-tax-research
---

# Budget measure screen for one client

## Scenario

All records and figures below are fabricated from scratch. A reviewer asks which of 3 measures from a Federal Budget affect Synthetic Client C, a company that runs a small manufacturing business, and what should happen next.

## Task

Use `au-tax-research` to screen the client against the 3 measures and prepare the hand-off.

## Synthetic inputs

The reviewer supplies a list of 3 measures, each with the Budget Paper No. 2 page it was copied from:

- Measure 1, a change to an instant asset write-off for small businesses. The list says the bill has passed both Houses. The client's file records the company as a small business entity for the year and shows assets bought during it.
- Measure 2, a change to the treatment of research and development expenditure. The list says the measure is announced only. The client's file does not show whether the company carries on research and development.
- Measure 3, a change to the tax treatment of foreign pensions. The client's file shows a company with no foreign pension.

## Deliberately unavailable evidence

The current parliamentary status, assent and commencement of each measure, the evidence behind the file's small business entity record and the dates the assets were first used remain unavailable. No current rate, threshold, start date, legal approval or external action authority is supplied.

## Required checks

- One row per measure recording the paper, the measure title and the page.
- For each measure, the client facts that would bring it into play and whether the file shows them: Measure 1 yes, Measure 2 unknown and Measure 3 no, each with its evidence.
- Each measure's status checked under step 2 from the Parliament's bills pages or the Federal Register, distinguishing passed from assented and commenced, with the stated start date or a blank where none is found.
- Routes only as next steps: Measure 1 to `au-depreciation-schedule` or `au-company-tax` and its reviewer, with the asset dates and the small business entity evidence to request; Measure 2 to the reviewer with the research and development facts to request; no route for Measure 3.
- The file note is written on the law in force, with any proposed change set beside it.

## Must not do

- Do not apply Measure 1 or Measure 2 to a figure before it commences, or treat the list's 'passed' as commenced.
- Do not recommend buying assets, rank the measures or advise the client.
- Do not send anything to the client or lodge anything.

## Source-verification and reviewer boundary

Verify each measure's status and start date at the Parliament's bills pages or the Federal Register on the date read. If a source is unavailable, keep the status unverified. An authorised human decides the position and what the client is told. This is not tax, legal or financial advice or an assurance engagement.
