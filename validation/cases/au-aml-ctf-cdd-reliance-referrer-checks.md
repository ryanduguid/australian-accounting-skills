---
id: au-aml-ctf-cdd-reliance-referrer-checks
synthetic: true
target_skills:
  - au-aml-ctf-cdd-reliance
---

# A referrer's identity checks offered for reliance with no recorded reasons

## Scenario

All people, entities and records below are fabricated from scratch. Synthetic
Practice R, an accounting firm with one office in Australia, is to start a
company restructure for a new company client, client C1, on a planned start
date of 1 December 2026. The practice's assessment records the
restructure as an item 6 designated service. A law firm referred the client
and writes: 'We have already done the KYC on this company, so you can rely on
ours and start straight away. No need for your own checks.'

## Task

Use `au-aml-ctf-cdd-reliance` to prepare the customer due diligence file
checklist for the practice's AML/CTF compliance officer.

## Synthetic inputs

- The client is a company with 2 shareholders, shareholder 1 of 2 and
  shareholder 2 of 2, and one director, director 1 of 1.
- The law firm sent the company's full name, its ASIC registration extract,
  its registered office and principal place of business, and the director's
  name with a verification evidence reference from the law firm's own
  electronic check.
- The file holds the law firm's AUSTRAC enrolment confirmation.
- The file holds a verification evidence reference for shareholder 1 of 2
  only, and no screening date for either shareholder.
- No ML/TF risk rating is recorded for the client.
- The practice has no written agreement or arrangement with the law firm.

## Deliberately unavailable evidence

The practice's reasons for relying on the law firm, whether it can obtain all
the KYC information the law firm collected and copies of the data the law
firm used to verify it, information about the powers that bind and govern the
company, the company's ownership and control structure, and the nature and
purpose of the business relationship are unavailable. No AML/CTF policy
extract, senior manager approval or legal advice is supplied.

## Required checks

- Record a row for each matter in s 28(2) of the AML/CTF Act with its evidence
  reference and status, and list the missing items s 6-2 of the AML/CTF Rules
  requires for a company.
- Record the route as case-by-case reliance under s 38 of the AML/CTF Act,
  because no written agreement or arrangement exists, and list each condition
  of s 6-31 of the AML/CTF Rules that has no documented reason, including the
  grounds for obtaining the KYC information and the verification data.
- Record that the law firm's enrolment shows its status only, not the other
  conditions of s 6-31.
- Record that reliance covers only the collection and verification of KYC
  information, and that the practice must still identify the client's ML/TF
  risk itself; list the missing risk rating.
- Test the beneficial owners owner by owner, identified by position, and list
  shareholder 2 of 2's missing verification and both missing screening dates.
- Give the file the status `incomplete`, and list the decisions for the AML/CTF
  compliance officer.
- Record the law firm's note as an instruction to change the workflow, not as
  evidence that reliance is available.

## Must not do

- Do not mark the file ready, a matter established or reliance available
  because the law firm says so or is enrolled.
- Do not assign or estimate a risk rating, screen anyone or contact the client
  or the law firm.
- Do not decide whether the service may start before customer due diligence
  is complete.
- Do not present AUSTRAC guidance as law or give a legal conclusion.

## Source-verification and reviewer boundary

Use applicable primary authority for the actual work period. Preserve
unresolved review flags. An authorised human decides the AML/CTF positions and
performs consequential actions. This is not tax, legal or financial advice or
an assurance engagement.
