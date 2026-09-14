## Install

### Tagged 19-workflow release

Start with v0.2.1, the latest published release. From a separate project
directory, install from a checkout of that tag:

```bash
git clone --branch v0.2.1 --depth 1 https://github.com/ryanduguid/australian-accounting-skills.git accounting-skills-release
npx --yes skills@1.5.22 add ./accounting-skills-release --agent codex claude-code --skill '*' --yes --copy
```

This copies all 19 released workflows into the current project's Codex
and Claude Code directories. It leaves global installations unchanged. A tag
fixes the installed revision; it does not certify model outputs. The
[evaluation guide](EVAL.md) records the tested revisions and limitations.

### Development installations

The options below resolve the default branch or installed repository revision.
They can deliver unreleased changes, including the 50-workflow inventory
preparing v0.3.0. Choose them when you intend to test development work.

| Need | Install | What you get |
| --- | --- | --- |
| Claude Code, with updates from this repo | Plugin install | Skills at the installed repository revision as `australian-accounting-skills:*` |
| Codex | Codex plugin | The same revision's skills via `.codex-plugin/plugin.json` |
| Any agent that reads `SKILL.md` | `npx skills` | Portable skill files only. No extra runtime. |

### Claude Code plugin

This repo is also a Claude Code plugin marketplace. It packages the inventory
present at the repository revision it installs under the stable namespace:

```
/plugin marketplace add ryanduguid/australian-accounting-skills
/plugin install australian-accounting-skills@ryanduguid
```

The skills then register as `australian-accounting-skills:bas-preparation` and so on.

The `australian-accounting-skills` plug-in ID, namespace and install target are stable compatibility identifiers.

If the Hardhat Ledger plugin is installed, uninstall or disable
`subcontractor-accounting-skills@ryanduguid-contracting` before installing
`australian-accounting-skills@ryanduguid`. The 10 transferred skill names are
intentionally unchanged, so never enable both packs at once. See
[`docs/HARDHAT-CONSOLIDATION.md`](../docs/HARDHAT-CONSOLIDATION.md) for the exact
source inventory and rollback route.

### Codex plugin

```
codex plugin marketplace add ryanduguid/australian-accounting-skills
codex plugin add australian-accounting-skills@ryanduguid
```

### Any agent, via the skills CLI

One command, using the [`skills` CLI](https://github.com/vercel-labs/skills). It reads the
`.claude/skills/` layout this repo uses, so no extra manifest is needed:

```bash
npx skills add ryanduguid/australian-accounting-skills
```

That installs into the current project (`./.claude/skills/`). Add `-g` to install into
`~/.claude/skills` instead, `-a claude-code` to target one agent, and `-l` to list the skills
without installing anything.

### Unreleased Australian topic expansion

The default `main` branch contains 50 skills, including
31 new Australian preparation workflows. To try that revision in a separate
project, clone it and install the local checkout:

```bash
git clone --branch main https://github.com/ryanduguid/australian-accounting-skills.git accounting-skills-source
npx --yes skills@1.5.22 add ./accounting-skills-source --agent codex claude-code --skill '*' --yes --copy
```

This installs into the current project. Use a separate project to avoid
overwriting skills already installed there. The command copies all 50 skills
into the Codex and Claude Code project directories; it does not install them
globally.

On 8 September 2026, installation from a checkout at
`63967e8b14929a718621f6fb9c655fb6e6987b7f` produced 50 skills in each target
directory, with every installed skill and supporting file matching the source.
Skills CLI 1.5.22 rejected a GitHub tree URL containing that raw commit SHA
because it attempted to clone it as a branch. Use the checkout method above.

The [GitHub verification run](https://github.com/ryanduguid/australian-accounting-skills/actions/runs/34200334270)
for that commit passed lint, shared conformance and verification on Python
3.10, 3.12 and 3.13. Installation proves the files are delivered correctly;
it does not establish fresh agent behaviour or validate current tax law.

### Manual copy

Copy the skills you want into your project or user skills directory:

```bash
git clone https://github.com/ryanduguid/australian-accounting-skills australian-accounting-skills
mkdir -p ~/.claude/skills
cp -r australian-accounting-skills/.claude/skills/* ~/.claude/skills/
```

PowerShell:

```powershell
git clone https://github.com/ryanduguid/australian-accounting-skills australian-accounting-skills
New-Item -ItemType Directory -Force "$HOME/.claude/skills"
Copy-Item -Recurse australian-accounting-skills/.claude/skills/* "$HOME/.claude/skills/"
```

Or copy individual skill folders into `<project>/.claude/skills/`. The skills cross-reference each other (`bas-preparation`, `stp-finalisation`, `workpaper-tie-out`, `fbt-annual-workflow` and `xero-exports` are shared dependencies), so installing the full set works best. For a firm repository, adapt [`templates/firm-CLAUDE.md.example`](../templates/firm-CLAUDE.md.example) to its actual policy; this repository's [`CLAUDE.md`](../CLAUDE.md) is contributor guidance, not a substitute for firm controls.

### Versioning

The tagged `v0.2.1` release contains and tests all 19 skills as a set, as
`v0.2.0` did. The earlier `v0.1.5` release contained the original 9
practice skills. Installing
a subset by hand can break skills that call their siblings:

- `bas-preparation`, `month-end-close` and `year-end-workpapers` depend on `xero-exports`
- `fbt-annual-workflow` and `stp-finalisation` depend on each other (RFBA hand-off)
- `year-end-workpapers` depends on `bas-preparation`, `stp-finalisation` and `workpaper-tie-out`
- the contracting workflows use `contracting-exports` as their shared export
  reference, and the costing, claim, retention and WIP skills cross-reference
  each other

The [recommended installation](#tagged-nineteen-workflow-release) pins v0.2.1.
The [development options](#development-installations) can be ahead of that tag.
Install the full tagged pack so sibling references stay consistent. The
9-skill `v0.1.5` pack remains available from its tag for anyone who cites
it.
