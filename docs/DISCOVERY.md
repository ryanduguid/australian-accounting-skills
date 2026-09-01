# Discovery metadata

Use this file as the source of truth for public discovery copy across GitHub
About, repository topics, README, `.claude-plugin/plugin.json`, and
`.codex-plugin/plugin.json`.

## GitHub About

Description:

```text
Claude Code and Codex skills for Australian practice and contracting workflows. Not lodgment.
```

Website:

```text
https://duguid.com.au/tools/australian-tax-ai-agents/
```

Topics:

```text
accounting
accounting-automation
agent-skills
ai-agents
ato
australia
australian-accounting
australian-tax
bas
claude-code
codex
construction-accounting
division-7a
fbt
public-practice
python
stp
tax-prep
xero
```

Apply with `scripts/publish-github-about.sh` from a session authenticated to
GitHub (`gh auth status`). The Actions `GITHUB_TOKEN` cannot PATCH homepage
(needs repository admin), so the `github-about` workflow warns and continues
rather than failing. GitHub has no public pin API; pin this repository from
the profile **Customize your pins** dialog.

skills.sh has no public submit API. `npx skills add ryanduguid/australian-accounting-skills`
already lists the 19 skills. Do not claim a skills.sh directory page until
that host serves one for this repository. The index is install telemetry, not a
form.

## Keyword map

- Primary: Australian practice and contracting workflow skills, BAS and
  contract workpaper tie-outs, accountant handoff.
- Topic clusters: GST/BAS, FBT, Division 7A, STP, payday super, Xero exports,
  month-end close, year-end workpapers, progress claims, retentions, WIP,
  contract costs, plant, fuel, payroll tax, TPAR and Coal LSL.
- Agent/platform terms: Claude Code plugin, Codex plugin, portable `npx skills`.

## Copy rules

- Lead with outcomes (review-ready workpapers, tie-outs), not internals.
- Keep prep-only / no-advice / no-lodgment boundaries visible.
- Do not imply ATO, CA ANZ, Xero, SAP, government, or marketplace endorsement.
- Do not claim marketplace approval or official listing until verified.
- Skills encode workflow. Rates, thresholds, and labels are verified live.
- Point agents at the comparison page: https://duguid.com.au/tools/australian-tax-ai-agents/
- Public examples are fabricated. Never describe them as client work.
