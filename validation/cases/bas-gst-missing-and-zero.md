---
id: bas-gst-missing-and-zero
synthetic: true
target_skills:
  - bas-preparation
  - xero-exports
---

# Missing GST and legitimate zero amounts

## Scenario

Synthetic Entity A requests a transaction-only GST review of fabricated tax-rate
detail. All amounts are AUD, GST-inclusive where applicable. An isolated
arithmetic exercise supplies a 10% rate; current legal treatment still needs
primary-source verification for the engagement's period.

## Task

Review every detail, separating treatment, buyer entitlement and attribution.
Identify supported omissions and legitimate zero amounts without a full BAS
readiness conclusion.

## Synthetic inputs

| Row | Direction | Gross | Recorded GST | Supplied facts |
|---|---|---:|---:|---|
| A | Sale | 110.00 | 0.00 | Domestic ordinary service in Entity A's enterprise, supplier registered, consideration received in period; no exemption facts |
| B | Purchase | 220.00 | 0.00 | Same service type from registered supplier; valid invoice held and supplied, wholly creditable business use, fully paid in period |
| C | Sale | 330.00 | 0.00 | Export claimed by description only; no export or recipient evidence |
| D | Other | 55.00 | 0.00 | Transfer between Entity A's own cash accounts; no consideration for a supply |
| E | Purchase | 110.00 | 10.00 | Ordinary domestic service from registered enterprise supplier, valid tax invoice held and supplied, wholly creditable business use, fully paid in period |

The entity is registered on the cash basis. Both statement views are supplied
and independently linked; D appears only in the complementary full GL population.
No payroll or prior-period comparison is requested.

Handover mutation: the folder also uses the full-BAS gate's recognised filenames,
but its supplied gate result is `NOT_READY` because payroll evidence is missing.
Compare a transaction-only request with a full-BAS preparation request using the
same files. The gate result itself is supplied evidence, not an executed test.

## Deliberately unavailable evidence

- No export support for C or organisation mapping for its custom zero code.
- No primary authority packet or statement label set is supplied.
- No authority to change a ledger or lodge.

## Required checks

- Account for all five details and distinguish statement coverage from the GL.
- Verify treatment, entitlement and attribution before concluding A/B are
  supported omissions; conditional arithmetic at the supplied rate is 10.00
  sale GST and 20.00 purchase GST. Keep sales and credits separate.
- Retain C unresolved; its description does not establish GST-free treatment.
- Assess D using the actual transfer facts, not a blanket zero-code rule.
- Retain E as a positive control when its evidence and applicable authority
  support treatment, entitlement and attribution; do not flag every purchase.
- Continue transaction work without requesting unrelated payroll reports.
- In the handover mutation, deliver the scoped register and retain the unchanged
  full-BAS gate status separately. In full-BAS mode, preserve the missing payroll
  as a full-pack deficiency rather than asserting readiness.

## Must not do

- Do not regard every zero amount as an error or turn missing facts into zero.
- Do not infer current legal treatment from the supplied arithmetic rate.
- Do not combine duplicate report views, post or lodge.

## Source-verification and reviewer boundary

Verify applicable primary authority and retain unsupported legal conclusions as
unverified. An authorised reviewer decides treatment and any corrections. The
case does not establish accuracy on a named model or client.
