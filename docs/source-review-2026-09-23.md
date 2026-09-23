# Source claim check, 23 September 2026

An agent checked the unverified claims behind audit findings AAS-1, AAS-4 and
AAS-6 against public primary sources. This is not a human review. No human
`checked_at` date, `fact` or record URL was changed; the skills keep a visible
"Human review pending" flag and still require a source check at use time.
Dates use Australia/Sydney (UTC+10). No client data was used.

## AAS-6: STP finalisation deadline

The indexed URL (`.../single-touch-payroll/in-detail/finalisation`) and a
second guessed URL both return HTTP 404. The live page is
[End-of-year finalisation through STP](https://www.ato.gov.au/businesses-and-organisations/hiring-and-paying-your-workers/single-touch-payroll/start-reporting/end-of-year-finalisation-through-stp),
QC 58561, last updated 16 October 2025. It states:

- 14 July each year for arm's length employees
- 30 September for closely held payees, where the employer has 20 or more
  employees or has both closely held and arm's length payees
- the payee's tax return due date where a small employer (19 or fewer
  employees) has only closely held payees.

A person should re-point the `sources.json` record to this URL and date the
review.

## AAS-1: Payday Super STP amounts

[Single Touch Payroll reporting under Payday Super](https://www.ato.gov.au/businesses-and-organisations/super-for-employers/paying-super-on-payday/single-touch-payroll-reporting-under-payday-super),
QC 107592, last updated 27 June 2026, requires qualifying earnings and
superannuation liability amounts for each employee for paydays from 1 July
2026. From 1 July 2027 the ATO rejects reporting that lacks both amounts.

The page names no field codes and no STP specification version, so the skill
keeps the field names and codes unverified until the specification is read.

## AAS-4: NSW Payroll Tax Act 2007

The whole in-force text was retrieved from
<https://legislation.nsw.gov.au/view/whole/html/inforce/current/act-2007-021>
(reprint publication date 10 June 2026 in the page metadata). The browser
view's automated extract misquoted s 32(2), so only the downloaded text was
relied on.

| Skill statement | Act text | Change |
| --- | --- | --- |
| Division 8 of Part 3 is ss 37 to 40 | Division 8 runs from s 36A to s 42 | Corrected |
| Whether s 32(2) carves out a contract of service and an employment agency contract | s 32(2) excludes a contract of service; s 32(3) excludes an employment agency contract | Stated |
| Exempt-client relief under ss 40(2) and 60 | s 40(2) needs the client's declaration in the approved form; s 60 limits local government exemptions | s 60 removed |
| Groups under ss 70 to 74 | ss 70, 71, 72, 73 and 74 match; s 74A adds groups arising from former entities | s 74A added |
| Joint and several liability: check the provision | s 81 | Cited |
| s 79 exclusion only for s 71 to s 73 groups, on a "substantially independent" test | s 79(4) extends to s 74 groups; s 79(3) bars a body corporate related through Corporations Act s 50; s 79(8) bars s 74A groups; s 79(2) requires the business to be carried on independently of, and not connected with, any other member's business | Restated from the Act |

## AAS-3: Coal LSL eligible wages (checked 23 September 2026)

Source: *Coal Mining Industry (Long Service Leave) Payroll Levy Collection
Act 1992*, compilation C2026C00364 (compilation 12, in force from
1 September 2026, includes amendments up to Act No. 63, 2026), read from the
Word download on the Federal Register of Legislation Downloads tab
(SHA-256 `d6e3a5a442369e26ff33d4f2936d8a73d19f4de168b8dc2ae451aa0abc432bb7`).
The HTML text view still failed to load.

| Skill claim | Section 3B | Result |
| --- | --- | --- |
| Non-casual base-rate employee: greater of Formula A and Formula B | s 3B(1): greater of (a) base rate including incentive-based payments and bonuses, and (b) 75% of base rate including those payments, overtime or penalty rates, and allowances other than expense reimbursements | Matches |
| Base pay taken before salary sacrifice | s 3B(4)(a), (aa) and (b) | Matches |
| Incentives and bonuses count only if paid at least monthly | s 3B(4)(c) and (d) | Matches |
| Annual salary: include incentives and bonuses, exclude overtime, penalty rates and shift loading | s 3B(2) | Matches |
| Casual: base pay plus incentives, bonuses and a quantifiable casual loading; otherwise ordinary pay plus incentives and bonuses | s 3B(3)(a) and (b); (a) applies only where an industrial instrument covering the employee specifies a casual loading | Matches |
| Casual method from 1 January 2024 | Act No. 43, 2023, Schedule 6 item 17(4): the amendments apply to payments made on or after 1 January 2024 for service days on or after 1 January 2024 | Supported; item 17(4) supplies the payment-date and service-day boundary |
| Casual hours counted by payroll weeks ending in the month | Not in s 3B | Guidance only |
| Insurer-paid workers compensation or income protection excluded | Not in s 3B | Guidance only |

Schedule 1 clause 11(b) assumes s 3B(1)(b) never applied when working out
an unpaid levy payment arrangement; the skill already defers those terms to
a current-source read.

## Not resolved

- AAS-2 already requires the charge percentage, cap and rounding to be read
  from the applicable compilation at use time; no further check was made.
- AAS-5 concerns imported history, which a source check cannot restore.
