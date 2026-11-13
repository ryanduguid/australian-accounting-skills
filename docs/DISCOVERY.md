# Discovery metadata

Public discovery copy must satisfy the rules below wherever it appears, in GitHub
About, repository topics, README, `.claude-plugin/plugin.json`,
`.codex-plugin/plugin.json` and `.cursor-plugin/plugin.json`.

## GitHub About

`scripts/publish-github-about.sh` holds the description, homepage and topic
list that are actually applied. Run it from a session authenticated to GitHub
(`gh auth status`); the Actions `GITHUB_TOKEN` cannot PATCH homepage (needs
repository admin). GitHub has no public pin API; pin this repository from the
profile **Customize your pins** dialog.

skills.sh has no public submit API. `npx --yes skills@1.5.22 add ryanduguid/australian-accounting-skills`
resolves the default branch, with the CLI version this repository verifies. The v0.7.0 release contains 107
skills, and the default branch can be ahead of it. Keep About copy evergreen. Document versioned counts in the README and
installation guide. Verify the installed revision before advertising its count. skills.sh serves a [page for this repository](https://skills.sh/ryanduguid/australian-accounting-skills).
On 31 October 2026 it showed 67 skills and 159 installs, and on 11 November 2026 it showed 97 skills
and 256 installs; do not quote its count as the inventory. The index is install telemetry, not
a form. On 11 November 2026, 70 of the 97 skills had a Snyk page there and 27 returned 404.
W011 reflects that skills read third-party exports and web pages. W012, 'Unverifiable external
dependency detected', appears on 2 skills and flags the GitHub URL of an optional external tool:
`solomons-sword` in `au-trust-distributions` (audited 4 November 2026) and
`xero-trial-balance-export` in `xero-exports` (audited 2 October 2026). Socket warns that
`au-financial-statements` and `wip-over-under-billing` leave the provenance of the
`aasb-corpus` executable unverified (both audited 4 November 2026). No skill downloads a script or pipes one into a shell. The README's
[Privacy](../README.md#privacy) section lists each local program a skill names and the 2
`cargo install` commands. Recheck the audits after the host re-indexes rather than claiming
they are clear.

[Skills Directory](https://www.skillsdirectory.com/authors/ryanduguid) also lists these skills. On
5 November 2026 its author page showed 65 skills, behind the default branch, so do not quote its
count as the inventory either. Any new listing needs Ryan's authority first.

## Keyword map

- Primary: Australian tax and accounting agent skills, review-ready workpapers for
  BAS, FBT, Division 7A, trusts, payroll and practice compliance, accountant handoff.
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
