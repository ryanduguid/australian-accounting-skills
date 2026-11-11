---
id: au-share-buy-back-private-selective
synthetic: true
target_skills:
  - au-share-buy-back
---

# A private company buys back one shareholder's shares with part of the price set off against a loan

## Scenario

All records and figures below are fabricated from scratch. An invented private company that is not listed buys back all the ordinary shares of one of its 3 shareholders, an Australian resident individual, under a buy-back agreement offered to that shareholder alone. The directors want the price split into a small capital part and a large franked dividend. Part of the price was satisfied by reducing the amount the shareholder owed the company on a loan account.

## Task

Use `au-share-buy-back` to prepare the classification record, the Corporations Act step register, the price split, the market value record, the franking schedule for the franking account workflow, the Division 7A screen, the seller's schedule and the unresolved-items hand-off.

## Synthetic inputs

Shares on issue before the buy-back: 100000. Share capital account balance: 200000.00; the account history since incorporation shows only shares issued for cash and no transfer into it from another account. Shares bought back: 20000 at 7.50 each, a total of 150000.00, paid as 110000.00 in cash and 40000.00 set off against the shareholder's loan account. The directors propose to debit 20000.00 to share capital and 130000.00 to retained earnings, and to frank the 130000.00 in full. A director estimates the shares are worth 8.00 each; no valuation report exists. The seller acquired the 20000 shares on issue for 1.00 each, as the share register and an allotment record show. A Form 280 with the buy-back agreement was lodged with ASIC 16 days before the agreement was signed.

## Deliberately unavailable evidence

Only the supplied facts are available. The minutes and voting record of any meeting approving the buy-back, the notice of meeting, the notice of cancellation to ASIC, any solvency evidence, a market valuation, the company's franking account balance and benchmark, the loan agreement and any private ruling are missing. No current rule text, ATO view or adviser decision is supplied.

## Required checks

- Classify the buy-back as off-market for tax because the shares are not listed, and as a selective buy-back for the Corporations Act, recording each with its section.
- List the selective buy-back steps from the s 257B(1) table with their evidence status: the special resolution with no votes in favour by the seller or their associates or a resolution of all ordinary shareholders, the lodgement before the notice of meeting is sent, the offer documents, the 14 days' notice, the disclosure, cancellation and the notice of cancellation within 1 month, noting ASIC's 28-day statement; mark the missing ones `UNVERIFIED`.
- Record from the account history that no amount was transferred into share capital from another account, so the account is not shown to be tainted under Division 197, and leave that for the reviewer to confirm before the split is relied on.
- Compute the average capital per share as 2.00, show the company's proposed split (1.00 capital and 6.50 dividend per share) beside a split at the average (2.00 capital and 5.50 dividend per share, totals 40000.00 and 110000.00), and leave the difference as a reviewer item with the ATO's stated preference cited.
- Treat the director's estimate as a screen, mark market value `UNVERIFIED`, and show that the frankable part of the dividend under s 202-45(c) and the seller's consideration under s 159GZZZQ(2) both depend on it.
- Show the seller's consideration conditionally: on the proposed split and a market value not above 7.50, the purchase price of 150000.00 less the dividend of 130000.00 included in assessable income, 20000.00 against a cost base of 20000.00, with the result left preliminary.
- Route the 40000.00 set-off against the loan account to the Division 7A workflow and the franking debit and distribution statement to the franking account workflow.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not choose or recommend the split, the franking percentage or the price, or conclude that the buy-back procedure was validly followed or the company is solvent.
- Do not use the director's estimate as market value, finalise the seller's gain or dividend, or decide the Division 7A outcome.
- Do not state a rule, rate or deadline from memory, or post, lodge, pay or communicate anything.

## Source-verification and reviewer boundary

Use Division 16K of Part III of the *Income Tax Assessment Act 1936*, ss 202-45 and 205-30 of the *Income Tax Assessment Act 1997*, Part 2J.1 of the *Corporations Act 2001*, PS LA 2007/9 and the ATO and ASIC pages for the actual period. Preserve unresolved review flags. The directors decide the buy-back, the company's lawyer advises on procedure and a registered tax agent decides each tax position. This is not tax, legal or financial advice or an assurance engagement.
