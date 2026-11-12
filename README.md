<p align="center">
  <picture>
    <source media="(max-width: 600px) and (prefers-color-scheme: light)" srcset=".github/assets/banner-phone-light.svg">
    <source media="(max-width: 600px)" srcset=".github/assets/banner-phone.svg">
    <source media="(prefers-color-scheme: light)" srcset=".github/assets/banner-light.svg">
    <img src=".github/assets/banner.svg" width="100%" alt="AU Skills. Review-ready BAS, close and payroll workpapers. Pixel art of a clipboard checklist beside the AU Skills wordmark in slab-serif block letters.">
  </picture>
</p>

<div align="center">

[![verify](https://github.com/ryanduguid/australian-accounting-skills/actions/workflows/verify.yml/badge.svg?branch=main)](https://github.com/ryanduguid/australian-accounting-skills/actions/workflows/verify.yml)
[![Codecov](https://codecov.io/gh/ryanduguid/australian-accounting-skills/graph/badge.svg)](https://codecov.io/gh/ryanduguid/australian-accounting-skills)
[![CodeQL](https://github.com/ryanduguid/australian-accounting-skills/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/ryanduguid/australian-accounting-skills/actions/workflows/codeql.yml)
[![SonarCloud](https://sonarcloud.io/api/project_badges/measure?project=ryanduguid_australian-accounting-skills&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=ryanduguid_australian-accounting-skills)
[![Codacy code quality](https://app.codacy.com/project/badge/Grade/b46694168d304886be1287d54cf33923)](https://app.codacy.com/gh/ryanduguid/australian-accounting-skills/dashboard)<br>
[![OpenSSF Scorecard](https://raw.githubusercontent.com/ryanduguid/.github/badges/ryanduguid/australian-accounting-skills.svg)](https://scorecard.dev/viewer/?uri=github.com/ryanduguid/australian-accounting-skills)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/15423/badge)](https://www.bestpractices.dev/projects/15423)
[![SLSA provenance](.github/assets/badges/slsa.svg)](https://github.com/ryanduguid/australian-accounting-skills/attestations)
[![VirusTotal](.github/assets/badges/virustotal.svg)](https://github.com/ryanduguid/australian-accounting-skills/releases/latest)<br>
[![release](https://img.shields.io/github/v/release/ryanduguid/australian-accounting-skills?label=release&color=66023C&labelColor=000000&style=flat)](https://github.com/ryanduguid/australian-accounting-skills/releases/latest)
[![licence: Ryan Duguid Public Attribution Licence 1.0](.github/assets/badges/licence.svg)](LICENSE)

[Install](#install) · [Start here](#start-here) · [First run](#first-run) · [Privacy](#privacy) · [Skill catalogue](docs/skill-catalogue.md) · [Validation](validation/README.md) · [Licence](#licence)

</div>

Australian Accounting Skills is a set of agent skills for Australian accountants and tax practitioners: BAS, month-end close, payroll, FBT, Division 7A, trusts, returns and practice compliance. An authorised human reviews, decides and lodges.

Each skill takes an agent through the workflow, sends it to current primary sources for anything that changes and ends in a review-ready workpaper. [Scope, limits and examples](https://duguid.com.au/tools/australian-tax-ai-agents/) are on the author's site.

v0.6.0 corrects 4 passages in v0.5.0, including a withdrawn GST ruling that `tax-invoice-review` cited: see [Corrections since v0.5.0](RELEASE_NOTES.md#corrections-since-v050).

## Install

Install the 107 workflows in the published release, [v0.6.0](https://github.com/ryanduguid/australian-accounting-skills/releases/tag/v0.6.0). Each command below was run on Linux on 12 November 2026 against the files this release tags.

Claude Code, as a plugin:

```bash
claude plugin marketplace add ryanduguid/australian-accounting-skills#v0.6.0
claude plugin install australian-accounting-skills@ryanduguid
```

Codex, as a plugin:

```bash
codex plugin marketplace add ryanduguid/australian-accounting-skills --ref v0.6.0
codex plugin add australian-accounting-skills@ryanduguid
```

Any agent that reads `SKILL.md`, from a separate project directory:

```bash
git clone --branch v0.6.0 --depth 1 https://github.com/ryanduguid/australian-accounting-skills.git accounting-skills-release
npx --yes skills@1.5.22 add ./accounting-skills-release --agent codex claude-code --skill '*' --yes --copy
```

That copies the 107 skills into the current project's Codex and Claude Code directories and leaves global installations alone. For OpenCode, use `--agent opencode`. To install one skill by name, use `--skill bas-preparation` in place of `--skill '*'`, which copied that skill alone when run on Linux on 12 November 2026. To use Claude.ai or the desktop app, [upload one skill at a time](docs/installation.md#claudeai-or-the-claude-desktop-app-without-a-terminal). [Installation](docs/installation.md) covers manual copying, removal and versioning.

Claude Code is the tested runtime. Codex packaging and portable skill files are included, and OpenCode has an install and discovery check only. None of this establishes testing in every agent runtime. The validation record under the fold gives the model runs and their limits.

## Start here

With the skills installed, use the prompts below to ask your agent to run the named skill.

```text
Use bas-preparation to prepare this quarter's BAS workpaper from the reports in this folder and show the GST control-account tie-out.
```

```text
Use month-end-close to run the close checklist for last month and list what is still open, with an owner for each item.
```

```text
Use au-tax-research to draft a file note on the question below, with each primary source, the version you read and the date you read it.
```

| Skill | Use it for |
| --- | --- |
| `bas-preparation` | BAS or IAS workpaper, GST coding review and label tie-out |
| `month-end-close` | Checklist-driven close: bank recs, control accounts, accruals and variances |
| `workpaper-tie-out` | Trace every statement line to its workpaper and source, and back |
| `xero-exports` | Specify and check the Xero reports the other skills read |
| `stp-finalisation` | STP year-end: payroll versus GL versus filed totals |
| `fbt-annual-workflow` | FBT year-end: benefits, declarations, gross-up and RFBA |
| `div7a-compliance` | Division 7A loan register and minimum repayments |
| `au-trust-distributions` | Trust distribution review pack |
| `au-individual-return` | Individual tax return workpaper: income, deductions and offsets traced to evidence |
| `au-tax-research` | File note with source status and alternative views |
| `cashflow-forecast-13week` | Rolling 13-week cashflow from bank balance and agings |

See [all 107 skills](docs/skill-catalogue.md), which include the 31 added since v0.5.0.

## First run

The first run is a synthetic BAS example, and the skills are prep-only workflow aids.

**Input:** a fabricated quarterly cash-basis BAS with GST collected of $4,400.00 and GST paid of $1,210.00, plus the matching GST control-account movement.

An agent runtime is required. Ask it to prepare the BAS workpaper from the supplied reports and show the GST control-account tie-out.

Follow the [first run and BAS walkthrough](docs/bas-walkthrough.md) for the complete example.

**Output:** net GST of $3,190.00 ties to the $3,190.00 movement, with exceptions retained and reviewer sign-off blank.

**Human decision:** Resolve the coding exceptions and confirm the reporting basis and evidence before signing off.

![Synthetic BAS workpaper showing a $3,190 GST tie-out and blank reviewer sign-off](assets/readme/bas-workpaper-synthetic.svg)

Skills specify the workflow and require current primary authority for mutable rates, thresholds, labels and due dates. Keep real client files in the firm's approved environment, outside this repository.

## Privacy

The skill folders hold Markdown and JSON files and no scripts, so the skills send nothing themselves. What leaves the machine depends on how you run them:

- **Your agent host** decides where the prompts, files and tool results it reads go. With a cloud model they normally reach the model provider, under your account's terms, and a client file the agent opens goes the same way, so check your host's configuration.
- **The bundled MCP server** ([`aus-accounting-mcp`](https://github.com/ryanduguid/australian-accounting/tree/main/apps/aus-accounting-mcp)) runs over stdio. At the pinned `aus-accounting-mcp` 0.6.0 (release commit [`f17bbb2`](https://github.com/ryanduguid/australian-accounting/commit/f17bbb2f920e3c11dac9810060a533c64e0e3be8)), its own code and its 5 pinned engines import no network library apart from `asyncio`, which its demo uses only to run an event loop (a scan of their Python files on 11 November 2026), and a Linux trace on 6 November 2026 saw 0 socket and 0 connect calls from its 12 calculation tools on fabricated valid arguments. The MCP SDK it runs on is not pinned (`mcp>=2.3.0,<3`, 2.3.0 that day) and depends on HTTP libraries, including `httpx2`, `starlette` and `uvicorn`; the scan did not cover it. Its 8 corpus tools were not traced on a corpus. The trace's method and output are not published, so it cannot be rerun from this repository. Your host handles its tool arguments and results as above. The plugin builds it with `uvx` from that commit on first start; the wheel built there matched the PyPI 0.6.0 wheel file for file apart from its `RECORD` and `WHEEL` metadata (13 November 2026).
- **A local program a skill names** is installed separately and is not part of this repository. A skill tells the agent to run one only when it is already installed: `review-ready` in `bas-preparation`, `month-end-close`, `workpaper-tie-out` and `year-end-workpapers`; `close-control` in `month-end-close`; `aasb-corpus` in `au-financial-statements` and `wip-over-under-billing`; `wip-tally` in `wip-over-under-billing`; `fadden` in `au-tax-research`; and the `xero_aged_receivables.py` verifier in `xero-exports`. `solomons-sword` in `au-trust-distributions`, `the-exchequer-tally` in `au-franking-account` and `payday-super-check` in `stp-finalisation` are offered as optional checks without a condition that they be installed first. `xero-trial-balance-export` in `xero-exports`, for an operator who already has a Xero OAuth app, requests the trial balance from Xero's API. `month-end-close` gives the operator a `cargo install` command that builds `close-control` from a checkout, and `wip-over-under-billing` one that builds `wip-tally` from a pinned commit once installation is approved; both download crates. Each program's own code decides what it reads and sends.
- **A ledger connector** adds whatever the vendor's service handles. Use the [read-only connector route](.claude/skills/xero-exports/SKILL.md#read-only-connector-route) for Xero.
- **Installing** contacts GitHub and, with `npx skills`, the npm registry. That CLI collects anonymous usage data unless `DISABLE_TELEMETRY` or `DO_NOT_TRACK` is set.
- **The source preflight** fetches public pages from its allowlisted hosts and sends no client data.

**Human review pending:** an agent read the sources below on 6 November 2026, not a human review.

A registered tax or BAS agent must not disclose a client's information to a third party without the client's permission unless there is a legal duty. [TPB(GS) 55/2026](https://www.tpb.gov.au/tpbgs-552026-use-artificial-intelligence-and-code-professional-conduct) says that entering client information into an AI tool can be such a disclosure, depending on how the tool is configured and used, and that each client's permission is needed first (paragraph 23).

From 10 December 2026, Australian Privacy Principle (APP) 1.7 requires an APP entity's privacy policy to state the kinds of personal information used and the kinds of decisions involved, but only if the entity has arranged for a computer program to make a decision, or do a thing substantially and directly related to making one, the decision could reasonably be expected to significantly affect an individual's rights or interests, and personal information about that individual is used in the program's operation ([*Privacy and Other Legislation Amendment Act 2024*, Schedule 1, Part 15](https://www.legislation.gov.au/C2024A00128/asmade/text)). It covers decisions made after that date, whenever the program was arranged. A human reviewing the output does not by itself take a decision out of scope ([OAIC APP Guidelines, chapter 1](https://www.oaic.gov.au/privacy/australian-privacy-principles/australian-privacy-principles-guidelines/chapter-1-app-1-open-and-transparent-management-of-personal-information), paragraph 1.41, updated 30 September 2026). Whether a firm is an APP entity and meets that condition is for the firm to decide.

## Alternatives

Australian Accounting Skills is preparation-only and written for Australian practice. The
[Ask Nagaris comparison](docs/nagaris-comparison.md) records topic-by-topic decisions as at
2 November 2026. As read on 5 November 2026, these packs cover nearby ground:

- [openaccountants/openaccountants](https://github.com/openaccountants/openaccountants): a broad
  multi-jurisdiction pack under AGPL-3.0, to which Ryan Duguid contributes.
- [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins): official
  finance and small-business plugins. The `small-business` plugin declares Xero and MYOB connectors. At
  [commit d900840](https://github.com/anthropics/knowledge-work-plugins/blob/d900840/small-business/skills/tax-prep/SKILL.md),
  its `tax-prep` skill documents US federal calculations, not BAS preparation.
- [darrentmorgan/au-accounting](https://github.com/darrentmorgan/au-accounting): MIT-licensed
  Australian calculators with refusal codes.
- [adoptai/cpa-skills](https://github.com/adoptai/cpa-skills): US-framed skills that ship Python scripts.

<details>
<summary>Validation record, corrections, development installation and guides</summary>

## Validation record

Human-confirmed model verdicts cover 95 of the 235 [validation cards](validation/README.md). Claude Opus 5.5 passed all 70 cards then current in a whole-card run on 28 September 2026, confirmed on 29 September, and passed the `au-client-acceptance` and `au-working-holiday-makers` cards in single-card runs on 1 and 4 October, confirmed on 4 October. Earlier, Claude Opus 5 passed the 17 cards then current on 6 September and gpt-6-astra through Codex passed 16 of 17 on 8 September. Neither of those records states its input mode. Claude Opus 5.5 also passed the 23 cards added on 2 November 2026 in task-only runs that day, which withheld each card's required checks, prohibitions and source boundary; Opus judges proposed the verdicts and Ryan Duguid confirmed a pass for each the same day. Two of the 28 September passes, for `au-financial-statements-missing-evidence` and `wip-cost-to-complete-gap`, were given on earlier versions of those cards, which changed on 19 October 2026, so [How each skill was verified](docs/skill-verification.md) counts 93 cards with a confirmed pass on the current card and lists those 2 under a non-current digest.

The [evaluation guide](docs/EVAL.md) supplies the whole card, including its required checks, so read these results as adherence to visible instructions, not independent error detection. The 28 September run could read only each card and its skills, so it does not show source retrieval or restraint with action tools. Most confirmed verdicts also predate the current skill wording: on 11 November 2026, for 73 of the 95 cards, the `SKILL.md` or references of a skill the card names in its `target_skills` had changed beyond copyright and licence lines between the commit its confirmed run recorded and `main`, so those verdicts describe the earlier wording.

The other 140 cards have no confirmed model verdict: the duplicate-export, mismatched-period, stale-workpaper, debtor-summary, source-quotation, receipt-conflict, statement-revision, completion-evidence, 3 transaction-GST cases, 2 short-stay accommodation cases, 3 pre-lodgement review cases, a CGT contract-timing case, business selection, template output, a rental-agent balance bridge, a formula-change case, 2 reconciliation break-trace cases, GST screening leads, lodged-figure drift, a close with prior review points, 2 close-control cases, a card statement in credit across a year end, an employee master-data screen, a family trust distribution tax screen, 11 payroll tax cases, an AASB 18 comparative-year case, 3 AML/CTF beneficial owner cases, 2 BAS import GST cases, a two-way workpaper tie-out case, 4 cases for the client departure, trust loss, ATO correspondence and ATO account workflows, 2 FBT cases covering the line register and car valuation records, a professional-body obligations case, 7 land tax cases, 8 transfer duty cases, 2 Xero connector cases, a tax invoice threshold case, 7 planted-instruction and 7 altered or forged document cases with 2 positive controls for ordinary payment terms and an explained timing difference, 3 cases for SMSF death benefits, private company dividend preparation and a family trust election, 2 farm land GST and farm succession cases, 2 main residence and 3 share buy-back cases, 2 client meeting file note cases, 2 MYOB export cases, 3 marketplace settlement cases, 2 client letter cases, 2 client email triage cases, 2 CPI rent review cases, 4 client request draft cases and a 3-year analytical review case, 3 cases for an accounting depreciation schedule, a management report and a three-way forecast, 3 cases for a partnership agreement abstract, a Budget measure screen and a draft remission request, 3 cases for a practice's AML/CTF rows, an ATO client list reconciliation and a trust resolution content schedule, a positive control for 2 suppliers sharing an invoice number, and 12 niche tax cases covering PSI/PSB, SAPTO, DSSP/DRP, ESS, AMIT, non-commercial losses, foreign pensions, arrears and the small business income offset. Static checks cover all 107 skills, and [coverage.json](coverage.json) gives the state of each skill; [How each skill was verified](docs/skill-verification.md) shows it as one table of sources, review dates, cards and confirmed verdicts.

## Corrections to v0.2.1

v0.3.0 corrects passages that v0.2.1 carried in `bas-preparation`, `fuel-tax-credits`, `coal-lsl-levy`, `plant-and-equipment-costing`, `contractor-super-tpar`, `payroll-tax-contractors`, `progress-claim-preparation`, `retention-schedule`, `xero-exports` and `wip-over-under-billing`, and unsourced statements in `cashflow-forecast-13week` and `stp-finalisation`. [Corrections since v0.2.1](RELEASE_NOTES.md#corrections-since-v021) lists each with its pull request. Check an affected passage against it before relying on v0.2.1.

## Runtime and release

A development installation tracks the default branch, and a citation names the published release.

### Development installation

The marketplace added without a tag resolves the default branch, which can be ahead of v0.6.0. It is not a published release.

```
/plugin marketplace add ryanduguid/australian-accounting-skills
/plugin install australian-accounting-skills@ryanduguid
```

At v0.6.0 the default branch holds the same 107 workflows; later changes land there first. See the [Australian topic coverage map](docs/au-guide-coverage.md) for the additions and verification limits, and [Installation](docs/installation.md) for the Hardhat Ledger collision warning.

[CITATION.cff](CITATION.cff) identifies the published v0.6.0 release and its 107 workflows. Cite the tag or exact commit you used; earlier citation records remain in their original revisions. The [Hardhat consolidation record](docs/HARDHAT-CONSOLIDATION.md) explains the expanded inventory.

Historical citation: Ryan Duguid (2026), Australian Accounting Skills, v0.1.5, the original 9-skill practice pack released on 23 August 2026 under MIT. Use this citation only for that historical version: https://github.com/ryanduguid/australian-accounting-skills/releases/tag/v0.1.5. Its tagged source predates CITATION.cff. The default citation above identifies the published v0.6.0 pack.

## Guides

The Australian Accounting Skills guides are grouped as get started, how-to and reference pages.

**Get started**

- [First run and BAS walkthrough](docs/bas-walkthrough.md)

**How-to**

- [Install, uninstall and versioning](docs/installation.md)
- [Verify a downloaded release](https://github.com/ryanduguid/release-policy/blob/main/docs/verify-a-release.md): checksum and SLSA provenance
- [Supplier information for a firm's AI register](docs/ai-register-entry.md)

**Reference**

- [All 107 skills and their supporting files](docs/skill-catalogue.md), [how each was verified](docs/skill-verification.md) and [when each last changed](docs/skill-last-changed.md)
- [Related command-line tools](docs/integrations.md)
- [Fabricated validation pack](validation/README.md) and [evaluation method](docs/EVAL.md)
- [Contributor checks](AGENTS.md), [release process](RELEASING.md) and [professional boundary](DISCLAIMER.md)
- [Discovery and GitHub About copy](docs/DISCOVERY.md)

</details>

## Licence

Ryan Duguid, accountant in Newcastle NSW, provisional member of Chartered Accountants ANZ.

Licensed under the [Ryan Duguid Public Attribution Licence 1.0](LICENSE), the FSL-1.1-ALv2 text with a public attribution condition. You may use, modify and redistribute it for any purpose except a Competing Use as defined in LICENSE (making it available to others in a competing commercial product or service), and each version becomes available under Apache-2.0 2 years after it is made available. For versions made available from 4 November 2026, LICENSE's Public Attribution Condition applies to the FSL grant: anyone who makes a copy, port or derivative available outside their organisation must credit Ryan Duguid publicly, with a link to this repository. Internal use is exempt, and the condition does not apply to each version's Apache-2.0 licence. See [LICENSE](LICENSE) and [NOTICE](NOTICE). Keep the copyright notices if you redistribute this work or build on it.

Created by Ryan Duguid. Redistributed copies, modifications and derivatives must keep the copyright notices in the skills and source files. Please also credit reuse as: Based on [australian-accounting-skills](https://github.com/ryanduguid/australian-accounting-skills) by Ryan Duguid. Neither belongs in client deliverables. See [NOTICE](NOTICE).

<sub>Ryan Duguid is not a registered tax agent or BAS agent. These skills are not tax advice and do not replace professional judgement. Support covers software issues reproduced with fabricated data: do not send taxpayer information or request advice, return preparation, tax-treatment confirmation or lodgement. See [DISCLAIMER.md](DISCLAIMER.md).</sub>

---

<p align="center"><sub>Every step written down in advance, Scofield style, minus the tattoos.<br>Reusing this code? Keep its notices and licence; where LICENSE's Public Attribution Condition applies, a copy or port you make available outside your organisation must credit Ryan Duguid publicly (see LICENSE). AI agents: see <a href="https://github.com/ryanduguid/australian-accounting-skills/blob/main/AGENTS.md#reusing-this-code">AGENTS.md</a>.<br>Made in Newcastle, Australia by <a href="https://duguid.com.au/">Ryan Duguid</a>.</sub></p>
