# Source review, 14 October 2026

Ryan Duguid confirmed on 14 October 2026 that he had reviewed the 114 actionable records raised in issue #213 by the 11 October sweep and found no errors: 10 records whose source text changed, 94 on hosts that refuse automated retrieval and 10 that timed out. These span 53 skills and 102 distinct URLs.

The records' `checked_at` dates are now 14 October 2026. Facts, limitations, `reverify_by` dates and verification statuses are unchanged. Each fact keeps the date of the reading it describes. The review does not adopt a tax position for a particular taxpayer or extend a source beyond its applicable period.

## Retrieval evidence

On 14 October the repository's source refresh code retrieved readable content for 8 of the 9 changed URLs, and the 9 records using them were accepted under [source preflight](source-preflight.md): each now carries the new baseline and a matching `reviewed_content` binding. RevenueSA returned HTTP 403 to that fetcher, as it did on 30 September. Ryan's review covers that page, but its previous machine digest remains until the fetcher can retrieve comparable content.

The 104 blocked and unreachable records keep their existing digests. Their review dates moved because a person read them; the network limitations remain, and a later sweep will report them again.

The Federal Register's current versions of the Income Tax Assessment Act 1997 and the Taxation Administration Act 1953 start on 1 October 2026 with unincorporated amendments and no compilation identifier, as the 12 October draft review on issue #213 recorded. Those records' facts and limitations already describe their compilation dates and do not establish the law for a later period.
