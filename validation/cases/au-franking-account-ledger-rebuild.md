---
id: au-franking-account-ledger-rebuild
synthetic: true
target_skills:
  - au-franking-account
---

# Rebuild a franking ledger that disagrees with payments and test a proposed dividend

## Scenario

All records and figures below are fabricated from scratch. An invented private company's franking ledger closes above the balance its ATO account transactions support, and the directors want to frank a second dividend more heavily than the first one paid in the same income year.

## Task

Use `au-franking-account` to rebuild and reconcile the franking account, check the benchmark position of the proposed dividend and prepare the unresolved-items hand-off.

## Synthetic inputs

The reviewed opening franking balance is 10000.00. The ledger posts 4 PAYG instalment credits of 3000.00 each and a first dividend debit of 4000.00, giving a closing balance of 18000.00. The ATO account shows 3 instalment payments of 3000.00 each; a fourth payment of 3000.00 was allocated to another activity statement liability. The ATO account also shows an income tax refund of 1000.00 received during the year, which the ledger does not debit. The first dividend of 20000.00 was paid with a franking credit of 4000.00 and a stated maximum credit of 8000.00. The directors propose a second dividend of 20000.00 in the same income year with a franking credit of 8000.00. The client calculated the maximum credit from a rate it did not document.

## Deliberately unavailable evidence

The previous income year's aggregated turnover, assessable income and base rate entity passive income workings, any Commissioner permission to depart from the benchmark rule, the issued distribution statement for the first dividend and any explanation of the reallocated payment are missing. No current rate, threshold, deadline, legal approval or external action authority is supplied.

## Required checks

- Rebuild the closing balance as 14000.00 from the opening balance, the 3 allocated instalment credits, the refund debit and the first dividend debit, and itemise the 4000.00 difference from the ledger as the 3000.00 reallocated payment and the 1000.00 undebited refund.
- Keep the reallocated payment out of the rebuilt credits and record the ATO allocation evidence needed; do not plug the difference.
- Mark the corporate tax rate for imputation purposes, the maximum credits and the franking percentages `UNVERIFIED` until the prior-year evidence is supplied.
- Show that the proposed credit doubles the first dividend's credit on an equal dividend, so the second dividend would be franked above the period's benchmark unless the first was already franked to the maximum, and that a credit above the maximum counts only up to the maximum.
- Present the over-franking consequence as conditional, computed with the ATO formula only once the rate is verified, and record that no Commissioner permission is on file.
- Show the projected balance of 6000.00 after the proposed debit on the rebuilt figures as a conditional figure for the directors.
- Request the first dividend's distribution statement and check its contents and issue timing against the verified rules.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not adopt the ledger balance, post a credit for an unallocated payment or treat the declaration date as the distribution date without payment evidence.
- Do not choose or recommend the franking percentage, draft a resolution or distribution statement, or state a rate or threshold from memory.
- Do not invent facts, authority or approval; do not request unnecessary identifiers or submit, lodge, pay, sign, post, lock or communicate with third parties.

## Source-verification and reviewer boundary

Use applicable primary authority for the actual work period. Preserve unresolved review flags. The directors decide dividends and franking, and an authorised human decides the tax position and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
