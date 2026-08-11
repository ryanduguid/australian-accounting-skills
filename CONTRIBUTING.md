# Contributing

These skills describe how an agent should work through an Australian accounting task. They encode workflow and tie-out discipline. They are not tax advice and must not read as a substitute for professional judgement.

## Data boundary

- No client data, ever. The `.gitignore` blocks `input/`, `output/`, `clients/`, `exports/` and every common export extension, including `.aba`, `.myox`, `.ofx` and `.qif`.
- Examples must be fabricated. A realistic-looking entity name, ABN or balance set drawn from real work is still client data.

## Writing a skill

- Send the agent to the primary source for anything that changes: rates, thresholds, benchmark interest, label numbers, lodgement dates. Hardcoding a current-year figure guarantees the skill is wrong next year and silent about it.
- Every step must be reachable from the inputs the skill actually asks for. A step that needs a payroll report, a balance sheet, or a payment history the skill never requested is a broken skill, not a thorough one.
- Keep the scope fence visible: state what the skill will not decide, and where a human has to sign off.
- Prefer a tie-out to an assertion. If a step produces a number, say what it must agree with.

## Local verification

Python 3.10 or newer, standard library only.

```bash
python -m unittest discover -s tests -v
```

The suite checks skill metadata and structure. Add a test when a change introduces a rule a reader could get wrong.

## Pull requests

Cite the provision, ruling or ATO page behind any technical change, and give its date. If a change alters a rule, search for every other place that states or polices it. The same rule is often repeated in a checklist, a tie-out and a worked example.

For a potential security vulnerability, follow [SECURITY.md](SECURITY.md) rather than opening an issue.
