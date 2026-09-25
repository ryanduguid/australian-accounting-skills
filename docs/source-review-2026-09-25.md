# Primary source retrieval, 25 September 2026

Refreshed the priority source records for BAS, month-end close, thirteen-week cash
flow, STP finalisation, payroll review and WIP. Retrieval gaps now affect 5 skills,
down from 10. All 4 existing flags for a source changed since human review remain.

This is machine retrieval evidence. The source titles, URLs, facts, periods and
`checked_at` dates are unchanged. Under `AGENTS.md`, only a person can advance a
human review date. A successful retrieval does not approve a workflow or establish
that its interpretation is current.

## Retrieval method and results

The existing `scripts/source_refresh.py --skill bas-preparation --write` command
retrieved all 5 BAS pages. Their readable-text digests were unchanged. The
[How GST works page](https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/how-gst-works)
still records a 14 September 2026 source update after its 19 August review.

Local direct requests for the Payday Super and Fair Work pages timed out. Firecrawl
retrieved fresh raw HTML with `maxAge=0` and `onlyMainContent=false` for those pages
and the two NSW sources below. Each returned HTTP 200 at its indexed URL.

| Source | Affected skills | Recorded readable-text SHA-256 |
| --- | --- | --- |
| [ATO Payday Super](https://softwaredevelopers.ato.gov.au/PaydaySuper) | `month-end-close`, `cashflow-forecast-13week`, `stp-finalisation` | `6f8cc3ad8db5c51a1441d965a6e6a6bce4a03301f09c7ed1d14f3b7b95bb014f` |
| [Fair Work record-keeping and pay slips](https://www.fairwork.gov.au/tools-and-resources/fact-sheets/rights-and-obligations/record-keeping-pay-slips) | `au-payroll-review` | `0fdc36b69cd47019ea5915e9a782685720efc96c29d93a2180828586e41441b6` |
| [NSW Security of Payment Regulation 2020](https://legislation.nsw.gov.au/view/whole/html/inforce/current/sl-2020-0504) | `wip-over-under-billing` | `1eebc91163117f00141762f3092c69cae155d68db2af8f301678306c8d9a13ae` |
| [NSW Security of Payment Act 1999](https://legislation.nsw.gov.au/view/whole/html/inforce/current/act-1999-046) | `wip-over-under-billing` | `e641988ac70bc2068fc9b355c3a0de11259943ac469567568ab05b027b69c196` |

The captured HTML was passed through the repository's existing `body_digest` and
`upstream_last_modified` functions, then `apply_fetch` updated only machine-owned
fields. These are HTML digests, not hashes of Firecrawl's Markdown. No new source
refresh dependency or automated fallback was added. The parser found no supported
last-modified value in those four responses, so none was invented.

The six records now describe successful retrieval through Firecrawl. This does not
prove the direct-fetch CI job can reach those hosts. A later sweep may report a
transport failure again; retain that result and use an approved browser to inspect
the source before relying on it.

## First-pass review work

`coverage.json` was regenerated from the source records. The five remaining skills
with retrieval gaps are outside this priority set. Human review remains pending for
the changed sources in `bas-preparation`, `au-gst-registration-review`,
`au-partnership-tax` and `au-return-amendment`.

The first retrieval pass changed no skill instructions, validation cards or
model-run results. No new model evaluation or human source review was claimed.

## Follow-up retrieval

The later pass on 25 September checked the remaining ten failed source records
across five skills. Four distinct pages were retrieved through Firecrawl with
`rawHtml`, `maxAge=0` and `onlyMainContent=false`. The two NSW Security of Payment
captures above were reused from the same day's successful retrieval.

| Skill | Records updated |
| --- | ---: |
| au-payroll-tax-states | 2 |
| payroll-tax-contractors | 3 |
| plant-and-equipment-costing | 1 |
| progress-claim-preparation | 2 |
| retention-schedule | 2 |

The first NSW Payroll Tax Act and Federal Register responses contained only page
shells despite HTTP 200. Those bodies were rejected. A second capture with
`waitFor=5000` contained the legislative text and supplied the recorded digest.
The three payroll-contractor URLs share one page and differ only by fragment;
their indexed URLs remain unchanged.

Every updated record now has HTTP 200 and an HTML digest computed through the
existing canonicaliser. The coverage register has zero recorded retrieval
failures. This is a targeted refresh of failed records, not a fresh retrieval of
all 123 sources or proof that the direct-fetch CI job can reach them.

All human-owned fields, including `checked_at`, facts and limitations, remain
unchanged in these ten records. The four changed-source review flags above remain
open. Retrieval does not establish legal correctness, the applicable historical
version or human review. The two new validation cards are separate preparation
work described in [EVAL.md](EVAL.md); neither has a confirmed model result.
