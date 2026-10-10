# Australian Accounting Skills: show the BAS tie-out

Ryan Duguid is not a registered tax agent or BAS agent. Project support is limited to software issues reproduced with fabricated data. Do not send taxpayer information or request advice, return preparation, tax-treatment confirmation, or lodgement.

[![Licence: MIT](https://img.shields.io/badge/licence-MIT-047857)](LICENSE)
[![Verify](https://img.shields.io/github/actions/workflow/status/ryanduguid/australian-accounting-skills/verify.yml?branch=main&label=verify&color=047857)](https://github.com/ryanduguid/australian-accounting-skills/actions/workflows/verify.yml)
[![CodeQL](https://github.com/ryanduguid/australian-accounting-skills/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/ryanduguid/australian-accounting-skills/actions/workflows/codeql.yml)
[![Version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fryanduguid%2Faustralian-accounting-skills%2Fmain%2F.claude-plugin%2Fplugin.json&query=%24.version&label=version&color=047857)](.claude-plugin/plugin.json)
[![Codacy code quality](https://app.codacy.com/project/badge/Grade/b46694168d304886be1287d54cf33923?branch=main)](https://app.codacy.com/gh/ryanduguid/australian-accounting-skills/dashboard)

Synthetic example. Prep-only workflow aids. An authorised human reviews, decides and lodges. These skills do not provide tax advice or replace professional judgement.

**Input:** a fabricated quarterly cash-basis BAS with GST collected of $4,400.00 and GST paid of $1,210.00, plus the matching GST control-account movement.

Start with the 65 workflows in the published release, [v0.3.1](https://github.com/ryanduguid/australian-accounting-skills/releases/tag/v0.3.1), by checking out its tag from a separate project directory.

```bash
git clone https://github.com/ryanduguid/australian-accounting-skills.git accounting-skills-release
git -C accounting-skills-release checkout --detach v0.3.1
npx --yes skills@1.5.22 add ./accounting-skills-release --agent codex claude-code --skill '*' --yes --copy
```

Clone once per project. To repeat or retry from that directory, rerun only the checkout and install commands.

v0.3.0 corrects passages that v0.2.1 carried in `bas-preparation`, `fuel-tax-credits`, `coal-lsl-levy`, `plant-and-equipment-costing`, `contractor-super-tpar`, `payroll-tax-contractors`, `progress-claim-preparation`, `retention-schedule`, `xero-exports` and `wip-over-under-billing`, and unsourced statements in `cashflow-forecast-13week` and `stp-finalisation`. [Corrections since v0.2.1](RELEASE_NOTES.md#corrections-since-v021) lists each with its pull request. Check an affected passage against it before relying on v0.2.1.

That copies the 65 released skills into the current project's Codex and Claude Code directories. It does not change a global installation. The [Codex plugin, the `npx skills` route, manual copying and versioning](docs/installation.md) cover the rest. Recorded model runs cover 72 of the 83 [validation cards](validation/README.md). Claude Opus 5.5 passed all 70 cards then current in a whole-card run on 28 September 2026, confirmed on 29 September, and passed the `au-client-acceptance` and `au-working-holiday-makers` cards in single-card runs on 1 and 4 October, confirmed on 4 October. Earlier, Claude Opus 5 passed the 17 cards then current on 6 September and gpt-6-astra through Codex passed 16 of 17 on 8 September. Neither of those records states its input mode. The [evaluation guide](docs/EVAL.md) supplies the whole card, including its required checks, so read these results as adherence to visible instructions, not independent error detection. The 28 September run could read only each card and its skills, so it does not show source retrieval or restraint with action tools. The other 11 cards have no confirmed model verdict: the duplicate-export, mismatched-period, stale-workpaper, debtor-summary, source-quotation, receipt-conflict, statement-revision, completion-evidence, and three transaction-GST cases. Static checks cover all 65 skills, and [coverage.json](coverage.json) gives the state of each skill.

An agent runtime is still required. Ask it to prepare the BAS workpaper from the supplied reports and show the GST control-account tie-out.

Follow the [first run and BAS walkthrough](docs/bas-walkthrough.md) for the complete example.

**Output:** net GST of $3,190.00 ties to the $3,190.00 movement, with exceptions retained and reviewer sign-off blank.

**Human decision:** Resolve the coding exceptions and confirm the reporting basis and evidence before signing off.

![Synthetic BAS workpaper showing a $3,190 GST tie-out and blank reviewer sign-off](assets/readme/bas-workpaper-synthetic.svg)

<details>
<summary>Installation, worked example, skill catalogue and boundaries</summary>

## Runtime and release

### Development installation

The plugin marketplace installs the default branch, which can be ahead of v0.3.1. It is not a published release.

```
/plugin marketplace add ryanduguid/australian-accounting-skills
/plugin install australian-accounting-skills@ryanduguid
```

Claude Code is the tested runtime. Codex packaging and portable skill files are included. That does not establish testing in every agent runtime.

The development installation resolves the default branch, which can carry changes made after v0.3.1. See the [Australian topic coverage map](docs/au-guide-coverage.md) for the additions and verification limits, and [Installation](docs/installation.md) for the Hardhat Ledger collision warning.

[CITATION.cff](CITATION.cff) remains pinned to v0.1.5, the original 9-skill practice pack. The [Hardhat consolidation record](docs/HARDHAT-CONSOLIDATION.md) explains the expanded inventory.

## Reference

- [Install, uninstall and versioning](docs/installation.md)
- [First run and BAS walkthrough](docs/bas-walkthrough.md)
- [Sixty-five skills and their supporting files](docs/skill-catalogue.md)
- [Related command-line tools](docs/integrations.md)
- [Fabricated validation pack](validation/README.md) and [evaluation method](docs/EVAL.md)
- [Contributor checks](AGENTS.md) and [professional boundary](DISCLAIMER.md)
- [Supplier information for a firm's AI register](docs/ai-register-entry.md)
- [Discovery and GitHub About copy](docs/DISCOVERY.md)

Skills specify the workflow and require current primary authority for mutable rates, thresholds, labels and due dates. Keep real client files in the firm's approved environment, outside this repository.

Ryan Duguid, accountant in Newcastle NSW, provisional member of Chartered Accountants ANZ.

MIT: [LICENSE](LICENSE). Provenance: [NOTICE](NOTICE).

</details>
