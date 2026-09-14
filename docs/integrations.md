# Sibling command-line tools

For local Payday Super timing and ATO benchmark ratios through an agent, see [Aus Accounting MCP](https://github.com/ryanduguid/australian-accounting/tree/main/apps/aus-accounting-mcp), distribution `aus-accounting-mcp`.

These skills name 5 maintained tools rather than asking the agent to invent the same work. Each now lives in a monorepo; the distribution and command names are unchanged.

- [`payday-super-check`](https://github.com/ryanduguid/australian-accounting/tree/main/packages/payday-super-checker) (`payday-super-checker` in `australian-accounting`) for contribution timing against SGAA s 18C. The agent must not invent an SGC charge; that remains advice territory.
- [`xero-trial-balance-export`](https://github.com/ryanduguid/accounting-review-pipeline/tree/main/packages/xero-trial-balance-export) (`export-tb`; `xero-trial-balance-export` in `accounting-review-pipeline`) for an optional API trial-balance CSV. The `xero-exports` file path remains the default for any practice.
- [Workpaper Review Gate](https://github.com/ryanduguid/accounting-review-pipeline/tree/main/packages/review-ready-gate) (`review-ready-gate` in `accounting-review-pipeline`) for whether a BAS, month-end, or year-end pack is allowed onto the review desk. A `NOT_READY` or `BLOCKED` pack goes back to the preparer. `READY` is not sign-off.
- [The WIP Tally](https://github.com/ryanduguid/australian-accounting/tree/main/packages/the-wip-tally) (`the-wip-tally` in `australian-accounting`; `wip-tally schedule`) for reviewed cost-to-cost arithmetic. The skills retain the unit-of-account, recognition and professional-judgement gates.

Trial-balance exception review after the gate runs through [Monthly Close Controls](https://github.com/ryanduguid/accounting-review-pipeline/tree/main/packages/monthly-close-control-plane) (`monthly-close-control-plane` in `accounting-review-pipeline`), which surfaces exceptions and never locks a period.
