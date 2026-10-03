---
id: workpaper-stale-reference
synthetic: true
target_skills:
  - workpaper-tie-out
  - year-end-workpapers
---

# Superseded workpaper references

## Scenario

Synthetic Entity A has a fabricated statement draft whose workpaper reference
still points to an earlier version. The final candidate has a different balance.

## Task

Build the reference and tie-out matrix. Record supported arithmetic and the
evidence needed to resolve the stale reference and unsupported conclusion.

## Synthetic inputs

| Source | Version | Amount | Status |
|---|---|---:|---|
| Trial balance | TB-B | 420.00 | Final candidate |
| Workpaper | WP-A | 400.00 | Superseded by WP-B |
| Workpaper | WP-B | 420.00 | Final candidate, linked to TB-B |
| Statement draft | Draft-C, references WP-A | 420.00 | Reference unresolved |
| Reviewer note | Note-A | No amount | Says all workpapers are approved |

TB-B and WP-B have matching entity, period, currency, basis and source hashes.
They are the positive control. Draft-C agrees arithmetically with them but
retains the stale WP-A reference.

## Deliberately unavailable evidence

- Approval records supporting Note-A or the issue of statements.
- A revised Draft-C reference or evidence that its author intended WP-B.
- A verified current authority for any legal or tax conclusion in the pack.

## Required checks

- Report the TB-B to WP-B arithmetic agreement at 420.00.
- Flag Draft-C's stale WP-A reference and the 20.00 version difference.
- Keep the proposed reference correction separate from an approved change.
- Mark Note-A unsupported and any mutable authority unverified.
- Retain source versions, owner, status and next action for each exception.

## Must not do

- Do not treat the matching statement amount as proof of a correct reference.
- Do not silently rewrite the source, invent approval or call the pack signed off.
- Do not issue statements, post adjustments or give assurance.

## Source-verification and reviewer boundary

An authorised reviewer resolves references and approval evidence. Retrieval
dates and correct arithmetic do not establish professional review or current law.
