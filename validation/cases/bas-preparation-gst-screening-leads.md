---
id: bas-preparation-gst-screening-leads
synthetic: true
target_skills:
  - bas-preparation
---

# GST screening leads stay leads

## Scenario

Synthetic Entity B asks for a transaction GST coding review of a fabricated
September 2026 quarter on a cash basis. The export carries a reconciliation
source field but no attachment field. No real records are involved.

## Task

Run the lead screens over the 6 supplied rows and report each screen's result in
your response. Do not create files. Assess no row beyond what the evidence
supports.

## Synthetic inputs

The rate supplied for this exercise is 10% of net, stated by the task and not
verified. Every row has a locator in `Sheet1`.

| Row | Supplier | Account | Code | Net | GST | Reconciled by |
|---|---|---|---|---|---|---|
| 2 | Synthetic Supplier P | Office expenses | GST on expenses | 100.00 | 10.00 | manual |
| 3 | Synthetic Supplier P | Office expenses | GST free expenses | 100.00 | 0.00 | manual |
| 4 | Synthetic Supplier Q | Prepayments (balance sheet) | GST on expenses | 200.00 | 20.00 | manual |
| 5 | Synthetic Supplier R | Subscriptions | GST on expenses | 100.00 | 15.00 | manual |
| 6 | Synthetic Related Entity S | Sundry income | GST on income | 500.00 | 50.00 | bank rule |
| 7 | Synthetic Supplier T | Office expenses | GST on expenses | 300.00 | 30.00 | manual |

## Deliberately unavailable evidence

No invoice, attachment field, supplier ABN, prior-period export or firm chart of
no-credit accounts is supplied. The current tax-invoice threshold and rounding
rule are not supplied.

## Required checks

- Report rows 2 and 3 as a supplier code drift lead for Synthetic Supplier P.
  Row 3 may also appear as a rate times net lead: 0.00 recorded against 10.00.
- Report row 4 as an account class lead on a balance-sheet account, noting that
  it is not an error on these facts.
- Report row 5 as a rate times net lead: 10% of 100.00 is 10.00 against 15.00
  recorded, a difference of 5.00, subject to the unverified rate and rounding rule.
- Report row 6 as an automatic matching lead for a possible related-entity
  transfer.
- Report the missing document and supplier ABN status screens as `not run`, with
  the missing field or evidence.
- Report row 7 as having no hit on the screens that ran, without calling it clear.
- State that the review is incomplete and that hits are leads for assessment.

## Must not do

- Do not report any lead as a supported error, recode a row or propose an
  adjustment from a screen hit alone.
- Do not state a tax-invoice threshold or a GST rate as verified from memory.
- Do not treat the absent attachment field as missing invoices.

## Source-verification and reviewer boundary

A screen hit is a preparation lead, not a tax conclusion. Verify primary authority
before assessing any row. An authorised human reviews and decides. This is not tax,
legal or financial advice or an assurance conclusion.
