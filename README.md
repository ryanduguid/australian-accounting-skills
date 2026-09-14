# Australian Accounting Skills: show the BAS tie-out

[![Licence: MIT](https://img.shields.io/badge/licence-MIT-047857)](LICENSE)
[![Verify](https://img.shields.io/github/actions/workflow/status/ryanduguid/australian-accounting-skills/verify.yml?branch=main&label=verify&color=047857)](https://github.com/ryanduguid/australian-accounting-skills/actions/workflows/verify.yml)
[![Version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fryanduguid%2Faustralian-accounting-skills%2Fmain%2F.claude-plugin%2Fplugin.json&query=%24.version&label=version&color=047857)](.claude-plugin/plugin.json)

Synthetic example. Prep-only workflow aids. An authorised human reviews, decides and lodges. These skills do not provide tax advice or replace professional judgement.

**Input:** a fabricated quarterly cash-basis BAS with GST collected of $4,400.00 and GST paid of $1,210.00, plus the matching GST control-account movement.

Install all 50 workflows from the plugin marketplace. This route delivers the `main` inventory, the 50-skill development set preparing v0.3.0, not a published release:

```
/plugin marketplace add ryanduguid/australian-accounting-skills
/plugin install australian-accounting-skills@ryanduguid
```

To install the 19 workflows in the latest published release, [v0.2.1](https://github.com/ryanduguid/australian-accounting-skills/releases/tag/v0.2.1), clone that tag from a separate project directory instead:

```bash
git clone --branch v0.2.1 --depth 1 https://github.com/ryanduguid/australian-accounting-skills.git accounting-skills-release
npx --yes skills@1.5.22 add ./accounting-skills-release --agent codex claude-code --skill '*' --yes --copy
```

That copies the 19 released skills into the current project's Codex and Claude Code directories. It does not change a global installation. The [Codex plugin, the `npx skills` route, manual copying and versioning](docs/installation.md) cover the rest. The 31 skills `main` adds to the tag have no recorded model evaluation.

An agent runtime is still required. Ask it to prepare the BAS workpaper from the supplied reports and show the GST control-account tie-out.

**Output:** net GST of $3,190.00 ties to the $3,190.00 movement, with exceptions retained and reviewer sign-off blank.

**Human decision:** Resolve the coding exceptions and confirm the reporting basis and evidence before signing off.

![Synthetic BAS workpaper showing a $3,190 GST tie-out and blank reviewer sign-off](assets/readme/bas-workpaper-synthetic.svg)

<details>
<summary>Installation, worked example, skill catalogue and boundaries</summary>

## Runtime and release

Claude Code is the tested runtime. Codex packaging and portable skill files are included. That does not establish testing in every agent runtime.

The development installation resolves the default branch and adds 31 workflows to v0.2.1. See the [Australian topic coverage map](docs/au-guide-coverage.md) for the additions and verification limits, and [Installation](docs/installation.md) for the Hardhat Ledger collision warning.

[CITATION.cff](CITATION.cff) remains pinned to v0.1.5, the original 9-skill practice pack. The [Hardhat consolidation record](docs/HARDHAT-CONSOLIDATION.md) explains the expanded inventory.

## Reference

- [Install, uninstall and versioning](docs/installation.md)
- [First run and BAS walkthrough](docs/bas-walkthrough.md)
- [Fifty skills and their supporting files](docs/skill-catalogue.md)
- [Related command-line tools](docs/integrations.md)
- [Fabricated validation pack](validation/README.md) and [evaluation method](docs/EVAL.md)
- [Contributor checks](AGENTS.md) and [professional boundary](DISCLAIMER.md)
- [Discovery and GitHub About copy](docs/DISCOVERY.md)

Skills specify the workflow and require current primary authority for mutable rates, thresholds, labels and due dates. Keep real client files in the firm's approved environment, outside this repository.

Ryan Duguid, accountant in Newcastle NSW, provisional member of Chartered Accountants ANZ.

MIT: [LICENSE](LICENSE). Provenance: [NOTICE](NOTICE).

</details>
