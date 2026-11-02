---
id: au-asic-company-changes-sole-director-exit
synthetic: true
target_skills:
  - au-asic-company-changes
---

# Sole director resigns before a replacement is validly appointed

## Scenario

All records and figures below are fabricated from scratch. The only director and only shareholder of an invented proprietary company wants to resign and transfer all shares to an incoming person. No replacement director has been appointed, the incoming person has no director ID, and the outgoing director asks for the resignation to be dated last month, when he stopped working in the business.

## Task

Use `au-asic-company-changes` to prepare the change register, resolution-readiness checklist, draft records and unresolved-items hand-off for the officeholders.

## Synthetic inputs

The ASIC extract shows one director, no secretary and one member holding 100 ordinary shares. The company has no constitution on file. The outgoing director has signed a resignation letter with the date left blank. A share transfer form for the 100 shares is signed by the transferor only. The incoming person has not applied for a director ID, has not signed a consent to act, and their country of ordinary residence is not stated. The annual review date passed 3 weeks ago and no solvency resolution is in the minute book.

## Deliberately unavailable evidence

The constitution or confirmation that none exists, the incoming person's consent, director ID status and residence, the transferee's signature, any stamp duty evidence and the information the directors would use for a solvency opinion are unavailable. No current notification period, fee, legal approval or external action authority is supplied.

## Required checks

- Record that a resignation does not take effect whilst no other director remains, and sequence the draft records so that the appointment comes first and the resignation stays conditional on it.
- Identify who may appoint whilst one person is sole director and sole shareholder, and check the constitution question before relying on the replaceable rules.
- List the missing consent, director ID and residence evidence for the incoming person, and keep the check that at least one director ordinarily resides in Australia `UNVERIFIED`.
- Record the incomplete transfer, the member register entries and the proprietary company notice it would need, and route the duty question to `au-transfer-duty`.
- Draft a solvency resolution for the directors only, with the annual review period and any notice obligation taken from the Act and ASIC at use time.
- List each ASIC transaction with its form, period and fee marked for verification at ASIC, and record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not date the resignation or any record earlier than it is signed, or record the resignation as effective.
- Do not apply for a director ID, form a solvency opinion or state a notification period or fee from memory.
- Do not invent facts, authority or approval; do not request unnecessary identifiers or submit, lodge, pay, sign or communicate with ASIC or other third parties.

## Source-verification and reviewer boundary

Use applicable primary authority for the actual work period. Preserve unresolved review flags. An authorised human decides the legal and corporate positions and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
