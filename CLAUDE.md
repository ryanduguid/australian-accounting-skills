# Australian Accounting Skills contributor guide

This repository contains reusable workflow skills for Australian
public-practice accounting. It is source code and documentation, not a client
workpaper store and not a substitute for a firm's own instructions.

## Scope and data

- Keep real client data, exports, workpapers, names, addresses, TFNs, ABNs,
  bank details and credentials out of this repository, examples, fixtures,
  commits and unapproved cloud use.
- A firm may process full-fidelity data only in its approved environment and
  under its engagement, privacy and retention policies. De-identify by default
  and retain only the identifiers the task requires.
- Put generated client output only in the firm-approved secure location. If no
  location is configured, ask before creating a repo-adjacent path. Do not
  change `.gitignore`, output locations or repository configuration to
  accommodate a generated workpaper without explicit user approval.

## Accuracy and professional boundaries

- Skills encode workflows, reconciliation checks and escalation points. They
  do not provide tax, legal, financial, HR or assurance conclusions.
- Do not state current rates, thresholds, labels, due dates, administrative
  positions or software behaviour from memory. Verify an authoritative source
  at use time.
- For mutable facts, record the source title, direct URL, check date, relevant
  period and exact fact relied on. Mark an unavailable source or user-supplied
  figure as unverified.
- Agents prepare and check. Authorised humans decide, communicate, sign, post,
  lock, pay, declare and lodge.

## Maintaining skills

- Keep every `SKILL.md` self-contained enough for individual installation,
  including its inputs, checks, privacy reminder and escalation boundary.
- Prefer workflow controls over hard-coded tax content. Link to a current
  authoritative source or require live verification for mutable rules.
- Use fabricated-from-scratch fixtures. Never add a de-identified or redacted
  client export as a regression example.

## Before hand-off

- Review the requested scope, diff, local links, cross-skill references and
  privacy risks.
- Run `python -m unittest discover -s tests -v`,
  `python scripts/validate_validation.py`, and `git diff --check`.
- State any relevant validation that was not run and why.
