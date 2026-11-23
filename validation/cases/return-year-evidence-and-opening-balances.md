---
id: return-year-evidence-and-opening-balances
synthetic: true
target_skills:
  - au-individual-return
---

# Income year evidence and opening balances

## Scenario

An individual supplies 2 independent fabricated packets, one for correspondence and one for continuing workpapers.

## Task

Prepare the 2025-26 intake using Australia/Sydney and hand over the opening schedules for 2026-27. Then process the corrected statement.

## Synthetic inputs

- The mail export uses UTC. M0 arrived on 30 June 2025 at 13:59:59, M1 on 30 June 2025 at 14:00:00, M2 on 30 June 2026 at 13:59:59 and M3 on 30 June 2026 at 14:00:00. M3 attaches invoice J, dated 29 June 2026 and paid on 3 July 2026. Compare the same invoice and payment evidence supplied manually without a message.
- At 30 June 2026 Owner A's reviewed CGT schedule shows 12 unsold units of parcel P with a total cost base of $240 per broker statement S1. Loss schedule L1 shows a $70 unapplied net capital loss. Property R's rental schedule shows an unexpired borrowing expense.
- After the initial roll-forward, statement S2 corrects parcel P's total cost base to $216. The practitioner has yet to reconcile the correction.

## Deliberately unavailable evidence

The facts establishing when J's expense was incurred and the page supporting Property R's remaining borrowing expenses are missing.

## Required checks

- Include M1 and M2 in the local-year message window. M0 and M3 fall outside. Retain J as late evidence. Record its document and payment dates and leave its year open on both intake routes.
- Link each opening row to its owner, prior year and closing schedule. Carry 12 units and $240 from S1 and $70 from L1. Leave the property's opening amount blank and identify the missing closing page.
- Retain S1 as superseded when S2 arrives. Show $216 as the proposed revised basis and reopen that balance and dependent amounts pending reconciliation. Keep the 12 units and the separately evidenced loss traceable.

## Must not do

- Do not assign a year from the message timestamp or count both copies of J as purchases.
- Do not invent an opening balance, silently replace S1 or reuse the unreconciled cost base.

## Source-verification and reviewer boundary

Verify the relevant timing authority and closing evidence before making a proposal. The reviewer decides the year and accepts the corrected balance.
