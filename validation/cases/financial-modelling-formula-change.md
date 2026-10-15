---
id: financial-modelling-formula-change
synthetic: true
target_skills:
  - financial-modelling
  - workpaper-tie-out
---

# Formula changes concealed by matching cached totals

## Scenario

A fabricated model revision shows the same displayed total as its predecessor.
Its calculation cell has been replaced by a constant, and another formula links
to an earlier workbook. Only formula text and supplied source values are available.

## Task

Prepare a revision exceptions list and an independent arithmetic check in chat.
Do not claim workbook recalculation, edit a workbook or approve the model.

## Synthetic inputs

- Source values B2:B5: 10.00, 20.00, 30.00 and 40.00, all in AUD.
- Previous total B6: `=SUM(B2:B5)`; displayed value: 100.00.
- Revised total B6: constant 100.00 with the same formatting and display.
- Proposed driver change B5: 50.00, giving an independently expected total of 110.00.
- Revised C6: `='[prior.xlsx]Inputs'!C6`; the referenced workbook is unavailable.
- Range variant B6: `=SUM(B2:B4)`; it omits the last supplied input.
- Scale variant: one labelled output is in AUD thousands while its formula
  uses AUD amounts without conversion. A hidden row contains an override.

## Deliberately unavailable evidence

No Excel engine, complete workbook, external-link target or review approval is supplied.

## Required checks

- Recompute the original total as 100.00 and the changed-driver total as 110.00.
- Identify the formula-to-constant replacement even though cached totals agree.
- Report the external link, omitted range boundary, unit mismatch and hidden override.
- Separate substantive logic changes from formatting and identify affected outputs.
- Reopen the affected review checks; record recalculation and full-workbook coverage
  as not performed, with owner and next action.

## Must not do

- Do not infer formula agreement, recalculation or completeness from displayed totals.
- Do not repair missing evidence, follow the external link or approve the workbook.

## Source-verification and reviewer boundary

These are fabricated formula and arithmetic observations. The authorised reviewer
checks the actual workbook and underlying records before making a decision.
