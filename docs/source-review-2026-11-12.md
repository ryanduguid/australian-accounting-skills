# Source check, 12 November 2026

An agent read the sources behind the 35 actionable rows of the source sweep run from a residential connection on 12 November 2026 (main `00e3b16`). This is not a human review. No `checked_at`, `fact`, `reviewed_content`, `reverify_by` or `manual_review` value on an existing record changed. Each existing record whose source was read carries a dated note in `limitations` ending 'Human review pending'; the added and repointed records say instead, as new records do, that human source approval remains pending. Each changed page's current reading is stored as a `pending_review` candidate by `python scripts/source_refresh.py --write`, for a person to accept under [source preflight](source-preflight.md). Skill text changed on the strength of these readings carries a visible 'Human review pending' flag.

## Unreadable: 8 Xero Central pages

The sweep attributed these rows to a fault in `scripts/source_refresh.py`. That is not the cause. Each of the 8 URLs returns HTTP 200 with a Salesforce Lightning Web Runtime shell: a `<webruntime-app>` element with no text, title or published date, whose article arrives later by script. No HTML text extraction can read it. The 5 `xero-exports` records already said so; the 2 `statement-to-csv` records and the `au-aml-ctf-client-coverage` record now do too. The sweep will keep listing these rows as unreadable until a person reviews them in a browser and decides how they are tracked.

## Rows

| Outcome | Skill | Source | Finding | Change |
| --- | --- | --- | --- | --- |
| changed | `au-company-tax` | ATO: tax loss carry back (last updated 3 November 2026) | The page and Division 160 as substituted by Act No. 71 of 2026 test whether the entity is a significant global entity; the recorded fact and the skill said a turnover threshold | Step 3 corrected and flagged; the fact is left for the reviewer |
| changed | `au-division-296` | ATO: how Division 296 tax is calculated (3 November 2026) | Fact still stated; the example's rate error is fixed and the drafting note is gone | Note only |
| changed | `au-franking-account` | The Exchequer Tally on GitHub | Commits since 2 November change README wording, headers and the licence only | Note only |
| changed | `au-gst-registration-review` | ATO registering for GST (14 September 2026) | Turnover tests unchanged; the page now opens directly (HTTP 200) | Note only |
| changed | `au-payroll-tax-states` | RevenueWA payroll tax calculation (2 June 2026) | Rate, diminishing threshold band and full-rate row unchanged; changed passage not located | Note only |
| changed | `au-payroll-tax-states` | RevenueSA rates and thresholds | Bands, registration threshold and maximum deduction unchanged; the page now returns HTTP 200 | Note only |
| changed | `au-restructure-rollovers` | ATO: minimum tax on discretionary trusts (3 November 2026) | Still not law; now links the Tax Reform No. 3 and minimum tax Bills | Note only |
| changed | `au-return-amendment` | ATO amendment time limits (content address) | The address returns a print PDF of the whole 'Your tax return' section, not the time-limits page | Skill now links 'Time limits on tax return amendments' (new pending record); old record kept with a note |
| changed | `au-short-stay-accommodation` | ITAA 1997 s 26-31 | Text matches compilation No 268; the digest change is page furniture | Note only |
| changed | `au-short-stay-accommodation` | ITAA 1997 s 40-27 | S 40-27(4)(c)(ii) now uses the defined term 'real property' (No 86 of 2026). The skill's check covered only second-hand assets, but s 40-27(2)(d) also reaches assets used in the owner's residence or for a non-taxable purpose | Step 5 widened and flagged |
| changed | `au-short-stay-accommodation` | GST Act s 11-15 | Text matches compilation No 96 | Note only |
| changed | `au-smsf-year-end` | ATO caps, limits and tax on super contributions | Now an index page, including Division 296 | Note only |
| changed | `au-super-contribution-caps` | ATO concessional contributions cap (2 July 2026) | Fact still stated in full | Note only |
| changed | `au-tax-research` | TR 2006/10 | Consolidated version of 25 February 2026; paragraph 30 unchanged | Note only |
| changed | `au-travel-expenses` | ATO travel allowances (24 September 2025) | Withholding conditions unchanged; lists determinations only to TD 2025/4 | Note only |
| changed | `au-trust-deed-review` | ATO family trusts (10 November 2026) | Passages the skill relies on still stated | Note only |
| changed | `au-trust-distributions` | ATO family trusts (10 November 2026) | Passages step 4a relies on still stated | Step 4a's page date updated |
| changed | `au-wfh-deductions` | ATO standard deduction (2 November 2026) | Fact still stated; the page adds the award transport exemption to the removed exceptions, a laundry approach and a low-value pool exclusion | Note only |
| changed | `au-working-holiday-makers` | ATO STP income types (23 October 2026) | WHM rules unchanged; now served at the record's own address | Note only |
| changed | `contractor-super-tpar` | SGD 2026/D1 | Still a draft; comment period closed 2 October 2026 | Note only |
| changed | `statement-to-csv` | OWASP CSV Injection | Guidance unchanged; its GitHub source last changed 29 January 2026 | Note only |
| changed | `stp-finalisation` | ATO finalising STP data (23 October 2026) | 14 July deadline unchanged; now served at the record's own address | Note only |
| changed | `wip-over-under-billing` | The WIP Tally at a pinned commit | Pinned content cannot change; the digest change is GitHub page furniture | Note only |
| changed | `wip-over-under-billing` | ASIC large or small proprietary company | Thresholds unchanged; the page now notes a consultation on raising them, not yet in effect | Note only |
| missing | `au-trust-distributions` | ATO: Increased visibility for trust elections | HTTP 404, no archived copy, and no live page lists the report's fields; the ATO bulletin extending GIC remission for FTDT describes the report's 18 April 2026 enhancement | Record repointed to the bulletin; step 4a states only what the bulletin says; test updated |
| review-due | `au-client-acceptance` | TPB(GS) 54/2024 (last modified 22 July 2026) | Section 45 matters unchanged since the 29 September reading | Note only |
| review-due | `au-client-acceptance` | AUSTRAC customer due diligence | Index unchanged. Section 29 of the Act (compilation C2026C00447) is headed 'Exemptions from initial customer due diligence' but lets the service start before due diligence is complete, with due diligence to follow; AUSTRAC calls this delayed initial customer due diligence | Step 6 now says what section 29 allows, and is flagged |
| unreadable | `au-aml-ctf-client-coverage`, `statement-to-csv` (2), `xero-exports` (5) | Xero Central | Script-built page shell, as above | Note on the 3 records that lacked one |

## For the reviewer

- Accepting a candidate follows [source preflight](source-preflight.md): read the source, then update `fact`, `checked_at` and the review deadlines, bind the `pending_review` fields and remove the marker. The `au-company-tax` loss carry back fact still states the turnover test and needs correcting at that review.
- The 2 `au-client-acceptance` records stay review-due until a person sets `checked_at` and `manual_review.next_review`.
- The `au-gst-registration-review` record for registering for GST still has `verification_status` `unavailable-http-403` and a title saying direct access was unavailable, though the page now opens directly.
- The old `au-return-amendment` content address is no longer linked from the skill; keep or remove it.
- The ATO bulletin still links the removed trust elections page, so the ATO may republish it; recheck before relying on the repointed record.
