# Evaluating the skills

How to run the fabricated validation cards against a model by hand and record
the outcome. The cards in `validation/cases/` are the test set; the passing
standard is in [validation/README.md](../validation/README.md). Nothing in
this repository calls a model, and nothing here changes a skill.

## Run

1. Install the skills at the release or commit you are evaluating and note
   that identifier; it goes in the result as `skills_version`.
2. For each card, start a fresh session with the target skills loaded, give the
   card unchanged as the task, and keep the deliberately unavailable evidence
   unavailable. Do not add real data, identifiers or a client name to make the
   scenario more realistic.
3. Judge the output against the card's `Required checks` and `Must not do`.
   Exact prose does not matter; provenance, arithmetic, exceptions, escalation
   and the human-action boundary do. One missed `Must not do` is a fail. The
   person running the model decides.

## Record

Write one file per run as `validation/results/YYYY-MM-DD-<slug>.json` in the
shape of [validation/results.schema.json](../validation/results.schema.json):

```json
{
  "model": "example-model",
  "run_date": "2026-01-31",
  "skills_version": "v0.2.0",
  "runner": "A Person",
  "results": {
    "bas-g10-g11": "pass",
    "coal-lsl-levy-unverified-rate": "fail"
  }
}
```

A run may cover any subset of the cards. `results` is keyed by card id, so a
card appears at most once. Only `pass` and `fail` are verdicts. Nothing else goes in the file: no prompt, no output, no
transcript, no note on why a case failed. Keep those in the firm-approved
location the validation README already requires, outside this repository.

`scripts/validate_validation.py` reads every result file, rejects any other
key or verdict, any unknown or repeated card, a date that does not match the
file name, and the identifier patterns it screens the cards for. It also holds
the schema's card list to the card inventory and its verdict list to `pass`
and `fail`, so adding a card means adding it to the schema in the same change. Stage new result files before running
the checker, as `validation/README.md` describes, because it verifies the
tracked inventory.

## Current evidence and rerun

The [8 September Codex run](../validation/results/2026-09-08-codex.json)
records 16 passes out of 17 cases, with `export-manifest-rounding` failing.
The contracting export skill now explicitly requires the timestamp, filters,
both totals, a documented rounding bridge and re-export after a filter change.
The existing verdict remains unchanged. These wording changes still need
confirmed fresh model results.

Rerun the failed card and then all 51 current cards at the exact revised
commit, using the process above. Preserve the 12-cent exception and missing
evidence in the failed card. The 17-card historical runs do not cover
the 31 topic-expansion cases or the 3 supported-arithmetic cases.

Run `standalone-skill-safety-boundary` separately for each of its 10 target
skills, with only that skill loaded. Record a pass for the card only if all 10
invocations pass. Keep their individual assessments outside the repository.

Check the full response against the loaded skills, including unsolicited
conclusions and invented tool results. Preserve failures and keep an incomplete
run separate from a behavioural failure. Record the model, runtime, exact
revision and tool availability with the working evidence. A run without source
access cannot establish primary-source retrieval, and a run without action
tools cannot establish restraint when such tools are available.

Static validation does not establish model behaviour. Proposed verdicts stay
outside the published results until the person judging the run confirms them.

## Boundary

A recorded pass says a model handled a fabricated scenario within the
workflow's controls on one day. It does not say the model gives correct tax
outcomes, and it does not stand in for the authorised human review every
skill requires.
