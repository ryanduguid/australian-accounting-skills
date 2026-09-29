# v0.3.1 (unreleased)

Adds one client acceptance and engagement terms review workflow,
au-client-acceptance, bringing the pack to 64. It prepares an acceptance or
continuance review and engagement terms for an authorised practitioner to
decide, and ships with a source-discovery record and a fabricated
missing-evidence case, bringing the validation pack to 71 cards. That card
needs a confirmed result before this release.

# v0.3.0

Adds 43 original Australian preparation skills and one financial modelling
workflow, bringing the pack to 63.
The coverage map accounts for 38 OpenAccountants topic names while reusing
existing BAS, FBT, Division 7A and super workflows. Guide bodies were not
copied. Each of those additions includes a source-discovery record and a
fabricated missing-evidence case. The financial modelling workflow is
source-exempt and ships with a structure-faults case.

The new skills require applicable primary authority at use time; source
discovery is not current-law approval. Every addition's card has a
confirmed result, described below. Three of the
original 19 skill bodies gain new steps beyond the corrections listed below:
month-end-close gains a supplier bank-detail step, cashflow-forecast-13week a tax set-aside check and a GIC deductibility
note, and fbt-annual-workflow a status check on the announced electric car
discount changes. Six skills gain dated sources for 2026-27 Budget measures,
and au-ato-penalties-interest, au-payroll-review and tax-invoice-review gain
a GIC deductibility split, a pay-item settings review and a payee-detail
check. xero-exports and the shared accounting-safety rules keep credentials
with the operator: an agent never reads `.env` or another credential file,
never prints a secret value or passes one on a command line, and never asks
for one in chat.

The validation pack now has 70 cards, including 3 supported-arithmetic
cases for bookkeeping, financial-statement mapping and payroll tie-outs.
These check whether the model completes supported calculations while keeping
statutory conclusions and approval with the responsible human. All 70 cards
have confirmed results. Claude Opus 5.5 ran each card whole, with only its
target skills to read, against skills commit f4acd41 on 28 September 2026,
and Ryan Duguid judged every card a pass on 29 September
([confirmed record](validation/results/2026-09-29-whole-card-confirmed.json)). Skills changed after f4acd41
only in link targets. The runs could read nothing else and had no action
tools, so they do not establish source retrieval or restraint with action
tools available. The evaluation guide requires separate evidence for both.

The README recommends the tagged v0.3.0 installation. Development installation
commands resolve the default branch, which can be ahead of this release.

## Corrections since v0.2.1

Recorded 27 September 2026. Each passage below was wrong or unsupported in
v0.2.1 and is corrected on `main`. Anyone using v0.2.1 should check the
passage against the corrected text before relying on it.

- In `bas-preparation`, W1 gross payments under a voluntary agreement came
  from the PAYG withholding payable account, which holds only the amount
  withheld. They now come from the payroll report or the payment records, with
  the withholding reconciled separately (#113). Label mapping now starts from
  the entity's own statement and a checked ATO source (#103).
- In `fuel-tax-credits`, step 10 reduced non-cash attribution to the invoice
  alone. Under s 65-5 of the *Fuel Tax Act 2006* it now attributes the credit
  to the earlier of the period in which consideration is provided or an
  invoice is issued, provided the tax invoice is held at lodgement, and treats
  the later-period election in s 65-5(4) to (6) as a separate choice (#113).
- In `coal-lsl-levy`, v0.2.1 said there is no carve-out and no power to
  excuse. Schedule 1 clause 19(4) of the *Coal Mining Industry (Long Service
  Leave) Payroll Levy Collection Act 1992* disapplies ss 5 and 10 for
  employment covered by a Board-approved unpaid levy payment arrangement
  (#151). Employer screening now applies the definition in s 14 of the *Fair
  Work Act 2009*, including the Territory route, rather than legal form (#117).
  Eligible wages follow the formulas in s 3B of the same Payroll Levy
  Collection Act, including the Formula A and Formula B comparison (#115).
- In `plant-and-equipment-costing`, v0.2.1 offered a self-substantiated labour
  split as an alternative to a Chief Commissioner determination. Section 35(2)
  of the *Payroll Tax Act 2007* (NSW) requires the determination (#151).
- In `contractor-super-tpar`, the domestic-work exclusion in s 12(11) of the
  *Superannuation Guarantee (Administration) Act 1992* now needs a direct
  arrangement between the payer and the worker for domestic work done for the
  payer, following *Newton* [2010] FCA 1440 and TR 2023/4 (#116).
- In `payroll-tax-contractors`, wages for services performed wholly in NSW
  follow s 11(1)(a) of the *Payroll Tax Act 2007* (NSW) even if the worker
  lives elsewhere. The residence hierarchy applies only to services across
  jurisdictions (#115).
- In `progress-claim-preparation`, deadlines keep their contractual unit
  instead of all counting as business days (#115).
- In `retention-schedule`, Queensland retention trust account timing follows
  ss 34(2) and 35(2) of the *Building Industry Fairness (Security of Payment)
  Act 2017* (Qld) (#115).
- In `xero-exports`, totals in the inspected exports use live formulas of
  several kinds, not only `SUM`. The nil side of a debit or credit column can
  hold a numeric zero, and the Transactions by BAS Field tab has no `Net`
  column (#115).
- In `cashflow-forecast-13week`, `stp-finalisation`, `contractor-super-tpar`,
  `payroll-tax-contractors` and `coal-lsl-levy`, statements the skill could
  not source are now marked UNVERIFIED and leave the outcome `UNKNOWN` until
  checked. They include the 14 July finalisation deadline and the claimed
  1 July 2026 payday super STP fields in `stp-finalisation` (#103, #148).
- In `wip-over-under-billing`, the schedule engine link pointed at the retired
  TheWIPTally repository. It now pins the australian-accounting package (#103).

# v0.2.1

Changes since the last published release, `v0.2.0`. The inventory is the same
19 skills.

- `xero-exports` replaces its inferred parsing rules with conventions and
  header rows verified against Xero's own report exports. The skill's Parsing
  conventions and Observed column headers sections are the record: they name
  the export set (the Excel exports of 41 Demo Company (AU) reports plus the
  Overall Budget and Statement Lines CSV exports), carry the 5 September 2026
  check date beside each fact relied on, and say to re-verify when Xero
  changes a report layout.
- The validation pack gains a results schema and evaluation guide, and the
  first recorded validation run: 17 cards, 17 pass, `claude-opus-5` at
  `6e08f2a`, one fresh session per card with only that card and the skills it
  names loaded.
- The README leads with the synthetic BAS tie-out, AGENTS.md merges its
  duplicated repository summary and hand-off check lists, and the sibling
  tools point at their monorepo homes.
- `verify.yml` runs ruff and mypy in a lint job before the verification checks,
  which now run on Python 3.10, 3.12 and 3.13, and `pre-commit` runs the same
  ruff version on staged files. Every workflow carries a concurrency group and
  a job timeout, and text files normalise to LF.
- The release and verify workflows call the shared release-policy workflows at
  a commit reachable from that repository's `main` (`99a6314`) after the
  5 September history rewrite left the earlier pins dangling. The shared
  skill-verification canary reports on that pin.

# v0.2.0

Changes since the last published release, `v0.1.5`:

- The destination plugin is `australian-accounting-skills@ryanduguid`. Its
  19 skills include the 10 incoming Hardhat Ledger skills:
  `coal-lsl-levy`, `contract-cost-tracking`, `contracting-exports`,
  `contractor-super-tpar`, `fuel-tax-credits`, `payroll-tax-contractors`,
  `plant-and-equipment-costing`, `progress-claim-preparation`,
  `retention-schedule` and `wip-over-under-billing`.
- Claude and Codex plugin discovery resolve the canonical `.claude/skills/`
  owner. `skills@1.5.22 add . --list` must discover the same 19 skills.
- After a published and publicly verified destination release passes its gates,
  uninstall or disable `subcontractor-accounting-skills@ryanduguid-contracting`
  before installing `australian-accounting-skills@ryanduguid`. Never enable both
  packs at once because the 10 transferred skill names collide.
- To roll back, uninstall the destination pack and reinstall Hardhat Ledger
  `v0.1.5`. Keep its release and tags intact.

# v0.1.5

Changes since the last published release, `v0.1.4`:

- The documented Claude Code install works again: the marketplace entry sets `strict: true`, resolving the conflicting-manifests error that made the plugin fail to load with zero skills registered.
- The project identity is Australian Accounting Skills everywhere a reader meets it: README and contributor-guide headings, the disclaimer's lead sentence, the banner and the release runbook.
- Every skill's Boundaries section closes with an inline not-advice line that survives copying a single skill folder out of the repository, except `stp-finalisation`, which shipped with a repository-relative `DISCLAIMER.md` link only. Its inline line landed after this release.
- bas-preparation's `sources.json` records provenance for the W3/W4 label facts and the $1,000 capital-purchases concession its text hedges.
- Repository topics are reconciled between docs/DISCOVERY.md, the publish script (which now sets the list wholesale) and the live About; Dependabot covers the pinned pip test dependency.
- The release runbook records that v0.1.1 to v0.1.4 predate the August 2026 history rewrite, so `gh release verify` fails permanently for them; this release restores end-to-end verification.

# v0.1.4

Changes since the last published release, `v0.1.3`:

- publish the W1 large-withholder mapping (#35) and Payday Super allowable-period / s 18C control (#36) that landed on `main` after `v0.1.3`, so the tagged zip matches git `main`
- require an `UNKNOWN` / no-SGC missing-facts branch on the SG validation cards when first-contribution or s 18C facts are absent, and forbid a late classification from a 7-business-day count alone
- name the sibling CLIs `payday-super-check` and `export-tb` / `xero-trial-balance-export` from the skills pack, without moving SGC calculation into the agent
- point year-end payroll/SG ageing at the Payday Super timing control in `stp-finalisation`, and add the ATO employer Payday Super URL beside the existing software-developer source.

Recovery note: `v0.1.2` is a protected annotated tag at `efc8c5b8f0b6bd1dee65eccba953cb1b60a4aaa4`, but it has no GitHub release. Its release run failed safely at the asset-inventory gate because that gate expected `SHA256SUMS` before creating it. Upload, attestation, draft creation and publication did not start. The tag will not be moved, deleted or reused.
