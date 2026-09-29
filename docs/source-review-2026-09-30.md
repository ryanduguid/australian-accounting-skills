# Source review, 30 September 2026

Ryan Duguid confirmed that he had reviewed the sources raised in issue #195 and that they were good. This records his review of the 50 records missing a baseline and the 5 records whose source text changed. These are 55 records across 27 skills and 45 distinct URLs.

The records' `checked_at` dates are now 30 September 2026. Existing `reverify_by` dates and substantive limitations remain. The review does not adopt a tax position for a particular taxpayer or extend a source beyond its applicable period.

## Retrieval evidence

The repository's source refresh code retrieved readable content for 44 URLs and recorded the corresponding 54 content and destination baselines. RevenueSA returned HTTP 403 to that fetcher. Its page loaded successfully in the local browser and Ryan's review covers it, but its previous machine digest remains until the fetcher can retrieve comparable content. No refusal is represented as a successful automated fetch.

The reviewed records then classified as 54 unchanged and 1 blocked, with no missing source, unreadable source, overdue review or missing baseline reported by that retrieval. This comparison uses the recorded responses; it does not predict a later page change.

- Queensland's page still states the 4.75% and 4.95% bands, $1.3 million threshold and regional discount reflected in the record. The mental health levy limitation remains.
- RevenueSA's page still states the existing payroll bands and registration threshold. Its table layout and the record's limitations remain relevant.
- The Federal Register API identifies ITAA 1997 compilation C2026C00400, compilation 267, starting 27 August 2026. The previous recorded observation, C2026C00324, remains historical evidence and does not identify the current compilation.
- The WIP Tally source URL still pins commit `f10086d0c99c77bb3dabd3a0fc08b9e5ab1b939a`. A change to the GitHub page digest does not by itself establish a change to that immutable source tree.

Issue #195 also lists blocked and unreachable sources outside these 55 records. This change does not remove those retrieval limitations or advance their human review dates.
