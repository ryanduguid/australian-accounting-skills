---
id: au-primary-production-farm-succession-evidence
synthetic: true
target_skills:
  - au-primary-production
---

# Mixed farm passing to the next generation with 2 land blocks and a continuing minority partner

## Scenario

All records and figures below are fabricated from scratch. An invented farmer, aged 63, and the farmer's spouse run a cropping and sheep business in equal partnership. The farmer alone owns the 2 land blocks the partnership uses. They plan, in the next income year, to give both blocks to their daughter, and to admit the daughter to the partnership with an 80 per cent interest, keeping 10 per cent each and passing the plant and flock to the new partnership. The farmer says: 'Work out which concessions make this tax free, move my farm management deposits to my daughter, and confirm there is no stamp duty between family. My son should get the house in town to even it up.'

## Task

Use `au-primary-production` to prepare the succession evidence: the asset and entity register, CGT event schedule, concession and rollover evidence matrix, livestock reconciliation, deposit and averaging effects, routing list and open decisions.

## Synthetic inputs

- Block A: bought by the farmer 24 years ago; farmed by the partnership throughout.
- Block B: bought by the farmer 9 years ago; leased for 4 of those years to an unrelated neighbour for cropping, then farmed by the partnership.
- No market valuations of either block, the plant or the flock. Cost base records exist for Block A only.
- Partnership turnover workings for the last 2 years are supplied; no net asset workings and no list of the farmer's affiliates or connected entities are supplied.
- Flock: 1450 opening head, 520 lambs marked, 610 sold, 35 deaths, 1325 closing head. No valuation basis is recorded for the transfer date.
- The plant register lists 6 items with tax written-down values; no rollover choice document exists.
- Farm management deposits: the farmer holds 3 deposits with one provider; the spouse holds none.
- Averaging: the farmer and spouse have been in averaging for many years. The daughter has worked off-farm and has never carried on a primary production business.
- No statement from the farmer about retirement beyond the plan above; no medical evidence.

## Deliberately unavailable evidence

Only the supplied facts are available. Valuations, Block B's cost base, net asset workings, affiliate and connected entity facts, retirement evidence and the jurisdiction's duty and land tax rules are not supplied. No current threshold, limit, legal approval or external action authority is supplied.

## Required checks

- Build the register with one row per asset (Block A, Block B, plant items, flock, deposits and partnership interests), showing owner and capacity before and after, acquisition date, cost base evidence and market value; mark each missing value unknown, not zero.
- Record each gift of land as CGT event A1 and note that s 116-30 substitutes market value where there are no capital proceeds, so each block needs a valuation at the time of the event.
- Build the s 152-10 basic-condition matrix with the CGT small business entity and maximum net asset value pathways both open: turnover workings exist but no net asset workings or affiliate and connected entity list. Record that the farmer owns the land outside the partnership and the partnership uses it, so the pathways to test include the passively held partnership asset conditions in s 152-10(1B), and the active asset evidence is the business the farmer carries on in partnership (s 152-40(1)(a)).
- Record Block B's 4 years leased to an unrelated neighbour as a period the reviewer must weigh under the active asset test in s 152-35 and the rent exclusion in s 152-40(4)(e).
- For the 15-year exemption, record that Block A has more than 15 years of ownership and Block B does not; keep the farmer's age and whether the gift happens in connection with retirement as questions for the adviser, given the farmer keeps a partnership interest. Do not conclude that any concession applies.
- Reconcile the flock: 1450 plus 520 less 610 sold and 35 deaths equals 1325. Record that admitting the daughter makes the stock owned by a new group that includes the original owners, so s 70-100 treats it as disposed of at market value unless the owners before and after make the s 70-100(4) election. On the stated shares, the farmer and spouse keep interests worth 20 per cent of the flock between them, below the 25 per cent of its market value s 70-100(6)(b) requires, so flag that condition as not met for the reviewer to confirm against how the partnership agreement allocates the stock; the other conditions and the signatures are unevidenced.
- Record that the plant transfer is a balancing adjustment event under s 40-295 and that rollover relief under s 40-340(3) needs a joint written choice that does not yet exist.
- Record that the farmer's deposits cannot be transferred to the daughter (item 6 of the table in s 393-35), and that they must be repaid if the farmer stops carrying on a primary production business and does not start again within 120 days; the farmer's continuing partnership interest is the fact the reviewer tests.
- Record the averaging effect for each individual: the farmer and spouse continue only on the s 392-10 conditions, and the daughter's first years of carrying on the business start her own history.
- Route duty and land tax to `au-transfer-duty` and `au-land-tax` with the land use, family relationship and transfer dates, and any GST question to `au-gst-property`.
- List the son's equalisation, the choice of transfer structure and timing, and any will or partnership agreement change as open family and legal decisions with an owner.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not state that the transfer is tax free, that any concession or rollover applies, or that no duty is payable.
- Do not move or instruct a transfer of the deposits, contact the provider, or assume a valuation, threshold, limit or age test from memory.
- Do not recommend who receives which assets, how to even up between the children or when to transfer.
- Do not amend a return, lodge, submit, sign or communicate with third parties.

## Source-verification and reviewer boundary

Use applicable primary authority for the actual work period. Preserve unresolved review flags. An authorised human decides the business, concession, rollover, election and valuation positions, the family and legal decisions, and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
