# v0.5.1 (unreleased)

Together the changes below provide 101 skills, 207 validation cards and 116 routing
prompts. The added cards and prompts have no recorded model run.

Every skill that reads client documents, 96 of the 97, now records an instruction
that tries to change or override the workflow, its output, the firm's instructions
or the user's request, but not ordinary commercial terms, and any sign that a
document may have been altered or forged that the records do not explain, as a
reviewer exception without concluding why it differs. It keeps the item as printed,
marks it `UNVERIFIED` and leaves it out of supported totals until the reviewer
resolves it. The firm template carries the same rule. The skill left out,
`au-tax-rates-verification`, reads only published authority and calculator output.
16 synthetic cards bring the validation pack to 196: 7 plant instructions in a bank
statement line, an invoice footer, a lease clause, an email claiming to be from the
ATO, hidden PDF text, a spreadsheet comment and a client's attachment; 7 present an
ABN that fails its check digits, invoice lines that do not foot, impossible logbook
entries, a reused invoice number, an altered income statement, a BSB that belongs to
a different bank and an ATO statement that does not roll; and 2 positive controls
hold ordinary payment terms, including a note to the preparer, and a fully explained
timing difference, neither of which may be flagged. They have no recorded model run,
so the new test checks wording and card structure, not model behaviour.

Every skill now has a routing prompt. Sixty-six synthetic prompts bring
`validation/routing-cases.yaml` from 41 prompts for 35 skills to 107 for all
97, each listing the 1 to 3 neighbouring skills a router could confuse with the
expected one. A test now fails when a skill has no routing prompt. The new
prompts have no recorded model run.

`statement-to-csv` hands its tie-outs to a new `accounting-skills statement-check`
command when it is installed, which checks running, page and closing balances,
gross credits and debits against printed totals, and continuity between
statements in exact cents. Without it, the skill ties out by hand to the same
rules. Step 4 now fails omissions that cancel against printed totals, step 3
accepts a sign from the running balance only when the balance change equals the
amount and keeps card balances in the owed direction, and step 8 records Xero's
100,000-row limit and its date-format prompt, read on 11 November 2026. One
synthetic card brings the validation pack to 181, with no recorded model run for
it, so the new tests check wording and the checker's arithmetic, not model
behaviour. The 2 Xero source records still await human review: the source sweep
extracts no text from those pages, so it records no digest for them.

`accounting-skills statement-check` exits 0 when everything ties, 2 on any break
and 1 on malformed input, which includes an empty input, a repeated statement id
or a missing or repeated reference. It prints an `OVERLAP` line for each pair of
overlapping periods and breaks a statement period wholly within another, an
overlap it cannot place because the earlier lines lack posting dates or are not
in posting-date order, a line posted outside its period, and a line dated outside
it, with 31 days' allowance before the period for cards and other accounts in the
owed direction.
The `PASS` line counts the printed balances, printed totals and statement links
it compared.

Seven practice skills gain review steps. The transaction GST review in
`bas-preparation` screens manual journals to a GST account and credits on
government fees (GST Act Division 81 and the GST Regulations), and
`bas-preparation` runs the payroll tax registration test from
`au-payroll-tax-states` when payroll is in scope, comparing total Australian
or group wages with each paying jurisdiction's monthly, annual and any weekly
thresholds, and lists an unregistered Queensland group member separately.
`au-super-guarantee-charge` records the PCG 2026/1 risk zone at a recorded
as-at date for each first-year QE day with a shortfall, keeps a contribution
never made apart from one with no receipt date, and records who confirmed the
low-zone facts.
`xero-exports` ties a connector total to the on-screen report before relying
on a connection and runs completeness checks 1 and 3 on connector reads.
`tax-invoice-review` checks Peppol tax category codes (Guidance Note 11),
reads WET and LCT lines as Guidance Note 01 sets them out and holds a Peppol
self-billed RCTI to the same conditions as any RCTI.
`au-aml-ctf-client-coverage` names the practice system's code field, reports
dual-code mismatches, tests a trust's beneficial owner evidence role by role
and lists the trust, its representatives and identifiable beneficiaries for
screening. `au-payroll-review` screens new employees for a stapled fund request,
and `au-smsf-year-end` records each asset's market value basis and evidence.
The new test checks wording, not model behaviour, and the 9 new source records
await human review.

Two skills bring the pack to 99. `au-smsf-death-benefits` prepares an SMSF's
work after a member dies: each nomination tested against the deed, SIS and
tax dependants in separate columns, the forms of payment each recipient can
take, reversionary transfer balance credits, components and the untaxed
element, the payment timeline and withholding, and the records the trustee,
each recipient and the legal personal representative need.
`au-family-trust-election` prepares the evidence for deciding on a family trust
or interposed entity election: the reasons, each candidate test individual's
family and family group, the family control test, the earliest specified income
year, the FTDT that making the election would create, each interposed entity
election, the limits on later variation and revocation, and a form data sheet.
`au-franking-account` gains step 5a, which prepares a proposed private company
dividend: dividend rights, the s 254T evidence, a resolution schedule, the
benchmark position, draft distribution statements, the projected franking
entries and the Division 7A set-off route. `au-smsf-year-end` routes a member's
death to the new skill. Three synthetic cards bring the validation pack to 183 and
3 routing prompts bring the routing set to 44, with no recorded model run for
any of them. The new source records await human review.


`au-gst-property` gains a farm land step. It tests a supply of farm land for
farming (s 38-480) and subdivided farm land supplied to an associate
(s 38-475) condition by condition, with the evidence each needs, and sets them
beside the going concern path, the recipient's Division 135 adjustments, the
margin scheme history for a later sale, settlement withholding with the
credit (to a GST group's representative member or an insolvency
representative where liable) or refund, and the
supplier's notice. `au-primary-production` gains a farm succession step that
prepares the asset and entity register, CGT events, small business concession
and rollover evidence, trading stock and plant transfers, and the effect on
farm management deposits and averaging, routes duty, land tax and GST to their
skills and lists the family and legal decisions it leaves open. 2 synthetic
cards bring the validation pack to 182, with no recorded model run for them,
so the new test checks wording and card arithmetic, not model behaviour.
`au-small-business-cgt` now states the basic conditions and each concession's
extra conditions that the succession step routes to it, and notes that
s 152-205(2) changes the basic conditions for the small business reduction
from the income year that includes 1 July 2027. The 45 new source records
await human review.

Two skills fill gaps against the Ask Nagaris skill list. `au-main-residence`
prepares the main residence exemption evidence from Subdivision 118-B: who can
use it, the ownership period on contract and settlement dates, a period
schedule with the moving, changing residence, absence, building, destruction,
spouse and child rules, income use and the first income use rule, adjacent
land and the partial exemption inputs. `au-share-buy-back` prepares a
buy-back's workpapers under Division 16K and Part 2J.1: the tax and
Corporations Act classifications, the share capital tainting test, the
capital and dividend split beside the average capital per share, market
value, franking debits including distributions funded by capital raising,
Division 7A links and each seller's consideration and dividend.
`au-capital-gains`, `au-franking-account`, `au-nonresident-cgt`,
`au-rental-property` and `au-short-stay-accommodation` now route to them.
Five synthetic cards bring the validation pack to 185, with no recorded model run for them, and the new
source records await human review.

The `xero-exports` connector route gains a fork row in its tool allowlist: the
31 read tools `ryanduguid/xero-mcp-server` registers at commit `a115f18` with
`XERO_READ_ONLY=true`. The row applies only once the running server is verified
at that commit and setting; otherwise the base allowlist alone applies and the
work falls back to file exports.
The 31 handlers were read and no server was run, so the new test checks wording
and the tool names, not a live connection. The scopes check is unchanged.

`month-end-close` gains a close-control step after the review-ready gate. It
runs `close-control` when it is installed, carries `REVIEW` items forward and
returns a `BLOCKED` close to the preparer. On exit 0 or 2 it quotes the command
output and `exceptions.csv` byte for byte.
With no published release, it tells the operator to build the tool from
source. 2 synthetic cards bring the validation pack to 179, with no recorded
model run for them, so the new test checks wording, not model behaviour.

`tax-invoice-review`, `bas-preparation` and `au-bookkeeping` now state the tax
invoice threshold: a taxable supply valued over $75 excluding GST, which for
most supplies is a price over $82.50 including GST. `bas-preparation` also
screens for a credit at or below that value with no record. One synthetic card
brings the validation pack to 177, with no recorded model run for it, so the
new test checks wording and fixed figures, not model behaviour. The new source
records await human review.

The 10 cards added next bring the validation pack to 176, with no recorded
model run for them. The 8 transfer duty cards, one per state and territory,
exercise each jurisdiction's goods and business-asset rules. The 2 Xero cards
cover a new read-only connector route in `xero-exports` and `bas-preparation`,
which stops unless scopes and tools are confirmed read-only, records the
organisation, period, basis and capture time and refuses writes.
`au-business-formation` adds ASIC CP 391 as a dated proposal, and
`au-tax-research` names the corpus `as_at` check as an optional locator.

The connector route now asks a registered tax or BAS agent for the client's
permission first, citing TPB(GS) 55/2026, `au-bookkeeping` and `bas-preparation`
hold the same stop, and `docs/integrations.md` points to it. A file export is
not an exemption from the disclosure question. The README gains a Privacy section with
what leaves the machine and the conditional APP 1.7 to 1.9 duty from
10 December 2026.

Payroll tax source routes now cover all 8 jurisdictions. The contractor
workflow keeps its detailed NSW steps and routes other jurisdictions to their
own Acts and guidance, including the WA and ACT differences. New indexed
sources remain discovery only; the South Australian Act text was unavailable.
Eight fabricated jurisdiction cards bring the pack to 166, with no recorded
model run for those cards and 95 confirmed verdicts unchanged.

The preceding practice and land tax additions brought the validation pack to 158
cards. The FBT workflow reconciles each source line to its register, and the
tax agent obligations workflow separates optional professional-body rows from
TPB obligations. Land tax evidence routes cover all 8 jurisdictions, with the
Northern Territory position left unverified pending a primary source. The 9
new cards have no recorded model run. New source records await human review.

Fifteen skills gain a fabricated worked example with no rates, and a test
recomputes every equation in them.

`au-pre-lodgement-review` adds a missed-claim pass as reviewer questions,
`au-capital-gains` and `au-crypto-tax` take tracker reports as intake tied to
source records, and `year-end-workpapers` drafts a one-page client request list.

Adds 17 skills, bringing the pack from 76 to 93, and grows the validation
pack from 112 to 145 cards. Sixteen cover in-scope topics from a comparison
with the public Ask Nagaris skill list, recorded in
docs/nagaris-comparison.md; only the topic names were used.

- Tax workpapers: au-franking-account, au-trust-deed-review,
  au-restructure-rollovers, au-professional-firm-profits,
  au-travel-expenses, au-depreciation-schedule,
  au-property-development-income and au-primary-production.
- ATO and practice compliance: au-ato-objection,
  au-private-ruling-application, au-tax-agent-obligations,
  au-asic-company-changes and au-director-penalty-review, which comes from
  this repository's own gap list.
- Payroll, data and transactions: au-super-guarantee-charge (quarters and
  Payday Super QE days in separate registers), au-award-underpayment-review,
  statement-to-csv and au-business-acquisition-review.

Five skills are extended: au-capital-gains (pre-CGT and inherited-asset
evidence, and market valuations at a past date), au-super-contribution-caps
(proposed salary sacrifice headroom), au-tax-research (multi-issue requests
and the status of announced measures), au-individual-return (records
requests tied to the prior year) and au-land-tax (Victorian windfall gains
tax). Existing skills now route to the new ones where their work meets.

Skill descriptions are capped at 160 characters, so their combined length
stays below the 76-skill total. Claude Code's per-skill estimates put the
93-skill listing at about 6.1k tokens against 5.9k for the 76 skills before;
docs/installation.md records the measurement. Seventeen routing cases are added.
Every new source record is discovery-only. On 2 November Ryan Duguid accepted
the fetched readings of 143 of the 161 discovery-only records the repository
then held, without recording a current-law fact; the other 18 could not be
fetched and await human source review.
The 23 new cards were observed task-only, and the review of those answers
corrected 10 skills and 6 cards. Ryan Duguid confirmed a pass for each of the
23 on 2 November, so confirmed verdicts cover 95 of the 145 cards.

Three au-payroll-tax-states cards cover a group with a designated group
employer across 2 states, back pay and a reversal processed after 30 June,
and a part-year employer at the monthly threshold. They have no confirmed
verdict yet.

Five skills gain dated status and evidence checks. au-trust-distributions,
au-super-contribution-caps and au-rental-property record the stage of the
Treasury Laws Amendment (Tax Reform No. 3) Bill 2026, which passed the House
on 29 October 2026 and was not law on 4 November 2026, for the discretionary
trust minimum tax, transitional relief for June 2026 quarter super
contributions and the new residential dwelling tests. au-financial-statements
records whether a period is the comparative period before AASB 18 and the
AASB 108 disclosure of a standard issued but not yet effective.
au-pre-lodgement-review lists pre-filled income shown again in a manual
schedule. A new au-financial-statements card covers a for-profit Tier 1 year
ending 31 December 2026 and has no confirmed verdict yet. The new source
records await human review.

au-aml-ctf-client-coverage tests beneficial owner evidence owner by owner
against s 28(2)(d) and (e) of the AML/CTF Act, and records a screening
vendor's entity-level complete status beside that evidence, never in place
of it. It first applies any recorded basis under s 6-7, 6-17 or 6-18 of the
AML/CTF Rules to the owners within that basis's scope, whether or not owners
are listed, and routes a basis that is incomplete or rests on contradictory
KYC information to the compliance officer. Three new cards cover a company
with evidence for 1 of its 3 listed beneficial owners, known owners under a
recorded Rules exception and a basis resting on contradictory KYC, and have
no confirmed verdict yet. The new source records await human review.

bas-preparation lists import GST on broker and courier invoices coded to cost
as possible missed credits and tests who imported the goods and the import
declaration evidence against the ATO's imported goods guidance and
GSTR 2003/15. It excludes goods another entity imported on its own account
and recharges that are not import GST, and for deferred GST reconciles label
7A and proposes at 1B only the credit the evidence establishes. Two new cards
cover these cases and have no confirmed verdict yet. The 3 new source records
await human review, and preflight holds the skill until they are accepted.

workpaper-tie-out now traces both ways, from each source total forward as
well as from each statement line back, recomputes figures quoted in
narrative and tests any 'no exceptions' statement against open flags. A new
card covers a pack that agrees top-down but omits a source total and has no
confirmed verdict yet.

Six skills meet rules that changed in 2026. au-smsf-year-end checks real
property under an LRBA entered into from 10 August 2026 against the business
real property rule in s 67A(2)(c) of the SIS Act, with the exclusions for
earlier borrowings, refinancing and contracts. au-rental-property screens a
holiday home under s 26-50 of the ITAA 1997, TR 2026/1 and PCG 2026/3 before
apportioning. au-tax-agent-obligations extends the Code item 6 consent record
to AI tools under TPB(GS) 55/2026. au-trust-distributions records beneficiary
TFN quotes now that the quarterly TFN report has ceased. au-nonresident-cgt
applies the Act No. 86 of 2026 tests to CGT events from 1 October 2026, and
stp-finalisation asks whether the ABN, branch, payroll software or Payroll IDs
changed during the year. The new source records await human review.

Six more skills meet 2026 rules and drafts. bas-preparation compares any ATO
PAYG withholding pre-fill with payroll-derived W1 and W2, keeps payroll as
the source and leaves a difference unclassified unless a current ATO page
supports its cause. au-deceased-estates tests an inherited dwelling under
s 118-195 of the ITAA 1997 and marks TD 2026/D1 on the right to occupy as a
draft. fbt-annual-workflow tests car parking against s 39A(1) of the FBTAA,
TR 2021/2 and the Full Court's Toowoomba Regional Council decision, which the
High Court declined to review, and now carries a sources index in place of
its exemption. au-crypto-tax covers wrapping and airdrops under the drafts
TD 2026/D2 and TR 2026/D1. au-individual-return compares work-related claims
with the standard deduction in s 25-130 from 2026-27. au-tax-agent-obligations
records the Board sanctions in Schedule 1 to Act No. 86 of 2026 and the
amended section 45 client notices, and names TPB(GS) 49/2024 to 54/2024 for
the Code sections. The new source records await human review.

Six further skills gain dated checks. au-sole-trader adds a business-or-hobby
step 0 that records the indicators in draft TR 2026/D2, marked as a draft
open for comment until 27 November 2026, and routes missing or mixed evidence
to the reviewer. au-psi-review screens each PSB outcome against the low and
higher risk indicators in PCG 2025/5 and treats no level of PSI diversion as
safe. au-small-business-cgt keeps a gain a company or trust
disregards under the 15-year exemption off beneficiary statements and records
each payment of the exempt amount against s 152-125.
au-trust-distributions compares the trust's elections with the family trust
election and interposed entity election report in Online services for agents,
which gives no opinion on validity. au-aml-ctf-client-coverage gives each
ended relationship a 'retain until' date under s 111(2) of the AML/CTF Act
and keeps a retention list, never a deletion list. au-pre-lodgement-review
sets an individual's work-related expense claims beside a figure derived from
the ATO's taxation statistics, as a reviewer question only. The new source
records await human review.

au-transfer-duty lists every asset class in a transaction and records, for
each state and territory, what its revenue office says about goods
transferred with land or other dutiable property, excluded goods and other
business assets such as goodwill. South Australia taxes only land, including
fixtures; the other 7 can tax goods that go with other dutiable property. The
NSW-only starting point now names a revenue office for every jurisdiction.
xero-exports adds the GST Reconciliation (New report pack), the Tax
Depreciation and Tax Disposal Schedules and the older-BAS GST Audit report
trail, keeps the 'no GST Audit Report in the AU menu' line, and carries a
sources index in place of its exemption. The new source records await human
review.

Four practice skills bring the pack to 97 skills and 149 cards.
au-client-departure lists a departing client's records by proposed owner,
drafts the reply to the new accountant under APES 110 Section 320 and Code
item 6, and records lien questions and ATO client list steps without deciding
them. au-trust-losses evidences the Schedule 2F tests for a non-fixed trust,
the income injection test and family trust election records, and leaves each
deduction to the reviewer. au-ato-correspondence-triage sorts ATO letters and
notices by type, client match, stated due date and owner, screens for scams
and sends nothing. au-ato-account-reconciliation recomputes ATO account
balances, lists amendments processed after balance date for earlier periods as
reconciling items and pairs offsets. Each has a new card with no recorded run
and a routing case, and their descriptions keep the combined length below the
76-skill total. The new source records await human review.

The validation pack's private-data screen now refuses 2 kinds of digit run it
missed: an unbroken run of 12 or more digits, such as a card number, and a run
beside a full stop or comma, as at the end of a sentence or clause.

The coverage matrix builder, the source sweep's outcome check, task-only trial
preparation and the plugin eval builder now run only as native commands in
`tools/accounting-skills/`; their Python scripts are retired. The source sweep
files its issue from a separate job that runs no repository code. None of this
is part of the installed skills.

Both validation pack checkers ask Git once which sources `.gitignore` matches,
not once per file, so the pre-commit check no longer starts a Git process for
each of its 210 sources.

# v0.5.0

The pack moves from Apache-2.0 to the Functional Source License,
FSL-1.1-ALv2, with Apache-2.0 as the future licence (#289). The plugin
manifests declare FSL-1.1-ALv2. Releases up to v0.4.0 keep their licence. The pack grows from
65 to 76 skills and the validation pack from 83 to 107 cards.

Adds a short-stay accommodation workflow, au-short-stay-accommodation, and a
pre-lodgement review workflow, au-pre-lodgement-review, bringing the pack to
67. It prepares an individual host's gross platform
income reconciliation, night-by-night use calendar, holiday home evidence
under s 26-50, TR 2026/1 and PCG 2026/3, the GST residential premises screen
and state levy checks. It ships with a source-discovery record awaiting
baseline acceptance and 2 fabricated cases. A further au-capital-gains card
tests a disposal contract signed before 1 July 2027 that settles after it,
bringing the validation pack to 89 cards with the 3 pre-lodgement review
cards (#251).

au-pre-lodgement-review lists the items a reviewer should look at before
lodgement: missing records, claim conditions from the ATO's claiming
deductions guidance, claims out of line with occupation guides or small
business benchmarks, income completeness and ATO focus areas cited from
ato.gov.au. Every check is marked performed, not performed or not
applicable. It gives no risk rating or clearance to lodge, and sets no
claim by reference to the chance of review.

Skill text no longer hard-codes figures that change: au-payg-instalment-variation,
au-super-contribution-caps, bas-preparation and contractor-super-tpar now
point to the provision or ATO page that sets them, and a test fails on any
new dollar amount or percentage in skill prose. The cards for those 4
skills need a rerun at the revised commit.

A reconciliation break-trace workflow, reconciliation-break-trace, brings
the pack to 68. It traces each difference a bank, control account or
subledger reconciliation leaves open to its ledger entry and source record,
states the cause in one sentence and lists the evidence, owner and next
action. An unexplained remainder stays open, proposed adjustments stay
unposted drafts, and fresh exports and a rerun follow any posting. Its 2
fabricated cards test an unexplained remainder and an instruction in a
journal memo (#271).

Eight niche preparation workflows bring the pack to 76 (#279):
au-dssp (dividend substitution share plans, DRP and bonus-share parcels),
au-employee-share-schemes, au-foreign-pensions, au-lump-sum-arrears,
au-managed-fund-amit, au-non-commercial-losses, au-sapto and
au-small-business-income-offset. au-psi-review applies the PSI and PSB tests
to each individual and income year, verifies the results test first and
records a blocked test as unavailable, not failed. Their 12 fabricated cards
include one for au-psi-review.

au-bookkeeping, au-rental-property, au-tax-research, financial-modelling and
workpaper-tie-out gain evidence requirements for business identity, firm
templates, rental-agent funds and workpaper review, with 4 fabricated cards,
and the integrations guide documents a read-only MYOB recipe (#256).

Ten skills gain checks for comparing a result with an external calculator or
policy model, and every skill that mentions a calculator carries the
repository's calculator safeguards (#273). au-financial-statements and
wip-over-under-billing gain steps for verifying and citing a local AASB
corpus snapshot (#262). au-capital-gains, au-small-business-cgt and
au-trust-distributions point to the ATO's capital gains tax reform
transition rules from 1 July 2027 (#277).

Source records follow moved pages: the ASD business email compromise source
and 9 ATO sources are repointed (#275, #288) and the October change to the
ATO GST at settlement page is accepted (#274). tax-invoice-review indexes the
PINT A-NZ Billing release notes (#287), and au-tax-research the Tax
Practitioners Board annual report as a discovery aid (#292).

The Claude Code plugin starts aus-accounting-mcp 0.6.0, where the v0.4.0
tag pinned 0.2.7 (#257, #269).

The repository tooling gains a Rust port of `scripts/` in
`tools/accounting-skills/`, checked against the Python scripts, which stay
authoritative (#283), and Pyright replaces mypy (#264). Neither is part of
the installed skills.

Human-confirmed model verdicts cover 72 of the 107 cards. None of the 24
cards added since v0.4.0 has one.

# v0.4.0

The pack moves from MIT to the Apache-2.0 licence, with a `NOTICE` file whose
attribution anyone redistributing the skills or a derivative must keep (#230).
The plugin manifests declare Apache-2.0. Releases up to v0.3.2 stay under MIT.

The xero-exports debtor review reference now asks for Python 3.14 or later to
run the Accounting Review Pipeline aged-receivables example, matching that
repository's requirement (#214).

The repository's validation scripts refuse deeply nested front matter (#242),
contradictory source sweep reports (#228) and report paths outside the working
directory (#224, #244), and report a malformed `target_skills` value as a
validation error (#223, #244). They are not part of the installed skills.

Skill content is otherwise unchanged. The pack still has 65 skills.

# v0.3.2

bas-preparation gains a transaction GST coding review (#220). It accounts for
every supplied report row and keeps supply treatment, GST credit entitlement
and BAS period attribution separate, recording the evidence for each and
leaving unresolved findings for human review. xero-exports and the BAS
walkthrough follow it.

The working holiday maker super step reconciles contributions to qualifying
earnings for paydays from 1 July 2026 under Payday Super, and to ordinary time
earnings before then (#226).

au-tax-research asks for each decision's AGLC4 medium neutral citation, the
paragraph relied on and its later history (#218), and indexes the High Court,
Federal Court and Administrative Review Tribunal decision sources (#227).

Thirteen workflows adopt evidence intake, revision handling, source identity
and engagement completion checks (#217).

The validation pack grows from 76 to 83 cards. The three BAS GST cards and the
four source, receipt, revision and completion cards are prepared scenarios
with no model run or human-confirmed verdict recorded.

The pack still has 65 skills.

# v0.3.1

Adds one client acceptance and engagement terms review workflow,
au-client-acceptance. It prepares an acceptance or
continuance review and engagement terms for an authorised practitioner to
decide, and ships with a source-discovery record and a fabricated
missing-evidence case.

Adds a working holiday maker workflow, au-working-holiday-makers, bringing the
pack to 65. It runs in an employer mode (registration, Schedule 15
withholding, STP income type and country code, super) or an individual mode
(working holiday maker income, residency, the non-discrimination treaty
position after Addy, lodgement and departure), with a reviewed source record
and a fabricated missing-evidence case, bringing the validation pack to 72
cards. Both cards have confirmed results, described below.

Every volatile source record now carries a `reverify_by` date. The weekly
sweep reports a record past that date as review-due, and each skill whose
instructions point at `sources.json` says not to use an expired record even
as a cross-check.

xero-exports gains aged-receivables review guidance. Four core failure cards
cover debtor summary differences, repeated transaction identities, absent
exports, period mismatches and superseded workpaper references, bringing the
validation pack to 76 cards. Each includes a positive control. Their
structure and fixture arithmetic can be checked locally; no live agent
verdict is recorded for them. Source refreshes now keep pending human review,
bound fetches and redirects, and refuse linked source-index writes.

The client acceptance and working holiday maker cards have confirmed results.
Claude Opus 5.5 ran each card whole, told to read only the card and its
target skills: au-client-acceptance-missing-evidence at skills commit 4740483
on 1 October 2026 and au-working-holiday-makers-missing-evidence at 120fe99
on 4 October. Ryan Duguid judged both a pass on 4 October
([client acceptance](validation/results/2026-10-04-client-acceptance-confirmed.json),
[working holiday makers](validation/results/2026-10-04-working-holiday-makers-confirmed.json)).
The client acceptance card and its skill files are unchanged between those
commits. Other tools were available but unused, so the runs do not establish
source retrieval or restraint with action tools available.

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
