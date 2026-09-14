# First run

Minimal path from install to one verified result, assuming Claude Code is already installed:

1. Install the plugin (see [installation](installation.md)): `/plugin marketplace add ryanduguid/australian-accounting-skills` then `/plugin install australian-accounting-skills@ryanduguid`.
2. Export 3 reports from Xero for your most recent completed BAS period: `Activity Statement`, `Trial Balance` as at period end, and `General Ledger Detail` for the GST control account(s). Use a demo or fabricated file if you are only trialling. Keep real client exports and generated workpapers only in a firm-approved location outside every repository checkout. Client data must not be kept in this repository.
3. In Claude Code, in the folder holding those exports, ask: 'Prepare a BAS workpaper for the quarter ended 31 March from these exports. Cash basis, quarterly lodger.' The `bas-preparation` skill picks this up and asks for anything missing.
4. Verify the result yourself: check that net GST on the workpaper (1A less 1B) ties to the movement in the GST control account for the period. If the workpaper shows that tie-out and lists its exceptions, it worked.

Ask the agent in natural language. Copy one of these:

```text
Prepare a BAS workpaper for the quarter ended 31 March from these exports. Cash basis, quarterly lodger. Tie 1A less 1B to the GST control account movement and list exceptions.
```

```text
Finalise STP for the year ended 30 June from this payroll register, GL detail, and STP reporting summary. Reconcile register to GL and register to STP by employee. Do not compute an SGC charge.
```

```text
Use workpaper-tie-out on this year-end pack. Every statement line needs a source. Carry unresolved differences; do not smooth them.
```

Uninstall with `/plugin uninstall australian-accounting-skills@ryanduguid` (or delete the copied folders from `~/.claude/skills/` if you installed by hand).

## Worked example: bas-preparation

**Input.** A quarterly BAS for a small company on the cash basis. You supply the activity statement, the trial balance, general ledger detail for the GST control accounts, prior period BAS figures, and the payroll activity summary. Xero report names for each are in the `xero-exports` skill.

**What the skill checks.** It confirms the report basis matches the entity's ATO registration basis first, and stops and flags a mismatch rather than continuing. It maps ledger figures only to the labels actually present on the entity's statement (it will not invent a W1 just because payroll data exists; large withholders reporting through STP may not need one). It ties net GST (1A less 1B) to the movement in the GST control account to the cent, using the cash-basis bridge where the ledger is on accruals. It scans for coding exceptions such as GST claimed on bank fees, stamp duty or wages, and compares each label to the prior period and same period last year, asking you for the firm's variance threshold rather than inventing one.

**Output and escalation.** A review-ready workpaper: summary page with labels, amounts and tie-out proof, an exceptions list with resolutions, preparer and date, and space for reviewer sign-off. It does not lodge and does not draft ATO correspondence; that stays with the registered agent. If it cannot verify a current rate or label at ato.gov.au, it stops, asks you for the figure, records it as 'per [name], [date], unverified', and flags it on the workpaper.
