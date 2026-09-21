# Source record verification, 21 September 2026

This check addresses the two changed records in issue 138. It uses public
Federal Register of Legislation material and no client data. It checks source
identity and the provisions supporting the workflows, without deciding a tax
position. Existing human `checked_at` dates and discovery-only verification
statuses remain unchanged.

## Property GST

The [GST Act text view](https://www.legislation.gov.au/C2004A00446/latest/text)
served compilation C2026C00081, compilation 96 dated 1 January 2026. This is the
same compilation identified by the existing skill reference.

The rendered volume 1 text was inspected at s 75-20 and ss 11-5, 11-15 and
11-20. It supports the existing distinction between a property acquisition
under the margin scheme and construction or other separate costs. No workflow
rule or tax amount changes.

The old response body is not stored, so the exact text that changed in the
whole-page digest cannot be reconstructed. A changed page digest does not
establish a legislative amendment. The scoped digest is refreshed only after
checking the compilation identity and the provisions used by the skill.

## SMSF contributions

The former `C1997A00038` URL redirected to the Register home page with a
title-loading error in the browser. Its HTTP 200 response and stored digest
were not evidence that the Act had been retrieved.

The correct [Income Tax Assessment Act 1997 title](https://www.legislation.gov.au/C2004A05138/latest/text)
is `C2004A05138`. The Register served compilation C2026C00324, compilation 266
dated 1 July 2026. Its [volume 6](https://www.legislation.gov.au/C2004A05138/2026-07-01/2026-07-01/text/1/epub/OEBPS/document_6/document_6.html)
contains the relevant provisions:

- Section 291-20(3)-(7) covers the use and ordering of unused concessional
  contribution amounts from earlier years.
- Section 292-85(2)-(7) covers the non-concessional cap and the bring-forward
  conditions and periods.

These provisions support the workflow's separate checks for the two
concessions. The source record now points to the actual Act and identifies the
retrieved compilation. No cap amount or eligibility conclusion is adopted.

The Register labelled this compilation latest while displaying the period
1 July 2026 to 26 August 2026. That display is not evidence of the operative law
for a later transaction. The preparer must still check the relevant period,
subsequent amendments and application rules before relying on either concession.

## Coverage limits

Only these two legislative records were substantively checked. The blocked and
unreachable sources in issue 138 remain unverified by this work. HTTP retrieval
and digest refresh dates do not replace human review or professional judgement.
