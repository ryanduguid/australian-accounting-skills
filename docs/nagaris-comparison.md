# Ask Nagaris skill list comparison

Sixteen new skills and 5 extended skills cover the in-scope topics on the Ask Nagaris public skill list that this repository lacked. A seventeenth new skill in the same change, `au-director-penalty-review`, comes from this repository's own gap list rather than the Nagaris page. On 11 November 2026 `au-main-residence` and `au-share-buy-back` were added for 2 topics: the main residence exemption, which this table had recorded as covered although `au-capital-gains` held it only as review facts, and private company share buy-backs, which it had recorded as not adopted. On 12 November 2026 `au-client-meeting-note` was added for client meeting file notes, which this table had recorded as not adopted. Later that day `au-client-letter` and `au-cpi-rent-review` were added for the client advice letter and the CPI rent review, which this table had recorded as not adopted, and `au-client-email-triage` for client email triage, which it had recorded as extended in `au-tax-research`. The same day 16 topics this table had recorded as covered were read again against the skill text, and 13 skills were extended for 14 of them, where the workflow had stopped short of the output the topic names. Every other topic is either already covered here or is outside the repository's preparation-only accounting boundary, as the table below records.

Comparison date: 2 November 2026; the page was read again on 11 November 2026 for the main residence and share buy-back rows and on 12 November 2026 for the meeting file note row and the rows that name that day. Source: the public page [Ask Nagaris skills: the full list](https://nagaris.com/ask-nagaris-skills), which names 79 skills with a one-line description each, grouped by kind of work, although its introduction says 'more than 80'. Accounting-skills base: `f7e8c38`. The page publishes no skill content, so only the topics were used. All workflow text, sources and validation cards were written independently for this repository from Australian primary sources read on 2 November 2026; no Nagaris text was copied. Topic labels below are this repository's own summaries, not the page's wording.

## Decisions

'New' and 'Extended' name the skill that now carries the topic. 'Covered' names the existing skill. 'Not adopted' gives the reason.

### Tax advice and calculations

| Topic | Decision | Where or why |
| --- | --- | --- |
| Capital gains on a sale, including the discount, small business concessions, main residence and foreign residents | Covered; main residence new on 11 November 2026 | `au-capital-gains`, `au-small-business-cgt`, `au-nonresident-cgt`; `au-main-residence` prepares the main residence exemption evidence, which `au-capital-gains` had held only as review facts |
| Pre-CGT status, including inherited assets | Extended | `au-capital-gains`: acquisition evidence, inherited-asset dates and Subdivision 149-B ownership history |
| Market value of a property at a past date | Extended | `au-capital-gains`: valuation date, purpose, instructions and report contents; an appraisal is only a screen |
| Cost base of dividend reinvestment shares | Covered | `au-dssp` |
| CGT rollovers on a restructure | New | `au-restructure-rollovers` |
| Division 7A repayments, deemed dividends and trust entitlements | Covered | `div7a-compliance` |
| Private company dividends and distribution statements | New | `au-franking-account`; its step 5a, added on 11 November 2026, prepares a proposed dividend's s 254T evidence, resolution schedule, benchmark position, draft statements and franking entries, and routes a loan set-off to `div7a-compliance` |
| Franking account reconciliation and franking deficit tax | New | `au-franking-account` |
| Private company share buy-back | New on 11 November 2026 | `au-share-buy-back` prepares the company's and each seller's workpapers; the directors decide and a lawyer advises on the procedure |
| Family trust and interposed entity elections | New on 11 November 2026 | `au-family-trust-election` prepares the evidence for deciding on a new election: test individual, family group, specified income year, interposed entity elections, revocation limits and FTDT exposure. `au-trust-distributions` screens FTDT each year and `au-trust-deed-review` records existing elections |
| Trust deed review | New | `au-trust-deed-review` |
| Trust distribution resolution | Extended on 12 November 2026 | `au-trust-distributions` step 1a prepares a resolution content schedule for the trustee and their lawyer, with the resolution-readiness checklist in `au-trust-deed-review`; it is content, never wording, and the trustee and adviser draft and execute resolutions |
| Partnership agreements and partnership tax | Extended on 12 November 2026 | `au-partnership-tax` step 1a abstracts the agreement by clause and lists numbered questions for the partners' solicitor; validity and construction stay with the solicitor |
| Professional firm profit allocation | New | `au-professional-firm-profits` |
| Fringe benefits tax | Covered | `fbt-annual-workflow`, `au-car-expenses` |
| Travel deductions | New | `au-travel-expenses` |
| Individual deduction checklist | Covered | `au-individual-return`, `au-pre-lodgement-review`, `au-wfh-deductions`, `au-car-expenses` |
| Tax and accounting depreciation schedules | New; extended on 12 November 2026 | `au-depreciation-schedule`; step 8a prepares the accounting schedule from the entity's documented policy and ties it to the trial balance. `plant-and-equipment-costing` keeps per-machine costing |
| Non-commercial business losses | Covered | `au-non-commercial-losses` |
| Property development: income or capital | New | `au-property-development-income` |
| GST on property | Covered | `au-gst-property`; GST-free farm land under ss 38-480 and 38-475, with its going concern, margin scheme and withholding questions, added on 11 November 2026 |
| Primary production | New | `au-primary-production`; farm succession evidence added on 11 November 2026 |
| Fuel tax credits | Covered | `fuel-tax-credits` |
| Tax residency and overseas income | Covered | `au-tax-residency`, `au-foreign-income`, `au-foreign-pensions`, `au-working-holiday-makers` |
| Crypto records | Extended on 12 November 2026 | `au-crypto-tax`; step 0 drafts a records checklist and cover note for the practitioner to send, never asking for keys or seed phrases |
| Federal Budget measures and whether they are law | Extended | `au-tax-research`: announced, introduced, passed, assented or commenced, with the ATO's guidance on proposed measures; since 12 November 2026 it also screens a set of Budget measures against the client's facts, giving status and routes only |

### Super, retirement and estate

| Topic | Decision | Where or why |
| --- | --- | --- |
| Super and SMSF technical questions | Covered | `au-super-contribution-caps`, `au-smsf-year-end`, `au-division-293`, `au-division-296`; SMSF death benefits had no workflow until `au-smsf-death-benefits` was added on 11 November 2026 |
| Salary sacrifice to super | Extended | `au-super-contribution-caps` step 7: headroom by fund receipt date and effective-arrangement evidence, with no recommended amount |
| Super guarantee charge | New | `au-super-guarantee-charge` |
| Centrelink entitlements | Not adopted | Social security entitlement estimates are outside accounting preparation and Services Australia decides them; `au-sapto` covers the tax offset |
| Estate planning check | Not adopted | Reviewing wills, powers of attorney and nominations is legal work; `au-deceased-estates` covers the tax position after death |

### State taxes

| Topic | Decision | Where or why |
| --- | --- | --- |
| Duty, land tax and payroll tax in NSW, Victoria, South Australia and the ACT, and comparisons across states | Covered | `au-transfer-duty`, `au-land-tax`, `au-payroll-tax-states`, `payroll-tax-contractors`; payroll source routes cover all 8 jurisdictions, with detailed NSW contractor steps and separate routes for other jurisdictions |
| Victorian windfall gains tax | Extended | `au-land-tax` step 5: the rezoning, the owner then, the values on the notice, exemptions and any deferral |

### ATO and practice compliance

| Topic | Decision | Where or why |
| --- | --- | --- |
| Objection to an ATO decision | New | `au-ato-objection` |
| Remission of interest and penalties | Extended on 12 November 2026 | `au-ato-penalties-interest` step 7 sets out the draft request: only facts the evidence pack holds, unsigned, for the registered agent to review and send |
| Private ruling application | New | `au-private-ruling-application` |
| A tax agent's own obligations | New | `au-tax-agent-obligations` |
| AML/CTF obligations for accounting firms | Extended on 12 November 2026 | `au-tax-agent-obligations` step 8a keeps a row for each of the practice's own obligations under the Act and Rules, with no conclusion on compliance or designated services; `au-aml-ctf-client-coverage` and `au-client-acceptance` cover client checks |
| ASIC company changes, forms, deadlines and fees | New | `au-asic-company-changes` |
| Director appointment and resignation resolutions | New | `au-asic-company-changes` (resolution readiness); directors review and sign |

### BAS and bookkeeping

| Topic | Decision | Where or why |
| --- | --- | --- |
| BAS pre-lodgement check | Covered | `bas-preparation`, `tax-invoice-review`, `au-gst-registration-review` |
| Review after a BAS is lodged | Extended on 12 November 2026 | `bas-preparation` (lodged-figure drift and post-lodgement closing journal); step 6 turns each unexplained movement into a draft question for the client |
| Transaction coding and client queries | Extended on 12 November 2026 | `au-bookkeeping`; step 3a drafts a query for each line of unknown purpose, and a suggested code stays a suggestion until the client answers |
| Bank statement, credit card statement or pasted list to import CSV | New | `statement-to-csv` (one skill for all 3 sources) |
| Xero and MYOB troubleshooting | Not adopted | Vendor help pages own software fixes and change often; `xero-exports` and `myob-exports` cover the exports the skills use |

### Client reporting and advisory

| Topic | Decision | Where or why |
| --- | --- | --- |
| Review of several years' financials before the return | Extended on 12 November 2026 | `year-end-workpapers` (analytical review, with a 3-year view when 2 prior years' signed statements are supplied), `au-pre-lodgement-review` |
| Monthly management report | Extended on 12 November 2026 | `month-end-close` step 9: a report from the closed figures with stated ratio formulas, trends and options for the owner; `financial-modelling` |
| Three-way cash flow forecast | Extended on 12 November 2026 | `financial-modelling` three-way section, whose `check_balance` and `check_cash` must be zero every month; `cashflow-forecast-13week` for the weekly view |
| Loan repayments and affordability | Not adopted | Affordability is a credit judgement; repayment schedules belong in `financial-modelling` workbooks |
| Buy-side due diligence on a business | New | `au-business-acquisition-review` |
| Structure advice letter | Not adopted | Advice to a client; `au-tax-planning-review` and `au-business-formation` prepare the evidence before and after a human chooses |
| Commercial lease review | Not adopted | Legal review of lease terms |
| CPI rent review and CPI indexation | New on 12 November 2026 | `au-cpi-rent-review` works out a lease's reviewed rent in exact cents from its clause and the ABS CPI release, applies any cap, collar or ratchet and drafts the notice for the landlord to check and send; where tax law indexes an amount, the skill for that task names the series to verify |

### Employment and payroll

| Topic | Decision | Where or why |
| --- | --- | --- |
| Employment law questions | Not adopted | Fair Work legal advice |
| Award underpayment audit | New | `au-award-underpayment-review` |
| Redundancy payout | Covered | `au-etp-redundancy` covers the tax treatment; notice and entitlement amounts stay with the employer's adviser |
| Tax on a final pay | Covered | `au-etp-redundancy`, `au-payroll-review` |
| Offer letters and new employee packs | Not adopted | Employment contract and HR document drafting; `au-payroll-review` screens employee master data |
| Employing visa holders | Covered in part | `au-working-holiday-makers` covers the tax and payroll side; sponsorship and work limits are migration law |
| Work health and safety, workers compensation | Not adopted | Outside accounting preparation |

### Client communication and documents

| Topic | Decision | Where or why |
| --- | --- | --- |
| Reply to a routine client tax question, client advice letter | Letter new on 12 November 2026 | `au-client-letter` lays out advice a named practitioner has approved on the firm's template, each sentence traced and nothing added, for the practitioner to check and send; answering a client's tax question stays a human decision, and `au-tax-research` prepares the file note behind it |
| Triage of a multi-issue client email | New on 12 November 2026 | `au-client-email-triage` turns the email into an issue register, each question, deadline and attachment quoted and routed, answering none; `au-tax-research` takes each question that needs a file note |
| Tax research brief | Covered | `au-tax-research` |
| Year-end records request | Extended | `au-individual-return` step 1: each request item tied to the prior-year item or new event it follows from, with a covering email since 12 November 2026; `year-end-workpapers` step 0 does the same for entities |
| Matching 2 client lists | Covered in part | `au-aml-ctf-client-coverage` matches the client list to due diligence records and, since 12 November 2026, `au-tax-agent-obligations` step 8b matches the practice's client list to the ATO's on a shared identifier; generic list matching is not accounting-specific |
| Meeting file notes | New on 12 November 2026 | `au-client-meeting-note` turns a meeting transcript or notes into a draft file note for the practitioner's review. A file note of a client meeting is a record a tax practitioner may need to make (TPB(GS) 52/2024 gives a file note about advice provided verbally as an example), and a draft for review stays inside the preparation boundary. The client summary and work brief the Nagaris page also lists are not adopted: the note is never sent to the client |
| Document comparison, procedure flowcharts, branded charts and firm branding | Not adopted | General document tools, not accounting workflows; firm layouts are supplied through `templates/` and each skill's output rules |

## Verification and limits

The new skills follow the existing format: inputs, workflow, hand-off, the shared source and review boundary, a primary-source starting point and a discovery-only `sources.json`. Ryan Duguid accepted the fetched readings of those records on 2 November 2026 without recording a current-law fact; records that could not be fetched still await human source review. Each new skill and each extension has at least one fabricated validation card. Their task-only observations on 2 November 2026 led to corrections in 10 of the skills, and Ryan Duguid confirmed a pass for each card on 2 November 2026 ([docs/EVAL.md](EVAL.md)). No rate, threshold, fee or due date was added to skill prose. This comparison does not assess the quality of the Nagaris product, which this repository cannot inspect.

A recheck on 11 November 2026 found 3 sub-topics the rows above had marked as covered or new without a workflow for them: SMSF death benefits, preparing a private company dividend and deciding on a new family trust election. `au-smsf-death-benefits`, `au-family-trust-election` and step 5a of `au-franking-account` now cover them, written from legislation and ATO sources an agent read that day. Their source records await human review, and their 3 validation cards have no recorded model run.

A second recheck on 12 November 2026 read 16 topics the rows above had marked as covered against the skill text. 14 rows changed: the skill named now prepares the output the topic describes, such as a draft request, a schedule, a report or a register row, where before it stopped at the working behind it. Each draft is for the practitioner to review and send, and none states a tax position. 2 topics stay outside the boundary: a reply to a client's tax question, and visa sponsorship and work limits. The new steps were written from sources an agent read that day. Their new source records await human review, and their 14 validation cards have no recorded model run.
