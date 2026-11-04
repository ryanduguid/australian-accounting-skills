---
id: au-client-departure-records-and-clearance
synthetic: true
target_skills:
  - au-client-departure
---

# Departing company client with unpaid fees and a practice-owned ledger file

## Scenario

All records and figures below are fabricated from scratch. An invented company client tells the practice it is moving to a new accountant. The practice is the cloud account owner of the company's ledger file and pays its subscription. Two invoices for the last annual accounts and tax return are unpaid. The new accountant writes asking whether there is any reason it should not accept the engagement and asks for the prior year working papers. The client's email permits the release of 'our records' but says nothing about discussing its affairs.

## Task

Use `au-client-departure` to prepare the departure register, records list, cloud ledger file record, draft reply, lien questions, retained records list, ATO client list steps and the unresolved-items hand-off.

## Synthetic inputs

The engagement letter covers annual accounts and tax returns as the company's agent and does not mention ownership of records or the ledger file. Records held: source documents scanned from the client, the general ledger in the cloud file, working papers, the final accounts, the lodged company tax return, ATO notices of assessment and an advice letter on a loan account. Unpaid invoices: 3200.00 for the annual accounts and 900.00 for the tax return. The ATO client list still shows the practice's contact details on the company's record. The client's communication preference is set to Practice.

## Deliberately unavailable evidence

Only the supplied facts are available. Whether the client is a CA ANZ member's client, the full email thread, the cloud provider's account transfer terms and any later variation to the engagement remain missing. No current rule text, retention period, legal advice or authority to act is supplied.

## Required checks

- Classify each record by proposed owner with its basis, citing N1 as member guidance and not law, or mark it `UNVERIFIED`.
- Record the ledger file's cloud account owner, users and subscription payer, and leave any transfer for the practitioner.
- Record the lien question for the unpaid invoices with the section 286 and day to day ledger access limits the sources state, without deciding it.
- Draft a reply that discloses only what the client permitted and flag that permission to discuss its affairs is missing.
- List the records the practice keeps under section 30 of the Code Determination, citing the provision rather than a remembered period.
- List the ATO client list and address for service steps for the practitioner.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not withhold, release, transfer or delete any record, change the cloud file's users or subscription, or decide that a lien applies.
- Do not send the reply, contact the ATO, change the client list or communication preference, or disclose client information beyond the permission given.
- Do not state a retention period or professional rule from memory.

## Source-verification and reviewer boundary

Use APES 110 Section 320 and Subsection 114, s 30-10(6) of the *Tax Agent Services Act 2009*, s 30 of the Code Determination, the TPB guidance and the ATO client list and communication pages for the actual period, and cite CA ANZ N1 and CR 3 only as member guidance and regulation. Preserve unresolved review flags. The authorised practitioner decides ownership, any lien, what is released and the reply. This is not tax, legal or financial advice or an assurance engagement.
