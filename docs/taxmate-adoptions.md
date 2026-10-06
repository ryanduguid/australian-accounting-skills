# TaxMate comparison and adoptions

Ten existing accounting skills now ask for more precise intake evidence and keep it traceable through reviewer handoff. The changes were informed by TaxMate Australia and written independently for this repository.

Comparison date: 6 October 2026. TaxMate source tree: `42ba67d458439e7882a3e8e0d76bfa6efdecbad7`. Accounting-skills base: `90dd293069df2b6b6a38f04f9fbb18526cbcd66d`. The source inventory, relevant runtime modules, topic guidance, manifests and handoff tests were inspected. This is a scoped reuse assessment, not a full upstream security or correctness audit.

## Applied here

| Skill | Added control |
| --- | --- |
| `au-individual-return` | Distinguish zero, no, unknown and omitted facts; preserve conflicting answers; require document checks for AI extraction; reconcile statement components and aggregates; link evidence and review lists by item reference; verify return destinations separately from supporting topic sources. |
| `au-medicare-review` | Keep each insurer statement line and code separate, preserve zero values, distinguish partial-year cover, minimise policy identifiers and keep family facts separate from statement facts. |
| `au-wfh-deductions` | Separate service bills from device costs and identify employer-paid or reimbursed amounts and overlap with business/GST workpapers. |
| `au-capital-gains` | Reuse event references across asset schedules and collect main-residence periods, spouse choices and missing valuations as review facts. |
| `au-company-tax` | Keep company and shareholder facts separate and collect dividend, loan and benefit evidence for the existing review workflows. |
| `au-trust-distributions` | Preserve beneficiary component schedules and reconcile them separately from cash, trustee records and managed-fund statements. |
| `au-partnership-tax` | Link each partner statement to the agreement and period, keep components separate from drawings and flag GST/BAS overlap and PSI questions. |
| `au-super-contribution-caps` | Keep contribution, proposed deduction, notice of intent and fund acknowledgement evidence distinct. |
| `au-rental-property` | Link property, owner, cost and disposal references while retaining availability and private-use evidence. |
| `au-sole-trader` | Carry business and BAS periods, reporting basis and expense references through the return bridge, retaining duplicate-cost and evidence questions. |

The individual-return and Medicare acceptance examples now include conflicting answers, provisional extraction, supplied zeros, multiple insurer lines and partial cover. They are documented scenarios; no new model run is claimed.

TaxMate's [individual-return workflow](https://github.com/nijanthan-dev/taxmate-australia/blob/42ba67d458439e7882a3e8e0d76bfa6efdecbad7/skills/individual-return/SKILL.md), [intake module](https://github.com/nijanthan-dev/taxmate-australia/blob/42ba67d458439e7882a3e8e0d76bfa6efdecbad7/scripts/taxmate_intake.py), [entity routing](https://github.com/nijanthan-dev/taxmate-australia/blob/42ba67d458439e7882a3e8e0d76bfa6efdecbad7/scripts/taxmate_entity_routing.py), [entity worksheets](https://github.com/nijanthan-dev/taxmate-australia/blob/42ba67d458439e7882a3e8e0d76bfa6efdecbad7/scripts/taxmate_entity_worksheet.py) and [handoff contract](https://github.com/nijanthan-dev/taxmate-australia/blob/42ba67d458439e7882a3e8e0d76bfa6efdecbad7/scripts/taxmate_handoff.py) informed these controls. Its [private-health guidance](https://github.com/nijanthan-dev/taxmate-australia/blob/42ba67d458439e7882a3e8e0d76bfa6efdecbad7/skills/private-health-medicare/references/rules.md) informed the statement-line review.

## Existing owners and reuse decisions

| TaxMate pattern | Decision |
| --- | --- |
| Source retrieval dates, content digests and change reports | Already owned by `scripts/source_refresh.py` in this repository and the compilation-currency checks in `llm-tax-guardrails`. Retain the distinction between retrieval and human review. |
| Capability/source/test coverage | Already derived by `scripts/build_coverage.py` and checked against `coverage.json`. TaxMate's runtime coverage manifest does not justify a second matrix here. |
| Pre-commit checks matching CI | Already enforced here by `.pre-commit-config.yaml` and contributor-check tests. |
| Secret and client-identifier scanning | Already configured here and in `llm-tax-guardrails` with gitleaks. |
| Calculators and financial CSV classification | Keep the maintained engines in `australian-accounting` and the existing Ozzit functions. TaxMate's rates, period limits and transaction heuristics are not an interchangeable calculation contract. |
| Source indexing and provenance | Keep `au-tax-legislation-corpus` and TaxJarvis source-admission boundaries. An ATO prep source pack does not establish legislative effect or a verified publication. |
| MCP/plugin packaging and portable guidance | Existing accounting MCP and skills packaging already own these interfaces. Adding another launcher would duplicate delivery paths. |
| HTML guides and CSV workbook export | TaxMate supplies a renderer tied to its own intake and destination models. No existing renderer gap was established by this assessment. The row context and separate evidence/review lists were adopted as workflow output requirements. |
| CSV formula neutralisation | Identified in TaxMate's export module. No new CSV writer is added by this change; any future exporter needs its own boundary checks and regression cases. |
| Job tracker functionality | Koal's job workflow has no demonstrated TaxMate integration requirement. Tax-prep fields should stay with the workpaper owner. |

The earlier source-freshness adoption task records the September integration into accounting skills and tax guardrails. Current local owners were inspected before selecting new work. Other repositories received a fit assessment only; their full current implementations were not audited in this change.

## Licence and verification

TaxMate publishes an [Apache 2.0 licence](https://github.com/nijanthan-dev/taxmate-australia/blob/42ba67d458439e7882a3e8e0d76bfa6efdecbad7/LICENSE) and a [NOTICE](https://github.com/nijanthan-dev/taxmate-australia/blob/42ba67d458439e7882a3e8e0d76bfa6efdecbad7/NOTICE) identifying separate rights in cached ATO material. This change adds original workflow text under this repository's existing licence. Source code, generated topic bodies, cached ATO text and tax tables were not imported. The provenance record is in `NOTICE`.

Local verification on Python 3.14.7: Ruff 0.16.6 passed; mypy 2.3.1 passed on 25 source files; all 220 unittest tests passed; validation passed for 76 fabricated cards and 65 skills; Skills CLI 1.5.22 discovered all 65 skills; the coverage check passed. Whitespace and final scope checks passed.

These checks verify repository structure and existing gates. New instructions have not been evaluated in a fresh agent session. The Python 3.11, 3.12 and 3.13 CI matrix, GitHub-hosted checks and full-history gitleaks were not rerun locally. Aikido is skipped because only documentation changed. No source sweep or current-law verification was performed: this change adds evidence controls and no new tax rules or rates.
