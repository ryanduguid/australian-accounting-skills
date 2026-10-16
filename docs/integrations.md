# Sibling command-line tools

Before relying on a workflow's mutable facts, use the [skill source preflight](source-preflight.md).
It keeps source readiness separate from calculator results and review-gate labels.

For local Payday Super timing, Division 7A loan review and ATO benchmark ratios through an agent, see [Aus Accounting MCP](https://github.com/ryanduguid/australian-accounting/tree/main/apps/aus-accounting-mcp), distribution `aus-accounting-mcp`. The Claude Code plugin starts it, pinned, from `.claude-plugin/plugin.json`; see [installation](installation.md#claude-code-plugin).

These skills name 6 maintained tools rather than asking the agent to invent the same work. Each now lives in a monorepo; the distribution and command names are unchanged. None ships with the skills, since a portable skill install carries no runtime, so install a tool separately when a skill calls for it.

- [`payday-super-check`](https://github.com/ryanduguid/australian-accounting/tree/main/packages/payday-super-checker) (`payday-super-checker` in `australian-accounting`) for contribution timing against SGAA s 18C. The agent must not invent an SGC charge; that remains advice territory.
- [`xero-trial-balance-export`](https://github.com/ryanduguid/accounting-review-pipeline/tree/main/packages/xero-trial-balance-export) (`export-tb`; `xero-trial-balance-export` in `accounting-review-pipeline`) for an optional API trial-balance CSV. The `xero-exports` file path remains the default for any practice.
- [Workpaper Review Gate](https://github.com/ryanduguid/accounting-review-pipeline/tree/main/packages/review-ready-gate) (`review-ready-gate` in `accounting-review-pipeline`) for whether a BAS, month-end, or year-end pack is allowed onto the review desk. A `NOT_READY` or `BLOCKED` pack goes back to the preparer. `READY` is not sign-off.
- [`solomons-sword`](https://github.com/ryanduguid/australian-accounting/tree/main/packages/solomons-sword) (`solomons-sword` in `australian-accounting`, on PyPI; `solomons-sword s100a-check`) for an optional local classification of stated facts against PCG 2022/2's zones, named by `au-trust-distributions`. Its label is a review aid, never a conclusion on whether section 100A applies.
- [The WIP Tally](https://github.com/ryanduguid/australian-accounting/tree/main/packages/the-wip-tally) (`the-wip-tally` in `australian-accounting`; `wip-tally schedule`) for reviewed cost-to-cost arithmetic. The skills retain the unit-of-account, recognition and professional-judgement gates.

Trial-balance exception review after the gate runs through [Monthly Close Controls](https://github.com/ryanduguid/accounting-review-pipeline/tree/main/packages/monthly-close-control-plane) (`monthly-close-control-plane` in `accounting-review-pipeline`), which surfaces exceptions and never locks a period.

## MYOB reads

The `au-bookkeeping` workflow accepts identified MYOB exports or an approved
connector's read results. Record the selected company file or business, period,
basis, filters and capture date, and reconcile its identity to the engagement
before each read. AccountRight and MYOB Business can expose different product
features; an absent endpoint or unsupported report leaves that evidence missing.
Use exports when a connector cannot establish the required scope.

MYOB's [authentication](https://developer.myob.com/api/myob-business-api/api-overview/authentication/)
and [scope documentation](https://developer.myob.com/api/myob-business-api/api-overview/scopes/)
describe provider-managed sign-in and endpoint permissions. Have the approved
application manage authorisation and credentials; do not paste them into chat,
workpapers or this repository. Inspect the connector's actual tools and permissions
before using it; OAuth access can include writes and does not approve them.

The `@alfe.ai/myob-mcp` package is a separate third-party option, not a bundled
dependency. Its 0.5.3 metadata declares `UNLICENSED`, and its README requires
`myobBusinessId` on each MYOB API tool with Alfe-managed OAuth. These are provider
specific details to recheck at use time, not an instruction to install it or copy
its code. See the [package metadata](https://registry.npmjs.org/@alfe.ai%2Fmyob-mcp).

## Firm-template deliverables

`au-tax-research` can prepare a draft in a supplied Word, Excel or PowerPoint
template. Configure the template paths and versions and secure output location
in the [firm context example](../templates/firm-CLAUDE.md.example). The requested
layout must preserve citations, source-version evidence and open review items.
Record rendering and recalculation checks separately from the reviewer's decision.
