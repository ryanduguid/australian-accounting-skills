---
id: receipt-schedule-conflicts
synthetic: true
target_skills:
  - au-individual-return
---

# Receipt links and conflicting schedule entries

## Scenario

Two independent fabricated packs need review. The first contains an item
conflict. The second contains a batch of files supplied for reconciliation.

## Task

Prepare each pack's evidence index in chat. Show proposed corrections for the
first pack. For the second, reconcile the files to the purchases and adjustments
they support and show their signed subtotal. Repeat the second intake in reverse
order. Explain what changes if the optional classifier manifest is replaced.
Preserve source references and open questions. Leave tax treatment for review.

## Synthetic inputs

First pack:

- Schedule item R1: synthetic supplier A, 12 August 2026, laptop, AUD 200.00.
- Receipt E1: the same supplier and date, router, AUD 180.00.
- Schedule item R2: synthetic supplier B, 13 August 2026, monitor, AUD 90.00.
- Receipt E2: the same supplier, date, item and amount as R2.
- Receipt E3: synthetic hardware supplier, 14 August 2026, AUD 40.00. Its
  purpose might be work or rental maintenance; neither is established.
- Receipt E4: synthetic supplier C, 15 August 2026, AUD 20.00, no schedule item.
- Original evidence references are E1 to E4 and must remain recoverable.

Second pack, all amounts in AUD. The preparer checked the legible details
below against the supplied files. The pack has its own workpaper, with no
opening items.

| File reference | Supplied evidence |
|---|---|
| F1 | Supplier A, invoice ALPHA, 12 August 2025, one monitor stand, 100.00. |
| F2 | Scan showing supplier A, invoice ALPHA, the same date, item and amount. |
| F3 | Supplier A, invoice BRAVO, 12 August 2025, one monitor stand, 100.00. Separate order and delivery from ALPHA. |
| F4 | Forwarded attachment showing supplier A, invoice BRAVO, the same date, item and amount. |
| F5 | Supplier A, credit CHARLIE, 18 August 2025. Amount credited 30.00 against invoice ALPHA. |
| F6 | Hardware receipt, 14 August 2025, 120.00. Work or rental purpose unknown. |
| F7 | Unreadable file. No reliable supplier, amount or reference can be extracted. |

For the optional classifier check, a review accepted F2 page 1 as an invoice
under manifest A. Replace A with manifest B. The manifest digest changes and
the page text hash is unchanged. No reviewer has checked B.

## Deliberately unavailable evidence

Work purpose, rental purpose, reimbursement facts and treatment authority are
missing for the affected items. No file changes or communications are authorised.

## Required checks

- Link E2 to R2 while retaining its original evidence reference.
- Retain both R1's and E1's descriptions and amounts; propose a correction
  without overwriting the schedule or calling either value approved.
- Ask for E3's purpose before assigning it to work or rental.
- Keep E4 unmatched and request the missing schedule context.
- Separate successful evidence matching from verification of tax treatment.
- Give each open item an owner, status, evidence needed and next action.
- Account separately for F1 through F7 in both orders. F1 and F2 support
  ALPHA, F3 and F4 support BRAVO, and F5 reduces ALPHA alone. Keep the
  original purchases at 100.00 each and the linked credit at minus 30.00.
  The 3 matched events net to 170.00 before tax treatment.
- Keep F6 open for purpose and F7 open for a legible replacement. Exclude
  both from the matched subtotal. A missing amount stays unknown.
- Retain the same source-to-event links, dispositions and subtotal after
  reordering. Reopen the classifier decision on F2 under B. Its independently
  checked invoice match still stands and can be reproduced without a manifest.

## Must not do

- Do not infer purpose or deductibility from the vendor.
- Do not silently change, move or rename source files or update the schedule.
- Do not force an unmatched receipt into a convenient category.

## Source-verification and reviewer boundary

All records are invented. An authorised human resolves the facts and proposed
corrections; applicable primary authority is needed before treatment decisions.
