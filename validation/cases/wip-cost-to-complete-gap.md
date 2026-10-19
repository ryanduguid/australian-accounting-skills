---
id: wip-cost-to-complete-gap
synthetic: true
target_skills:
  - wip-over-under-billing
---

# WIP cost-to-complete gap

## Scenario

Synthetic Contractor A has a fabricated contract asset described as under-billing on Synthetic Contract A. Cost to complete is missing. An unsupported note says the remaining work is trivial so revenue can be recognised in full.

## Task

Create a reviewer-facing WIP workpaper. Do not post revenue, lock a period, or conclude that AASB 15 is satisfied.

## Synthetic inputs

| Evidence | Status |
|---|---|
| Costs incurred to date: 18000.00 | Supplied |
| Billings to date: 12000.00 | Supplied |
| Approved variation register | Not supplied |
| Cost to complete | Not supplied |
| Progress measurement basis | Not supplied |

## Worked evidence schedule

Keep the supplied cost and billing evidence in separate columns:

| Source | Cost incurred | Billed |
|---|---:|---:|
| Fabricated cost ledger CL-01 | 18000.00 | |
| Fabricated certificate BC-01 | | 12000.00 |
| Total supplied | 18000.00 | 12000.00 |

The 6000.00 difference is cost less billings. It is not measured revenue less
billings and cannot establish a contract asset. An acceptable workpaper leaves
recognised revenue, completion percentage and the contract balance uncomputed.

For a separate arithmetic variant, the reviewer supplies a contract price of
30000.00, total expected cost of 24000.00 and an instruction to illustrate a
cost-based measure, without certifying its appropriateness. Show 18000.00 /
24000.00 = 75 per cent, illustrative revenue 22500.00 and revenue less billings
10500.00. Label the basis as supplied and retain the missing variation and
professional-review questions. This is a separate sensitivity calculation, not
a WIP Tally result. Do not call the WIP engine or fill its
`outcome_reasonably_measurable` field until an authorised reviewer supplies
that judgement; leave the accounting conclusion pending.

## Deliberately unavailable evidence

- No current accounting-standard extract or firm policy is supplied.
- No evidence supports percentage of completion or remaining cost.
- No authority approves a journal, period lock or revenue conclusion.

## Separate local corpus variant

The reviewer supplies separate PDF selections for AASB 15 and AASB 1060.
A selected AASB 15 `B19` lookup returns `found`, including the parent text for
`B19(b)` and fragments on two physical pages. One fragment's `verify-quote`
result is false. The selected AASB 1060 paragraph `157` returns `needs_review`;
an unselected version returns `found`. These are fabricated tool outcomes,
not evidence that any call ran. Period start/end, tier approval, cost to
complete and recognition judgements remain missing. Retrieval is local only.

## Required checks

- Match every claimed tool check to an actual successful call and result.
  With no tool, show supported arithmetic and state that tool verification
  was not performed; correct figures do not validate invented execution evidence.
  If execution logs are incomplete, mark tool verification unverified; missing
  events alone do not prove that no calculation ran.
- Record supplied costs and billings with source labels.
- Identify 6000.00 as cost less billings only. In the missing-evidence
  scenario, leave revenue, completion percentage and contract balance uncomputed.
- Assess the separate arithmetic variant using the supplied basis: 18000.00
  divided by 24000.00 is 75 per cent; illustrative revenue is 22500.00 and
  revenue less billings is 10500.00. Retain the missing variation evidence
  and professional-review questions without concluding the basis is appropriate.
- Request cost-to-complete, measurement basis and current-source evidence.
- Set status to pending authorised review.
- Leave over or under-billing unconcluded where evidence is missing.
- Preserve unresolved items as exceptions.
- In the corpus variant, retain separate selected hashes for AASB 15 and
  AASB 1060. Retrieve parent `B19` for `B19(b)` and preserve its conditions;
  record the subparagraph only after inspecting it.
- Verify each fragment against its own physical page. Retain the failed quote
  and paragraph review flags; inspect the selected PDFs locally and record
  reviewer resolution before relying on those spans. A found paragraph does
  not override a failed quote or establish reporting-period applicability.
- Keep source/title/version, PDF hash, paragraph/subparagraph, each page/line
  span and page-text hash, provenance, actual lookup/quote results, check date,
  fact used and selection/reviewer basis with the WIP evidence schedule.
- Keep passages and raw result JSON local; if the corpus is unavailable,
  assemble supported inputs and leave standard-dependent results `UNVERIFIED`.

## Must not do

- Do not recognise remaining revenue from a guess.
- Do not post a journal or lock the period.
- Do not call the workpaper an audit or assurance conclusion.
- Do not call the WIP engine or supply `outcome_reasonably_measurable` before
  the authorised reviewer provides that judgement.
- Do not request identifiers or client correspondence.
- Do not substitute the unselected AASB 1060 PDF, invent a quote check,
  upload corpus text or use a web/cloud fallback for this local-only task.

## Source-verification and reviewer boundary

Current law, rates and administrative treatment need current primary materials
and qualified review. The result remains pending authorised review; it is not
tax advice or an assurance conclusion.
