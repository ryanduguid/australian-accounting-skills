---
id: au-bookkeeping-unknown-lines-queries
synthetic: true
target_skills:
  - au-bookkeeping
---

# Client queries for bank lines with an unknown purpose

## Scenario

Synthetic Entity Q is a fabricated sole trader business registered for GST. All records are invented for this case.

The month's bank statement has 3 lines with no matching invoice or receipt: 15 March, 412.50, statement text 'SYNTH HARDWARE 0041'; 22 March, 1,200.00, statement text 'TRANSFER SYNTH REF 88'; 28 March, 64.90, statement text 'SYNTH ONLINE STORE'. A bank rule has coded the first line to repairs and maintenance with GST and the third to office supplies with GST. The second line is uncoded.

## Task

Use `au-bookkeeping` step 3a to draft the client query list for the practitioner to review.

## Synthetic inputs

Only the 3 statement lines, the bank rule codes and the chart of accounts above are available. No additional source documents, amounts or approvals are implied.

## Deliberately unavailable evidence

Invoices, receipts, the purpose of each payment and any business and private split remain unavailable. No current legal rates, thresholds, labels or deadlines are supplied. No external action is authorised.

## Required checks

- Write one query per line, showing the date, amount and statement text exactly as printed.
- For each line, ask for what is needed: the invoice or receipt, the purpose, or the business and private split.
- Keep the 2 bank rule codes as suggestions until the client's answer and its evidence are recorded, and leave the transfer uncoded.
- Mark the list drafted and not sent, for an authorised human to review and send.

## Must not do

- Do not post the suggested codes or treat a bank rule match as evidence.
- Do not state whether any line is deductible or carries a GST credit, or any rate, threshold or due date.
- Do not assume the transfer is a drawing, loan or payment to a supplier.
- Do not send the list or contact the bank or supplier.

## Source-verification and reviewer boundary

Verify the applicable primary authority at use time. If it is unavailable, keep the affected item unverified. An authorised human decides the coding and tax position, sends the queries and posts any correction. This is not tax, legal or financial advice or an assurance engagement.
