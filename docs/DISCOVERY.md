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
and W012 cites a remote command. No skill downloads a script or pipes one into a shell. Six
skills tell the agent to run a local program only when it is already installed: `review-ready`
in `bas-preparation`, `month-end-close`, `workpaper-tie-out` and `year-end-workpapers`,
`close-control` in `month-end-close`, `aasb-corpus` in `au-financial-statements` and
`wip-over-under-billing`, and `wip-tally` in `wip-over-under-billing`. The one remote fetch is
the `cargo install --git` command `wip-over-under-billing` gives for when installation is
approved, which builds `wip-tally` from a pinned commit. Recheck the audit after
the host re-indexes rather than claiming it is clear.

[Skills Directory](https://www.skillsdirectory.com/authors/ryanduguid) also lists these skills. On
5 November 2026 its author page showed 65 skills, behind the default branch, so do not quote its
count as the inventory either. Any new listing needs Ryan's authority first.

## Keyword map

- Primary: Australian practice and contracting workflow skills, BAS and
  contract workpaper tie-outs, accountant handoff.
- Topic clusters: GST/BAS, FBT, Division 7A, STP, payday super, Xero exports,
  month-end close, year-end workpapers, progress claims, retentions, WIP,
  contract costs, plant, fuel, payroll tax, TPAR and Coal LSL.
- Agent/platform terms: Claude Code plugin, Codex plugin, portable `npx skills`.

## Copy rules

- Lead with outcomes (review-ready workpapers, tie-outs), not internals.
- State the prep-only, no-advice and no-lodgement boundary once: in `DISCLAIMER.md` and one small line at the end of the README, not in headlines, banners or opening paragraphs.
- Do not imply ATO, CA ANZ, Xero, SAP, government, or marketplace endorsement.
- Do not claim marketplace approval or official listing until verified.
- Skills encode workflow. Rates, thresholds, and labels are verified live.
- Point agents at the comparison page: https://duguid.com.au/tools/australian-tax-ai-agents/
- Public examples are fabricated. Never describe them as client work.
