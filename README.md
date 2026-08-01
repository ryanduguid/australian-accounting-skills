# australian-accounting-skills

Claude Code skills for Australian public-practice accounting workflows — BAS, FBT, Division 7A, STP finalisation, month-end close, year-end workpapers.

Built inside Australian public practice, for the people doing the work. Each skill encodes the *workflow* — the steps, the tie-outs, the exceptions to chase — not tax content. Rates, thresholds and due dates change every year, so skills direct the agent to verify current figures at ato.gov.au rather than hardcoding numbers that go stale.

## Who this is for

Accountants in Australian public practice (and finance staff in AU SMEs) using [Claude Code](https://claude.com/claude-code) or any agent that reads `SKILL.md` files. Assumes Xero as the primary ledger; most skills work from standard CSV exports and degrade gracefully with no integrations at all.

## Install

Copy the skills you want into your project or user skills directory:

```bash
git clone https://github.com/ryanduguid/australian-accounting-skills
mkdir -p ~/.claude/skills
cp -r australian-accounting-skills/.claude/skills/* ~/.claude/skills/
```

PowerShell:

```powershell
git clone https://github.com/ryanduguid/australian-accounting-skills
New-Item -ItemType Directory -Force "$HOME/.claude/skills"
Copy-Item -Recurse australian-accounting-skills/.claude/skills/* "$HOME/.claude/skills/"
```

Or copy individual skill folders into `<project>/.claude/skills/`. The skills cross-reference each other (`bas-preparation`, `stp-finalisation`, `workpaper-tie-out`, `fbt-annual-workflow` and `xero-exports` are shared dependencies), so installing the full set works best.

## Skills

| Skill | Use it for |
|---|---|
| `bas-preparation` | Prepare/review a BAS from ledger exports; label mapping, GST control account tie-out |
| `month-end-close` | Checklist-driven close: bank recs, control accounts, accruals, variance review |
| `workpaper-tie-out` | Audit-style verification: every statement line traced to workpaper and source |
| `fbt-annual-workflow` | FBT year-end: benefit identification, declarations, gross-up, RFBA |
| `div7a-compliance` | Division 7A loan register, complying-agreement checks, minimum repayments |
| `stp-finalisation` | STP year-end finalisation: payroll vs GL vs filed totals, super guarantee checks |
| `year-end-workpapers` | Review-ready annual workpaper pack from a trial balance export |
| `xero-exports` | Pulling and parsing Xero reports: quirks, completeness checks, naming conventions |
| `cashflow-forecast-13week` | Rolling 13-week cashflow from bank balance, agings and ATO obligation timing |

Also included: [`templates/firm-CLAUDE.md.example`](templates/firm-CLAUDE.md.example) — a starter `CLAUDE.md` for an accounting firm's repo: terminology, materiality defaults, workpaper conventions, privacy rules.

## Design principles

1. **Workflow over content.** The skill knows the steps and the checks; the ATO website is the source of truth for this year's rates and labels.
2. **Tie-out or it didn't happen.** Every skill ends by reconciling its output back to source — the habit that separates a workpaper from a guess.
3. **No client data, ever.** Examples use placeholder entities and round numbers. The `.gitignore` blocks common client-artifact patterns; keep real exports out of any repo.
4. **Degrade gracefully.** Skills work from CSV exports on disk. Ledger integrations (MCP) are a bonus, never a requirement.

## Disclaimer

These skills are workflow aids for qualified professionals. They are not tax advice, not financial advice, and not a substitute for professional judgment or review. Verify all rates, thresholds and due dates against current ATO publications before relying on any output. Nothing here lodges anything — lodgment is a registered agent's job.

Running these skills means client data passes through a cloud AI service. Check your firm's policy and your confidentiality and privacy obligations first; de-identify by default. [`templates/firm-CLAUDE.md.example`](templates/firm-CLAUDE.md.example) has starter privacy rules.

## Author

Ryan Duguid — accountant in Newcastle NSW, CA ANZ Provisional Member.

## License

MIT — see [LICENSE](LICENSE).
