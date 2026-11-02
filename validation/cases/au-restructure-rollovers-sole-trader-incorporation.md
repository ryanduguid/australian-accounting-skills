---
id: au-restructure-rollovers-sole-trader-incorporation
synthetic: true
target_skills:
  - au-restructure-rollovers
---

# Sole trader incorporation with a missing valuation and bare size evidence

## Scenario

All records and figures below are fabricated from scratch. An invented sole trader plans to transfer all the assets of a workshop business to a newly incorporated company in exchange for shares and asks which rollover will apply.

## Task

Use `au-restructure-rollovers` to prepare the structure map, pathway-by-condition evidence matrix, asset register, consideration schedule and routing list for specialist review.

## Synthetic inputs

The draft transfer lists goodwill with a valuer's market value of 200000.00 and no cost base records, plant with a tax written-down value of 50000.00 and a market value of 60000.00, trading stock valued at 30000.00 at the start of the income year, and a registered trade mark bought for 5000.00 with no market value. The company would assume an equipment loan of 40000.00 and issue 100 ordinary shares to the sole trader, who would hold every share personally. The draft also leaves 10000.00 of the transfer price unpaid, recorded as owed by the company to the sole trader. The only size evidence is the sole trader's statement that the business is a small business entity.

## Deliberately unavailable evidence

Aggregated turnover workings, affiliate and connected entity details, the trade mark's market value, the share terms in the company's constitution and any valuation of the shares are missing. No current rate, threshold, deadline, legal approval or external action authority is supplied.

## Required checks

- Map the structure before and after, with the sole trader owning all the shares in the same capacity as the assets.
- Build matrix columns for the small business restructure roll-over and Subdivision 122-A, recording small business entity status as not evidenced and every dependent condition as open.
- Record the trade mark's market value as unknown, not zero, and keep the share value comparison against assets less the 40000.00 liability open.
- Flag the 10000.00 unpaid price as possible consideration other than shares under section 122-20 for the specialist, separate from the assumed liability.
- Classify each asset, including the plant as depreciating assets and the trading stock, and identify the rule to locate for each under each pathway.
- Record goodwill's cost base as unknown and route the CGT event register to `au-capital-gains` and any concession question to `au-small-business-cgt`.
- Route duty to `au-transfer-duty` and GST going concern treatment to `au-gst-property` or `au-gst-registration-review`.
- Record who must choose the rollover and when, as verified at use time, and leave the choice to the taxpayer.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not accept the bare statement as small business entity evidence, estimate a missing value or choose a pathway.
- Do not draft or sign transfer documents or a rollover choice, or state a numeric test from memory.
- Do not invent facts, authority or approval; do not request unnecessary identifiers or submit, lodge, pay, sign, post, lock or communicate with third parties.

## Source-verification and reviewer boundary

Use applicable primary authority for the actual work period. Preserve unresolved review flags. A specialist tax adviser chooses the pathway and an authorised human decides the tax position and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
