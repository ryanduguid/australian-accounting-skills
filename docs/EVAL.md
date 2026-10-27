# Evaluating the skills

How to run the fabricated validation cards against a model by hand and record
the outcome. The cards in `validation/cases/` are the test set; the passing
standard is in [validation/README.md](../validation/README.md). Nothing in
this repository calls a model, and nothing here changes a skill.

This method supplies the whole card, including its required checks and
prohibitions. It measures adherence to visible instructions, not whether the
model discovers an error without that guidance. Describe results on that basis.
An evaluation of independent error detection would need a separate task-only
input and a withheld grading rubric. Its results would not be directly
comparable with these runs.

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

Write one file per record as `validation/results/YYYY-MM-DD-<slug>.json` in the
shape of [validation/results.schema.json](../validation/results.schema.json).
Existing records without `schema_version` retain this legacy shape.

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

A run may cover any subset of the cards. `results` is keyed by card ID, so a
card appears at most once. Only `pass` and `fail` are verdicts. Keep prompts,
outputs, transcripts and assessment notes in the firm-approved location
outside this repository. Never infer the input mode of a legacy record or add
provenance that was not recorded when it ran.

For new records, add `schema_version: 2`, `input_mode` (`task-only` or
`whole-card`), `status` and `provenance`. The common fields above remain
required. `runner` names the preparer or observer until a person confirms the
verdicts. For `confirmed`, it names that person. `run_date` is the date the
recorded stage completed and must match the filename. For preparation, name
the planned model, or use `unselected` if none has been chosen.

`provenance` maps each case ID to lower-case SHA-256 digests.

- `input_sha256`: the exact UTF-8 task bytes supplied or prepared for the model.
- `context_sha256`: the exact UTF-8 context manifest retained with the working
  evidence. It lists the loaded files and their byte hashes, the model and
  runtime, and available tools. Record unknown preparation settings explicitly
  and freeze the actual settings before observation.
- `rubric_sha256`: the exact UTF-8 full card bytes used for assessment.
- `output_sha256`: the exact UTF-8 response and tool-evidence artefact bytes.
  This field is required for observed and confirmed runs and forbidden for
  preparation.

Hash the retained bytes without normalising line endings. These digests bind a
record to retained evidence. Format validation cannot prove that the evidence
exists, that execution was complete or that a person reviewed it.

| Status | Meaning | `results` |
| --- | --- | --- |
| `prepared` | Inputs are frozen. No model observation is claimed. | Empty object |
| `observed` | A response exists. Assessment remains pending. | Empty object |
| `confirmed` | The named person has assessed every recorded case. | Exactly one verdict per provenance case |

Preserve earlier records when recording a later stage. Use a new filename with
a stage suffix. An incomplete execution can remain observed. It is not an
automatic behavioural failure. The validator reports each stage separately.

`scripts/validate_validation.py` reads every result file, rejects any other
key or verdict, any unknown or repeated card, a date that does not match the
file name, and the identifier patterns it screens the cards for. It also holds
the schema's card list to the card inventory and its verdict list to `pass`
and `fail`. For version 2 it checks the stage, digest fields and exact match
between confirmed verdicts and provenance cases. JSON Schema describes the
structure. The Python validator also enforces that cross-field match. Adding a
card means adding it to the schema in the same change. Stage new result files before running
the checker, as `validation/README.md` describes, because it verifies the
tracked inventory.

## Current evidence and rerun

The [8 September Codex run](../validation/results/2026-09-08-codex.json)
records 16 passes out of 17 cases, with `export-manifest-rounding` failing.
The contracting export skill now explicitly requires the timestamp, filters,
both totals, a documented rounding bridge and re-export after a filter change.
The existing verdict remains unchanged. The
[28 September whole-card run](../validation/results/2026-09-29-whole-card-confirmed.json)
reran all 70 current cards, this one included, at skills commit f4acd41,
and Ryan Duguid confirmed a pass for each on 29 September 2026. Skills
changed after f4acd41 only in link targets. The
`au-client-acceptance-missing-evidence` and
`au-working-holiday-makers-missing-evidence` cards, added afterwards for
v0.3.1, were each run whole on 1 and 4 October 2026 and confirmed as passes
on 4 October
([client acceptance](../validation/results/2026-10-04-client-acceptance-confirmed.json),
[working holiday makers](../validation/results/2026-10-04-working-holiday-makers-confirmed.json)).
The four core failure cards also added for v0.3.1 have no recorded whole-card run.
The `au-short-stay-accommodation-missing-evidence` and
`au-short-stay-accommodation-platform-gst-registration` cards and the
`au-capital-gains-contract-straddles-reform` card, added for v0.5.0, have no recorded whole-card run,
nor do the 3 `au-pre-lodgement-review` cards or the 2 `reconciliation-break-trace` cards. The v0.5.0 figure replacements
changed the wording of au-payg-instalment-variation, au-super-contribution-caps,
bas-preparation and contractor-super-tpar, so their cards need a rerun.

When a skill's wording changes, rerun its cards at the exact revised commit,
using the process above. Preserve the 12-cent exception and missing evidence
in `export-manifest-rounding`.

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
outside the result records until the person judging the run confirms them.

The [21 October niche-topic observations](../validation/results/2026-10-21-niche-tax-task-only-observed.json)
cover 12 task-only cases at b9de775, including positive SAPTO, DSSP and AMIT
preparation. The initial mixed-plan DSSP response omitted supported conditional
monetary bridges. After clarifying that workflow, both DSSP cases were
[observed again](../validation/results/2026-10-21-niche-tax-dssp-rerun-observed.json)
at 3bc5d13. The original observations are retained. All records remain observed,
with no human-confirmed verdicts; the confirmed-card count is unchanged.

Review against the 2025-26 ATO rebate-income worksheet then identified missing
FHSS and fringe-benefit employer-class inputs in the SAPTO workflow and positive
fixture. That initial positive observation does not establish a fully supported
rebate-income bridge. The workflow and fixture now distinguish those inputs,
with separate provisional section 57A, FHSS and unknown-class comparisons.
[Both SAPTO cards were observed again](../validation/results/2026-10-21-niche-tax-sapto-rerun-observed.json)
at efe1af8. Earlier records and frozen evidence remain unchanged. There are 16
observations across these 12 cases, with no human-confirmed verdicts.

These trials used fresh ephemeral Codex CLI sessions with `gpt-6.1-sol`, high
reasoning effort, inline target-skill material and task sections only. Rubrics
were withheld. Web search was disabled, user MCP configuration was excluded
and the instructions prohibited tools. The retained traces show no tool calls.
This establishes neither operating-system read isolation nor source retrieval
or restraint with consequential action tools. No baseline comparison or
performance improvement is claimed. Each record binds the exact frozen skill
and card bytes to the stated commit; those bytes were checked against Git
after execution. Human source approval remains pending.

## Task-only trials

Prepare a frozen packet outside the checkout with the existing card and exact
skill-file digests:

```bash
python scripts/prepare_trial.py month-end-mismatched-period ../trial-month-end --model unselected --runtime unselected
```

The new directory contains `input.md`, `context.json` and the withheld
`rubric.md`. Supply only `input.md` and the target skills to the evaluated
session; keep the rubric outside its accessible context. Preparation does not
call a model, prove isolation or record a verdict. Before observation, replace
the planned model/runtime and tool-availability note with the actual settings,
freeze that context and retain its exact bytes. The helper refuses an existing
destination and repository-local evidence, preserving earlier runs.

To test whether a model identifies the checks without seeing their answers,
prepare a separate task-only trial. Give it the target skills and only these
card sections: `Scenario`, `Task`, `Synthetic inputs` and `Deliberately
unavailable evidence`. Withhold `Required checks`, `Must not do` and
`Source-verification and reviewer boundary` until assessment. The loaded
skills still supply their normal safety and review instructions.

Freeze the exact card and skill bytes before running. Keep their hashes, the
model input and the full assessment rubric outside this repository, alongside
the runtime and tool-availability record. Check that the task contains no
grading answers. Give each case a fresh session and keep the assessment files
out of its accessible context.

Assess useful completed work as well as retained exceptions. A blanket refusal
fails a case that requires supported arithmetic. Keep incomplete execution
separate from a behavioural failure, and require a person to confirm any
proposed verdict after reading the whole response and available tool evidence.

These trials measure a different condition from the historical whole-card
runs. Record them with version 2 and `input_mode: task-only`, retaining the
working evidence separately. Do not pool their verdicts with whole-card or
legacy records. A prepared trial is not a model observation or a confirmed
result.

The [17 October task-only observations](../validation/results/2026-10-17-task-only-observed.json)
cover 29 cards at edcbaa9 using GPT-6.1 Sol in fresh Codex sessions, including
10 separate single-skill invocations for the standalone card, for 38 responses.
Exact packets, outputs and independent proposed assessments are retained
outside the repository. Linked supporting files read by some sessions extend
the declared target folders; a later manifest records those self-reported reads.
No runtime tool trace or OS isolation was established. Web and action tools
were excluded by instruction, so live retrieval and action restraint remain
untested. Every human verdict is pending; the confirmed-result count remains 72.

## Boundary

A recorded pass says a model handled a fabricated scenario within the
workflow's controls on one day. It does not say the model gives correct tax
outcomes, and it does not stand in for the authorised human review every
skill requires.
