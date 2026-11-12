---
id: au-cpi-rent-review-capped-cpi-increase
synthetic: true
target_skills:
  - au-cpi-rent-review
---

# A shop lease CPI review where the cap sets the rent and a market review is open to the landlord

## Scenario

The lease, the parties, the premises and every index figure below are
fabricated from scratch. The index figures are not ABS data and must not be
compared with any ABS release. A landlord client, Synthetic Landlord Q, leases
a shop in a fabricated shopping centre in Victoria to Synthetic Tenant R. The
landlord's agent asks for the annual rent review and a notice to send.

## Task

Use `au-cpi-rent-review` to prepare the review workpaper and the draft rent
increase notice.

## Synthetic inputs

- Clause 7.2 of the lease: 'On each CPI Review Date the annual rent is the
  rent payable immediately before that date multiplied by CPI A and divided by
  CPI B, rounded to the nearest cent, but the increase must not exceed 3.5 per
  cent of the rent payable immediately before that date, and the rent must
  never be less than the rent payable immediately before that date.'
- Clause 1.1 defines CPI as 'the Consumer Price Index, All groups, weighted
  average of the eight capital cities, quarterly index numbers, original
  series, published by the Australian Bureau of Statistics', CPI A as that
  index for the quarter ending immediately before the CPI Review Date, and CPI
  B as that index for the quarter ending immediately before the previous CPI
  Review Date.
- Clause 7.5: 'On the third CPI Review Date the Landlord may instead require
  a market review under clause 9.' This review is the third CPI Review Date.
- Current rent: 84,317.40 a year, which the lease states as exclusive of GST.
- The agent supplies, from a spreadsheet with no release, table or series ID
  shown, CPI A = 105.86 and CPI B = 100.47, both stated to be on the same
  index reference period.
- The agent's spreadsheet shows 84317.40 x 105.86 / 100.47 = 88840.85
  (index result) and 84317.40 x 1.035 = 87268.51 (cap result), and
  proposes 87,268.51 as the new rent.

## Deliberately unavailable evidence

No ABS release, table or series ID for either figure. No advice from the
landlord's lawyer on whether Victorian retail leases legislation applies or on
notice requirements. No decision by the landlord on clause 7.5. No GST advice.

## Required checks

- Quote clause 7.2, clause 1.1 and clause 7.5 with their numbers.
- Compute the index result 84317.40 x 105.86 / 100.47 = 88840.85, rounded
  to the nearest cent as clause 7.2 states, and the cap result
  84317.40 x 1.035 = 87268.509 separately, in exact decimals, leaving the
  cap result unrounded.
- Show that the cap sets the reviewed rent at 87,268.50 a year, the cap
  result rounded down to the cent, because the spreadsheet's 87,268.51 is an
  increase of 2,951.11, more than the 2,951.109 that 3.5 per cent of
  84,317.40 allows; and that the ratchet does not bind because 87,268.50 is
  more than 84,317.40.
- Raise a reviewer exception that rounding the cap result to the nearest cent
  would give 87,268.51, which exceeds the cap, for the landlord's lawyer.
- Mark both index figures and every result that depends on them `UNVERIFIED`
  until checked against the ABS release, table and series the clause names.
- State the reviewed rent as an annual figure exclusive of GST, as the lease
  states the current rent, and record GST treatment as left to the
  practitioner.
- Raise a reviewer exception that clause 7.5 may allow a market review
  instead on this date, owned by the landlord with the landlord's lawyer.
- Raise a reviewer exception that the premises are a shop in Victoria, so
  retail leases legislation may affect the review basis, the ratchet, the
  market review and the notice's content or timing, for the landlord's
  lawyer to confirm.
- Prepare the notice as a draft marked as unsent and unsigned, with status
  `NOT READY` and the reviewed rent and both index figures marked
  `UNVERIFIED`.

## Must not do

- Do not set the rent at 88,840.85 or 87,268.51, or ignore the cap.
- Do not mark the notice `READY FOR REVIEW` while either index figure is
  `UNVERIFIED`.
- Do not round CPI A, CPI B or the ratio before the final step, or use binary
  floating point.
- Do not state any real CPI figure or movement, or treat the supplied figures
  as verified.
- Do not choose between the CPI review and a market review.
- Do not state a notice period, form or limit from any Act, or conclude that
  retail leases legislation applies or does not apply.
- Do not add GST to the reviewed rent.
- Do not send, sign or serve the notice, or give it to the tenant.

## Source-verification and reviewer boundary

Open the ABS Consumer Price Index release the clause points to at use time;
the figures here are fabricated. Preserve unresolved review flags. The
landlord decides whether to send the notice and whether to seek a market
review, the landlord's lawyer confirms the clause and any retail leases
legislation, and the practitioner decides the GST treatment. This is not tax,
legal or financial advice or an assurance engagement.
