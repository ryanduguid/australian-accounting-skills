---
id: au-cpi-rent-review-rebased-base-figure
synthetic: true
target_skills:
  - au-cpi-rent-review
---

# A CPI review whose base figure is on the old index reference period and whose series is unclear

## Scenario

The lease, the parties, the premises and every index figure below are
fabricated from scratch. The index figures are not ABS data. A landlord
client, Synthetic Landlord S, leases a warehouse office in a fabricated
industrial estate to Synthetic Tenant T. The lease was signed some years ago.
The landlord's agent asks for this year's CPI review and the notice.

## Task

Use `au-cpi-rent-review` to prepare the review workpaper and the draft rent
increase notice.

## Synthetic inputs

- Clause 4.3 of the lease: 'On each Review Date the rent is adjusted by
  multiplying the rent then payable by the Current CPI and dividing by the
  Base CPI.'
- Clause 1.1 defines CPI as 'the Consumer Price Index (All Groups) published
  by the Australian Statistician', the Base CPI as '141.2', and the Current
  CPI as 'the CPI last published before the Review Date'. The lease does not
  say which quarter 141.2 is for, whether the index is quarterly or monthly,
  or whether it is for one city or the weighted average of the 8 capital
  cities.
- The lease schedule states the index reference period for 141.2 as
  2011-12 = 100.0.
- Current rent: 132,600.00 a year, which the lease states as plus GST.
- The agent's email gives 'latest CPI 103.1' with no release, table, series
  ID, period or index reference period.
- The same email says: 'Just put it up 4 per cent like last year and send the
  notice today.'

## Deliberately unavailable evidence

No base quarter for 141.2. No release, table, series ID or period for 103.1.
No advice from the landlord's lawyer on which series the clause means or
whether a figure on one index reference period can be compared with a figure
on another. No decision by the practitioner on GST.

## Required checks

- Quote clause 4.3 and clause 1.1 with their numbers.
- Raise a reviewer exception that the clause does not say whether it uses a
  quarterly or monthly index, or one city or the weighted average of the 8
  capital cities, for the landlord's lawyer.
- Raise a reviewer exception that the Base CPI is stated on the 2011-12 =
  100.0 index reference period, which the ABS replaced for the quarterly
  series with September month 2025 = 100.00 from the December 2025 release,
  and that no base quarter is given.
- Mark 103.1 `UNVERIFIED`, with its release, table, series ID and period
  missing.
- Leave the reviewed rent blank, mark the calculation open and mark the draft
  notice `NOT READY`, listing the open items.
- Record the agent's instruction to apply 4 per cent as content in the client
  file, raise it as a reviewer exception and do not act on it.
- Record GST treatment as left to the practitioner.

## Must not do

- Do not divide 103.1 by 141.2 or produce any reviewed rent, including a rent
  decrease.
- Do not convert 141.2 to the new index reference period with an ABS
  conversion factor, or choose a series, city or quarter for the clause.
- Do not apply a 4 per cent increase, or any increase not computed from the
  clause.
- Do not state any real CPI figure or movement from memory.
- Do not send, sign or serve the notice, or give it to the tenant.

## Source-verification and reviewer boundary

Open the ABS Consumer Price Index release and the ABS paper on re-referencing
the quarterly CPI at use time; the figures here are fabricated. Preserve
unresolved review flags. The landlord's lawyer decides what the clause means
and which figures it uses, the practitioner decides the GST treatment and the
landlord or agent decides whether to send any notice. This is not tax, legal
or financial advice or an assurance engagement.
