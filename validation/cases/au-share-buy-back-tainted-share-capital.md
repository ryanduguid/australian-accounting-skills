---
id: au-share-buy-back-tainted-share-capital
synthetic: true
target_skills:
  - au-share-buy-back
---

# A private company buys back shares after moving retained earnings into share capital

## Scenario

All records and figures below are fabricated from scratch. An invented private company that is not listed buys back part of one shareholder's ordinary shares off-market. Three years earlier it transferred an amount from retained earnings to its share capital account. The directors want to debit the average capital per share to share capital and frank the rest of the price as a dividend.

## Task

Use `au-share-buy-back` to prepare the share capital transfer and tainting record, the price split, the franking schedule for the franking account workflow and the unresolved-items hand-off.

## Synthetic inputs

The company has been an Australian resident since incorporation. Shares on issue before the buy-back: 100000. Share capital account history: 50000.00 from shares issued for cash on incorporation, then a journal 3 years before the buy-back transferring 150000.00 from retained earnings to share capital, for a balance of 200000.00. The journal narration reads "capitalise retained earnings"; no shares were issued with it and no debt was released. The company's records hold no choice to untaint the share capital account. Shares bought back: 10000 at 6.00 each, a total of 60000.00 paid in cash. The directors propose to debit 20000.00 to share capital and 40000.00 to retained earnings, and to frank the 40000.00 in full.

## Deliberately unavailable evidence

Only the supplied facts are available. A market valuation, the company's franking account balance and benchmark, the board minutes for the transfer, any lodged approved form and any private ruling are missing. No current rule text, ATO view or adviser decision is supplied.

## Required checks

- Record the 150000.00 transfer from retained earnings as one to which Division 197 of the *Income Tax Assessment Act 1997* applies unless an exclusion in ss 197-10 to 197-42 is evidenced, and record that the amount came from retained earnings, so nothing supplied shows it could always be identified as share capital (s 197-10), came from a debt/equity swap (s 197-15), a share premium account or capital redemption reserve (s 197-20), an option premium reserve on the exercise of options (s 197-25) or a demutualisation (ss 197-30 to 197-40), or was transferred in connection with creating exploration credits (s 197-42).
- Record that the transfer taints the share capital account until the company makes an irrevocable untainting choice in the approved form given to the Commissioner (ss 197-50 and 197-55), and that none is in the records.
- State that a tainted account is not a share capital account for s 159GZZZP of the *Income Tax Assessment Act 1936* (s 975-300(3)), so if the account is tainted the 20000.00 debit does not reduce the dividend and the whole 60000.00 is a dividend, of which the 20000.00 sourced from share capital is unfrankable (ss 202-45(e) and 975-300(3)(ba)).
- Show the directors' split (20000.00 capital and 40000.00 dividend) beside the tainted result (60000.00 dividend, 20000.00 of it unfrankable), and mark the split and the frankable amount `UNVERIFIED` until the reviewer settles tainting and market value.
- Route to the franking account workflow the franking debit on the transfer (item 7A of the s 205-30 table) and, should the company untaint, the possible further debit (s 197-65 and item 7B) and untainting tax (s 197-60), stated as conditional.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not treat the 20000.00 share capital debit as reducing the dividend, or frank any part of the price, before the reviewer settles tainting.
- Do not recommend making or not making an untainting choice, or choose the split or the franking percentage.
- Do not state a rule, rate or deadline from memory, or post, lodge, pay or communicate anything.

## Source-verification and reviewer boundary

Use Division 16K of Part III of the *Income Tax Assessment Act 1936*, Division 197 and ss 202-45, 205-30 and 975-300 of the *Income Tax Assessment Act 1997*, and PS LA 2007/9 for the actual period. Preserve unresolved review flags. The directors decide the buy-back and any untainting choice, and a registered tax agent decides each tax position. This is not tax, legal or financial advice or an assurance engagement.
