## Install

Every route this page describes, with the revision it installs and how it was
tested. The sections below give the commands. The MCP server is the optional
[Aus Accounting MCP](#claude-code-plugin) calculator cross-check.

| Route | Revision | MCP server | Terminal | Tested | Update |
| --- | --- | --- | --- | --- | --- |
| [Skills CLI from a release checkout](#tagged-107-workflow-release) | v0.6.0 tag | No | Yes | The README's command copied all 107 skills from the files this release tags, on Linux on 12 November 2026; install only, no model run | Not tested. Clone the new tag and run `add` again; the skills CLI README at v1.5.22 does not say whether `add` overwrites |
| [Claude Code plugin at the release tag](#tagged-107-workflow-release) | v0.6.0 tag | Yes, `aus-accounting-mcp==0.6.0` through `uvx`; needs Python 3.14 or later and uv | No for `/plugin` in a session; yes for `claude plugin` | `claude plugin` delivered the 107 skills on Claude Code 2.1.316 from the files this release tags, on Linux on 12 November 2026 | Remove the marketplace with `/plugin marketplace remove ryanduguid` and add it again at the new tag; not tested |
| [Codex plugin at the release tag](#tagged-107-workflow-release) | v0.6.0 tag | No | Yes | Delivered the 107 skills on Codex CLI 0.167.1 from the files this release tags, on Linux on 12 November 2026 | Not documented |
| [Claude.ai or desktop app upload](#claudeai-or-the-claude-desktop-app-without-a-terminal) | v0.6.0 tag (source ZIP) | No | No | Not separately tested; steps follow Anthropic's article as read on 31 October 2026 | Not documented |
| [Claude Code plugin, development](#claude-code-plugin) | Default branch | Yes, `aus-accounting-mcp` 0.6.0 from its release commit through `uvx`; needs Python 3.14 or later, uv and Git | No for `/plugin` in a session; yes for `claude plugin` | `/context` measured the 97-skill listing at commit 472112e on 5 November 2026 | Not documented |
| [Codex plugin, development](#codex-plugin) | Default branch | No | Yes | None recorded | Not documented |
| [Cursor plugin, development](#cursor-plugin) | Default branch in the local plugins folder; the tracked branch in a team marketplace | No | Yes for the local folder; no for a team marketplace | Not tested; the manifest has not been loaded in Cursor | Team marketplace: **Refresh** in the dashboard, documented by Cursor; not tested. Local folder: not documented |
| [Skills CLI from GitHub](#any-agent-via-the-skills-cli) | Default branch | No | Yes | `--agent opencode` copied all 97 skills from `main` at 472112e on 5 November 2026; install and discovery only, on Linux | `npx --yes skills@1.5.22 update`, documented in the skills CLI README at v1.5.22; not tested |
| [Skills CLI from a development checkout](#development-checkout) | Default branch | No | Yes | A checkout at `63967e8` produced 50 skills in each target directory on 8 September 2026 | Not tested. Pull the checkout and run `add` again; the skills CLI README at v1.5.22 does not say whether `add` overwrites |
| [Manual copy](#manual-copy) | v0.6.0 tag | No | Yes | None recorded | Copy again from a checkout of the new tag; not tested |

### Tagged 107-workflow release

Start with v0.6.0, the latest published release. From a separate project
directory, install from a checkout of that tag:

```bash
git clone --branch v0.6.0 --depth 1 https://github.com/ryanduguid/australian-accounting-skills.git accounting-skills-release
npx --yes skills@1.5.22 add ./accounting-skills-release --agent codex claude-code --skill '*' --yes --copy
```

This copies all 107 released workflows into the current project's Codex
and Claude Code directories. It leaves global installations unchanged. A tag
fixes the installed revision; it does not certify model outputs. The
[evaluation guide](EVAL.md) records the tested revisions and limitations.

To install the same release as a Claude Code plugin, add the marketplace at
its tag, inside a session:

```
/plugin marketplace add ryanduguid/australian-accounting-skills#v0.6.0
/plugin install australian-accounting-skills@ryanduguid
```

Or from a terminal, which delivered the 107 skills on Claude Code 2.1.316 on
12 November 2026:

```bash
claude plugin marketplace add ryanduguid/australian-accounting-skills#v0.6.0
claude plugin install australian-accounting-skills@ryanduguid
```

For the same release in Codex, which delivered the 107 skills on Codex CLI 0.167.1
the same day:

```bash
codex plugin marketplace add ryanduguid/australian-accounting-skills --ref v0.6.0
codex plugin add australian-accounting-skills@ryanduguid
```

The Claude Code plugin carries the v0.6.0 tag's own MCP pin, `aus-accounting-mcp==0.6.0`,
launched with `uvx`, so it needs Python 3.14 or later and uv. To move to a later release, remove the marketplace with
`/plugin marketplace remove ryanduguid` and add it again at the new tag.

### Claude.ai or the Claude desktop app, without a terminal

For one or a few workflows, no developer tools are needed. These steps follow
Anthropic's [Use skills in Claude](https://support.claude.com/en/articles/12512180-use-skills-in-claude)
article, read on 31 October 2026. Claude Code remains this repository's tested
runtime; this route has not been separately tested, and the menus can change.

1. Download the source ZIP from the [v0.6.0 release](https://github.com/ryanduguid/australian-accounting-skills/releases/tag/v0.6.0) and extract it.
2. Open `.claude/skills` in the extracted folder. Files and folders starting with
   a dot can be hidden, so show hidden items if you cannot see it.
3. Make a ZIP of one skill's folder, such as `bas-preparation`. Keep the folder's
   name unchanged; it must match the skill's name.
4. In Claude, confirm that code execution and file creation is on, then go to
   **Customize > Skills**, choose **+**, then **+ Create skill**, then **Upload a skill**.
5. Upload the ZIP and check that the skill appears in your list and is on.

Uploaded skills carry no MCP server, so a skill's optional calculator cross-check
is not available. Skills that call on another skill work best when that skill is
uploaded too. Client data rules still apply: check your firm's approval before
putting client information into any cloud service.

### Development installations

The options below resolve the default branch or installed repository revision.
They can deliver unreleased changes made after v0.6.0. Choose them when you intend to test development work.

### Claude Code plugin

This repo is also a Claude Code plugin marketplace. It packages the inventory
present at the repository revision it installs under the stable namespace:

```
/plugin marketplace add ryanduguid/australian-accounting-skills
/plugin install australian-accounting-skills@ryanduguid
```

The skills then register as `australian-accounting-skills:bas-preparation` and so on.

The development plugin also starts the local [Aus Accounting MCP](https://github.com/ryanduguid/australian-accounting/tree/main/apps/aus-accounting-mcp)
server, pinned to `aus-accounting-mcp` 0.6.0 by its release commit `f17bbb2f920e3c11dac9810060a533c64e0e3be8`
and launched with `uvx`, so it needs Python 3.14 or later, [uv](https://docs.astral.sh/uv/) and Git on the path.
The first launch builds the package from that commit; tool calls then run locally and send nothing to the ATO or any other
service. `div7a-compliance` and `contractor-super-tpar` use its Division 7A and
Payday Super tools, when available, to cross-check their own calculations;
the current primary-source checks in each skill still run. To run the skills without the server, disable it with
`/mcp` in Claude Code. The `npx skills` and Codex routes do not start it.

The immutable v0.6.0 and v0.5.0 Skills tags retain their MCP 0.6.0 plugin pin, and v0.4.0 its original 0.2.7 pin.
Installing only its skill files with the tagged command above does not launch
that server. The development plugin's pin does not change the tagged archive.

Claude Code lists each skill's name and description in the context and keeps that
listing within a budget of 1% of the model's context window by default; past it,
the least-used skills lose their descriptions and are chosen less often. On
5 November 2026 `/context` in a fresh session (Claude Code 2.1.316, a 1 million
token window, no other plugins or user skills) put the Skills row at 8.4k tokens,
0.8% of the window, for this plugin's 97 skills at commit 472112e and 13 built-in
skills. The plugin's own rows summed to about 6.3k tokens. Skill descriptions are
capped at 160 characters and total 13,652. skill-tax-cli 0.1.0, a second reading
with its own estimate, put the same 97 descriptions at about 3.9k tokens and within
a 10k budget.

That fits a 1 million token window with little room, and not a 200,000 token one:
1% there is 2k tokens, and skill-tax-cli reported 49 of the 97 descriptions at risk.
On 12 November 2026 the pack held 107 skills whose descriptions total 15,364 characters,
13% more than the 97 measured above; a test now holds each to 160 characters. `/context`
has not been run on them, so expect a larger Skills row than the 5 November reading.
Other plugins and skills sharing the listing can also push it over. To check, run
`/context` and compare the Skills row with your window. To reserve more, set
`skillListingBudgetFraction` in your Claude Code settings, for example
`"skillListingBudgetFraction": 0.02` for 2%. On 1 November 2026 a value of 0.005
cut the then 76-skill listing to 5k tokens.

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

### Cursor plugin

`.cursor-plugin/plugin.json` follows Cursor's
[plugins reference](https://cursor.com/docs/reference/plugins) as read on
12 November 2026. It has not been loaded in Cursor, so treat this route as
untested. It declares the skills folder and no MCP server.

Cursor's [plugins page](https://cursor.com/docs/plugins), read on
12 November 2026, documents the Cursor Marketplace, which lists only plugins
its team has reviewed, a team marketplace on a Teams or Enterprise plan, and a
local plugins folder. This plugin is not in the Cursor Marketplace. The clone
below installs the default branch, and a team marketplace installs the branch
it tracks. Neither route has been tried here.

For the local folder, which needs no team plan, put the plugin in its own
folder under `~/.cursor/plugins/local`, for example with a clone of the default
branch:

```bash
git clone --depth 1 https://github.com/ryanduguid/australian-accounting-skills.git ~/.cursor/plugins/local/australian-accounting-skills
```

Then restart Cursor or run **Developer: Reload Window**, and confirm the skills
under **Customize**. Cursor skips a symlink in that folder that points to a
checkout elsewhere. On Enterprise, the admin setting **Allow Local Plugin
Imports**, off by default, must be on. Cursor does not document how to update
a local plugin.

For a team marketplace, an admin opens **Dashboard -> Plugins & MCPs**, clicks
**Add Marketplace**, uses **Import from Repo** with
`https://github.com/ryanduguid/australian-accounting-skills` and adds the plugin
with **Add to Marketplace**. To update it, click **Refresh**. Auto Refresh
needs the Cursor GitHub App installed on this repository, which an importing
team cannot do. Cursor's pages do not say whether a repository with one plugin
and no `.cursor-plugin/marketplace.json` imports this way.

### Any agent, via the skills CLI

One command, using the [`skills` CLI](https://github.com/vercel-labs/skills). It reads the
`.claude/skills/` layout this repo uses, so no extra manifest is needed:

```bash
npx --yes skills@1.5.22 add ryanduguid/australian-accounting-skills
```

That asks which skills and agents to install, so it needs a terminal, and it installs
into the current project. It resolves the default branch, not the tagged release. Add
`-g` to install globally, `-a claude-code` to target one agent, `-l` to list the skills
without installing anything, and `--skill '*' --yes --copy` to skip the questions.

Skills CLI 1.5.22 puts OpenCode, Gemini CLI and Cursor installs in `./.agents/skills/`.
On 5 November 2026 `--agent opencode` copied all 76 skills from v0.5.0 and all 97 from
`main` at 472112e there, and `opencode debug skill` on OpenCode 1.19.5 listed every one.
That is an install and discovery check on Linux only: no model ran, and the other 2
agents' copies were not opened in those agents.

### Development checkout

v0.6.0 contains 107 skills, and the default `main` branch can be ahead of it.
To try `main`, the default branch, in a separate project, clone it and install the
local checkout:

```bash
git clone --branch main https://github.com/ryanduguid/australian-accounting-skills.git accounting-skills-source
npx --yes skills@1.5.22 add ./accounting-skills-source --agent codex claude-code --skill '*' --yes --copy
```

This installs into the current project. Use a separate project to avoid
overwriting skills already installed there. The command copies every skill on `main`
into the Codex and Claude Code project directories; it does not install them
globally.

On 8 September 2026, installation from a checkout at
`63967e8b14929a718621f6fb9c655fb6e6987b7f` produced 50 skills in each target
directory, with every installed skill and supporting file matching the source.
Skills CLI 1.5.22 rejected a GitHub tree URL containing that raw commit SHA
because it attempted to clone it as a branch. Use the checkout method above.

GitHub verification run 34200334270 for that commit passed lint, shared conformance and verification on Python
3.10, 3.12 and 3.13. Installation proves the files are delivered correctly;
it does not establish fresh agent behaviour or validate current tax law.

### Manual copy

Clone the published tag, review the checkout, then copy the skills you want into
your project or user skills directory. Only the clone uses the network; the copy
reads the local checkout and starts no MCP server. To install from a downloaded
release archive instead, check it first with [Verify a downloaded release](https://github.com/ryanduguid/release-policy/blob/main/docs/verify-a-release.md).

```bash
git clone --branch v0.6.0 --depth 1 https://github.com/ryanduguid/australian-accounting-skills.git australian-accounting-skills
mkdir -p ~/.claude/skills
cp -r australian-accounting-skills/.claude/skills/* ~/.claude/skills/
```

PowerShell:

```powershell
git clone --branch v0.6.0 --depth 1 https://github.com/ryanduguid/australian-accounting-skills.git australian-accounting-skills
New-Item -ItemType Directory -Force "$HOME/.claude/skills"
Copy-Item -Recurse australian-accounting-skills/.claude/skills/* "$HOME/.claude/skills/"
```

Or copy individual skill folders into `<project>/.claude/skills/`. The skills cross-reference each other (`bas-preparation`, `stp-finalisation`, `workpaper-tie-out`, `fbt-annual-workflow` and `xero-exports` are shared dependencies), so installing the full set works best. For a firm repository, adapt [`templates/firm-CLAUDE.md.example`](../templates/firm-CLAUDE.md.example) to its actual policy; this repository's [`CLAUDE.md`](../CLAUDE.md) is contributor guidance, not a substitute for firm controls.

### Versioning

The tagged `v0.6.0` release contains and tests all 107 skills as a set.
`v0.5.0` contained 76, `v0.3.1` to `v0.4.0` 65, `v0.3.0` 63, `v0.2.1` and `v0.2.0` 19, and the earlier `v0.1.5` release the
original 9 practice skills. Installing
a subset by hand can break skills that call their siblings:

- `bas-preparation`, `month-end-close` and `year-end-workpapers` depend on `xero-exports`
- `fbt-annual-workflow` and `stp-finalisation` depend on each other (RFBA hand-off)
- `year-end-workpapers` depends on `bas-preparation`, `stp-finalisation` and `workpaper-tie-out`
- the contracting workflows use `contracting-exports` as their shared export
  reference, and the costing, claim, retention and WIP skills cross-reference
  each other

The [recommended installation](#tagged-107-workflow-release) pins v0.6.0.
The [development options](#development-installations) can be ahead of that tag.
Install the full tagged pack so sibling references stay consistent. The
9-skill `v0.1.5` pack remains available from its tag for anyone who cites
it.
