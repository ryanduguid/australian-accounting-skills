# Contributing

These skills describe how an agent should work through an Australian accounting task. They encode workflow and tie-out discipline, and they stop where professional judgement starts. Nothing here is tax advice.

## Data boundary

- Keep client data out of the repository. The `.gitignore` blocks `input/`, `output/`, `clients/`, `exports/` and the common export extensions, including `.aba`, `.myox`, `.ofx` and `.qif`.
- Fabricate your examples. An entity name, ABN or balance set lifted from real work is client data however realistic it looks.

## Writing a skill

- Send the agent to the primary source for anything that changes: rates, thresholds, benchmark interest, label numbers, lodgement dates. Hardcode a current-year figure and the skill goes wrong next year without saying so.
- Reach every step from the inputs the skill asks for. A step that needs a payroll report, a balance sheet or a payment history the skill never requested is broken rather than thorough.
- Keep the scope fence visible. State what the skill declines to decide, and where a human signs off.
- Prefer a tie-out to an assertion. If a step produces a number, say what that number must agree with.

## Local verification

Python 3.10 or newer, standard library only.

```bash
python -m unittest discover -s tests -v
```

The suite checks skill metadata and structure. Add a test when your change introduces a rule a reader could get wrong.

## Pull requests

Cite the provision, ruling or ATO page behind any technical change, and give its date. When you alter a rule, search for every other place that states or polices it. The same rule tends to appear in a checklist, a tie-out and a worked example.

For a potential security vulnerability, follow [SECURITY.md](SECURITY.md) rather than opening an issue.
