# Discovery metadata

Public discovery copy must satisfy the rules below wherever it appears, in GitHub
About, repository topics, README, `.claude-plugin/plugin.json` and
`.codex-plugin/plugin.json`.

## GitHub About

`scripts/publish-github-about.sh` holds the description, homepage and topic
list that are actually applied. Run it from a session authenticated to GitHub
(`gh auth status`); the Actions `GITHUB_TOKEN` cannot PATCH homepage (needs
repository admin). GitHub has no public pin API; pin this repository from the
profile **Customize your pins** dialog.

skills.sh has no public submit API. `npx --yes skills@1.5.22 add ryanduguid/australian-accounting-skills`
resolves the default branch, with the CLI version this repository verifies. The v0.5.0 release contains 76
skills, and the default branch can be ahead of it. Keep About copy evergreen. Document versioned counts in the README and
installation guide. Verify the installed revision before advertising its count. skills.sh serves a [page for this repository](https://skills.sh/ryanduguid/australian-accounting-skills).
On 31 October 2026 it showed 67 skills and 159 installs, behind the 76 released, so do not
quote its count as the inventory. The index is install telemetry, not a form. Its Snyk audit
lists W011 and W012 against some skills: W011 reflects that skills read third-party exports,
and W012 cites a remote command, which the skills do not run; they name the optional
`review-ready` tool only where the operator has already installed it. Recheck the audit after
the host re-indexes rather than claiming it is clear.

## Keyword map

- Primary: Australian practice and contracting workflow skills, BAS and
  contract workpaper tie-outs, accountant handoff.
- Topic clusters: GST/BAS, FBT, Division 7A, STP, payday super, Xero exports,
  month-end close, year-end workpapers, progress claims, retentions, WIP,
  contract costs, plant, fuel, payroll tax, TPAR and Coal LSL.
- Agent/platform terms: Claude Code plugin, Codex plugin, portable `npx skills`.

## Copy rules

- Lead with outcomes (review-ready workpapers, tie-outs), not internals.
- Keep prep-only / no-advice / no-lodgement boundaries visible.
- Do not imply ATO, CA ANZ, Xero, SAP, government, or marketplace endorsement.
- Do not claim marketplace approval or official listing until verified.
- Skills encode workflow. Rates, thresholds, and labels are verified live.
- Point agents at the comparison page: https://duguid.com.au/tools/australian-tax-ai-agents/
- Public examples are fabricated. Never describe them as client work.
