# How each skill was verified

Generated from [coverage.json](../coverage.json) by `accounting-skills build-coverage --write`. Its `--check` mode fails when this page disagrees with the tree.

Totals: 107 skills, 742 indexed primary sources of which 341 have a recorded human review, 5 skills exempt from source indexing, 17 skills with an unreachable source, 13 skills with a source changed since review, 82 skills with a confirmed pass, 0 skills with a confirmed fail and 2 skills with a confirmed verdict whose rubric digest does not match the current card.

- **Sources**: primary sources in the skill's `sources.json`, or 'exempt' for a skill with a recorded exemption.
- **Earliest review**: the oldest date on which a person recorded reading one of those sources, then how many of them carry a review date at all. A source with no review date has not been reviewed. A fetch is not a review.
- **Unreachable**: sources whose last fetch did not return HTTP 200 and that have no manual review record.
- **Changed since review**: sources that published a change after their last review.
- **Cards**: fabricated [validation cards](../validation/README.md) that target the skill. It is a count of cards, not of runs.
- **Confirmed pass** and **Confirmed fail**: those cards with a human-confirmed verdict in [validation/results](../validation/results/) whose recorded rubric digest matches the card as it is now. A pass shows that a model passed the card's rubric on one run, not that the skill's content is correct.
- **Non-current digest**: cards with a human-confirmed verdict whose recorded rubric digest does not match the card as it is now. The build does not check the card's history, so this says only that the digests differ. Such a verdict does not count as a pass or fail; a verdict that matches the current card, if there is one, is counted in its own column.
- **Legacy records**: `2026-09-06-claude-opus-5.json` and `2026-09-08-codex.json` predate the confirmed status and state no input mode, so the columns leave them out. They record a fail for `export-manifest-rounding` (`2026-09-08-codex.json`).

| Skill | Sources | Earliest review | Unreachable | Changed since review | Cards | Confirmed pass | Confirmed fail | Non-current digest |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [`au-aml-ctf-client-coverage`](../.claude/skills/au-aml-ctf-client-coverage/SKILL.md) | [13](../.claude/skills/au-aml-ctf-client-coverage/sources.json) | 2026-10-14 (6 of 13) | 4 | 0 | 4 | 1 | 0 | 0 |
| [`au-asic-company-changes`](../.claude/skills/au-asic-company-changes/SKILL.md) | [10](../.claude/skills/au-asic-company-changes/sources.json) | 2026-11-02 (10 of 10) | 0 | 0 | 1 | 1 | 0 | 0 |
| [`au-ato-account-reconciliation`](../.claude/skills/au-ato-account-reconciliation/SKILL.md) | [6](../.claude/skills/au-ato-account-reconciliation/sources.json) | none (0 of 6) | 0 | 0 | 2 | 0 | 0 | 0 |
| [`au-ato-correspondence-triage`](../.claude/skills/au-ato-correspondence-triage/SKILL.md) | [4](../.claude/skills/au-ato-correspondence-triage/sources.json) | none (0 of 4) | 0 | 0 | 2 | 0 | 0 | 0 |
| [`au-ato-objection`](../.claude/skills/au-ato-objection/SKILL.md) | [9](../.claude/skills/au-ato-objection/sources.json) | 2026-11-02 (7 of 9) | 0 | 0 | 1 | 1 | 0 | 0 |
| [`au-ato-penalties-interest`](../.claude/skills/au-ato-penalties-interest/SKILL.md) | [9](../.claude/skills/au-ato-penalties-interest/sources.json) | 2026-09-30 (6 of 9) | 0 | 0 | 3 | 2 | 0 | 0 |
| [`au-award-underpayment-review`](../.claude/skills/au-award-underpayment-review/SKILL.md) | [6](../.claude/skills/au-award-underpayment-review/sources.json) | 2026-11-02 (1 of 6) | 5 | 0 | 1 | 1 | 0 | 0 |
| [`au-bookkeeping`](../.claude/skills/au-bookkeeping/SKILL.md) | [6](../.claude/skills/au-bookkeeping/sources.json) | 2026-10-14 (1 of 6) | 0 | 0 | 6 | 2 | 0 | 0 |
| [`au-business-acquisition-review`](../.claude/skills/au-business-acquisition-review/SKILL.md) | [5](../.claude/skills/au-business-acquisition-review/sources.json) | 2026-11-02 (5 of 5) | 0 | 0 | 2 | 1 | 0 | 0 |
| [`au-business-formation`](../.claude/skills/au-business-formation/SKILL.md) | [2](../.claude/skills/au-business-formation/sources.json) | 2026-10-14 (1 of 2) | 0 | 0 | 1 | 1 | 0 | 0 |
| [`au-capital-gains`](../.claude/skills/au-capital-gains/SKILL.md) | [8](../.claude/skills/au-capital-gains/sources.json) | 2026-09-30 (7 of 8) | 0 | 0 | 3 | 2 | 0 | 0 |
| [`au-car-expenses`](../.claude/skills/au-car-expenses/SKILL.md) | [2](../.claude/skills/au-car-expenses/sources.json) | 2026-10-14 (2 of 2) | 0 | 0 | 2 | 1 | 0 | 0 |
| [`au-client-acceptance`](../.claude/skills/au-client-acceptance/SKILL.md) | [11](../.claude/skills/au-client-acceptance/sources.json) | 2026-09-29 (6 of 11) | 1 | 0 | 2 | 1 | 0 | 0 |
| [`au-client-departure`](../.claude/skills/au-client-departure/SKILL.md) | [9](../.claude/skills/au-client-departure/sources.json) | none (0 of 9) | 0 | 0 | 1 | 0 | 0 | 0 |
| [`au-client-email-triage`](../.claude/skills/au-client-email-triage/SKILL.md) | [1](../.claude/skills/au-client-email-triage/sources.json) | none (0 of 1) | 0 | 0 | 2 | 0 | 0 | 0 |
| [`au-client-letter`](../.claude/skills/au-client-letter/SKILL.md) | [1](../.claude/skills/au-client-letter/sources.json) | none (0 of 1) | 0 | 0 | 2 | 0 | 0 | 0 |
| [`au-client-meeting-note`](../.claude/skills/au-client-meeting-note/SKILL.md) | [6](../.claude/skills/au-client-meeting-note/sources.json) | none (0 of 6) | 3 | 0 | 2 | 0 | 0 | 0 |
| [`au-company-tax`](../.claude/skills/au-company-tax/SKILL.md) | [3](../.claude/skills/au-company-tax/sources.json) | 2026-09-30 (3 of 3) | 0 | 1 | 1 | 1 | 0 | 0 |
| [`au-cpi-rent-review`](../.claude/skills/au-cpi-rent-review/SKILL.md) | [7](../.claude/skills/au-cpi-rent-review/sources.json) | none (0 of 7) | 0 | 0 | 2 | 0 | 0 | 0 |
| [`au-crypto-tax`](../.claude/skills/au-crypto-tax/SKILL.md) | [5](../.claude/skills/au-crypto-tax/sources.json) | 2026-10-14 (1 of 5) | 0 | 0 | 2 | 1 | 0 | 0 |
| [`au-deceased-estates`](../.claude/skills/au-deceased-estates/SKILL.md) | [4](../.claude/skills/au-deceased-estates/sources.json) | 2026-10-14 (1 of 4) | 1 | 0 | 1 | 1 | 0 | 0 |
| [`au-depreciation-schedule`](../.claude/skills/au-depreciation-schedule/SKILL.md) | [12](../.claude/skills/au-depreciation-schedule/sources.json) | 2026-11-02 (11 of 12) | 0 | 0 | 2 | 1 | 0 | 0 |
| [`au-director-penalty-review`](../.claude/skills/au-director-penalty-review/SKILL.md) | [5](../.claude/skills/au-director-penalty-review/sources.json) | 2026-11-02 (3 of 5) | 0 | 0 | 2 | 2 | 0 | 0 |
| [`au-division-293`](../.claude/skills/au-division-293/SKILL.md) | [2](../.claude/skills/au-division-293/sources.json) | 2026-10-14 (2 of 2) | 0 | 0 | 1 | 1 | 0 | 0 |
| [`au-division-296`](../.claude/skills/au-division-296/SKILL.md) | [4](../.claude/skills/au-division-296/sources.json) | 2026-09-30 (3 of 4) | 0 | 1 | 1 | 1 | 0 | 0 |
| [`au-dssp`](../.claude/skills/au-dssp/SKILL.md) | [2](../.claude/skills/au-dssp/sources.json) | 2026-11-02 (2 of 2) | 0 | 0 | 2 | 0 | 0 | 0 |
| [`au-employee-share-schemes`](../.claude/skills/au-employee-share-schemes/SKILL.md) | [1](../.claude/skills/au-employee-share-schemes/sources.json) | 2026-11-02 (1 of 1) | 0 | 0 | 1 | 0 | 0 | 0 |
| [`au-etp-redundancy`](../.claude/skills/au-etp-redundancy/SKILL.md) | [3](../.claude/skills/au-etp-redundancy/sources.json) | 2026-10-14 (3 of 3) | 0 | 0 | 1 | 1 | 0 | 0 |
| [`au-family-trust-election`](../.claude/skills/au-family-trust-election/SKILL.md) | [5](../.claude/skills/au-family-trust-election/sources.json) | none (0 of 5) | 0 | 0 | 1 | 0 | 0 | 0 |
| [`au-financial-statements`](../.claude/skills/au-financial-statements/SKILL.md) | [7](../.claude/skills/au-financial-statements/sources.json) | 2026-10-29 (1 of 7) | 0 | 0 | 3 | 1 | 0 | 1 |
| [`au-foreign-income`](../.claude/skills/au-foreign-income/SKILL.md) | [1](../.claude/skills/au-foreign-income/sources.json) | 2026-10-14 (1 of 1) | 0 | 0 | 1 | 1 | 0 | 0 |
| [`au-foreign-pensions`](../.claude/skills/au-foreign-pensions/SKILL.md) | [1](../.claude/skills/au-foreign-pensions/sources.json) | 2026-11-02 (1 of 1) | 0 | 0 | 1 | 0 | 0 | 0 |
| [`au-forex-review`](../.claude/skills/au-forex-review/SKILL.md) | [1](../.claude/skills/au-forex-review/sources.json) | 2026-10-14 (1 of 1) | 0 | 0 | 1 | 1 | 0 | 0 |
| [`au-franking-account`](../.claude/skills/au-franking-account/SKILL.md) | [18](../.claude/skills/au-franking-account/sources.json) | 2026-11-02 (15 of 18) | 0 | 0 | 2 | 1 | 0 | 0 |
| [`au-gst-property`](../.claude/skills/au-gst-property/SKILL.md) | [22](../.claude/skills/au-gst-property/sources.json) | 2026-09-30 (2 of 22) | 0 | 0 | 2 | 1 | 0 | 0 |
| [`au-gst-registration-review`](../.claude/skills/au-gst-registration-review/SKILL.md) | [2](../.claude/skills/au-gst-registration-review/sources.json) | 2026-10-14 (1 of 2) | 0 | 1 | 2 | 1 | 0 | 0 |
| [`au-individual-return`](../.claude/skills/au-individual-return/SKILL.md) | [7](../.claude/skills/au-individual-return/sources.json) | 2026-10-14 (2 of 7) | 2 | 0 | 6 | 3 | 0 | 0 |
| [`au-land-tax`](../.claude/skills/au-land-tax/SKILL.md) | [12](../.claude/skills/au-land-tax/sources.json) | 2026-09-30 (3 of 12) | 0 | 0 | 9 | 2 | 0 | 0 |
| [`au-lump-sum-arrears`](../.claude/skills/au-lump-sum-arrears/SKILL.md) | [1](../.claude/skills/au-lump-sum-arrears/sources.json) | 2026-11-02 (1 of 1) | 0 | 0 | 1 | 0 | 0 | 0 |
| [`au-main-residence`](../.claude/skills/au-main-residence/SKILL.md) | [15](../.claude/skills/au-main-residence/sources.json) | none (0 of 15) | 0 | 0 | 2 | 0 | 0 | 0 |
| [`au-managed-fund-amit`](../.claude/skills/au-managed-fund-amit/SKILL.md) | [1](../.claude/skills/au-managed-fund-amit/sources.json) | 2026-11-02 (1 of 1) | 0 | 0 | 2 | 0 | 0 | 0 |
| [`au-medicare-review`](../.claude/skills/au-medicare-review/SKILL.md) | [1](../.claude/skills/au-medicare-review/sources.json) | 2026-10-14 (1 of 1) | 0 | 0 | 1 | 1 | 0 | 0 |
| [`au-non-commercial-losses`](../.claude/skills/au-non-commercial-losses/SKILL.md) | [1](../.claude/skills/au-non-commercial-losses/sources.json) | 2026-11-02 (1 of 1) | 0 | 0 | 1 | 0 | 0 | 0 |
| [`au-nonresident-cgt`](../.claude/skills/au-nonresident-cgt/SKILL.md) | [3](../.claude/skills/au-nonresident-cgt/sources.json) | 2026-10-14 (1 of 3) | 0 | 0 | 1 | 1 | 0 | 0 |
| [`au-not-for-profit`](../.claude/skills/au-not-for-profit/SKILL.md) | [1](../.claude/skills/au-not-for-profit/sources.json) | 2026-10-14 (1 of 1) | 0 | 0 | 1 | 1 | 0 | 0 |
| [`au-partnership-tax`](../.claude/skills/au-partnership-tax/SKILL.md) | [3](../.claude/skills/au-partnership-tax/sources.json) | 2026-10-14 (1 of 3) | 1 | 0 | 2 | 1 | 0 | 0 |
| [`au-payg-instalment-variation`](../.claude/skills/au-payg-instalment-variation/SKILL.md) | [3](../.claude/skills/au-payg-instalment-variation/sources.json) | 2026-10-14 (1 of 3) | 0 | 0 | 1 | 1 | 0 | 0 |
| [`au-payroll-review`](../.claude/skills/au-payroll-review/SKILL.md) | [5](../.claude/skills/au-payroll-review/sources.json) | 2026-10-14 (2 of 5) | 0 | 0 | 5 | 3 | 0 | 0 |
| [`au-payroll-tax-states`](../.claude/skills/au-payroll-tax-states/SKILL.md) | [18](../.claude/skills/au-payroll-tax-states/sources.json) | 2026-09-30 (9 of 18) | 1 | 0 | 10 | 1 | 0 | 0 |
| [`au-pre-lodgement-review`](../.claude/skills/au-pre-lodgement-review/SKILL.md) | [12](../.claude/skills/au-pre-lodgement-review/sources.json) | 2026-10-15 (6 of 12) | 0 | 0 | 3 | 0 | 0 | 0 |
| [`au-primary-production`](../.claude/skills/au-primary-production/SKILL.md) | [29](../.claude/skills/au-primary-production/sources.json) | 2026-11-02 (13 of 29) | 0 | 0 | 2 | 1 | 0 | 0 |
| [`au-private-ruling-application`](../.claude/skills/au-private-ruling-application/SKILL.md) | [6](../.claude/skills/au-private-ruling-application/sources.json) | 2026-11-02 (6 of 6) | 0 | 0 | 1 | 1 | 0 | 0 |
| [`au-professional-firm-profits`](../.claude/skills/au-professional-firm-profits/SKILL.md) | [2](../.claude/skills/au-professional-firm-profits/sources.json) | 2026-11-02 (2 of 2) | 0 | 0 | 1 | 1 | 0 | 0 |
| [`au-property-development-income`](../.claude/skills/au-property-development-income/SKILL.md) | [7](../.claude/skills/au-property-development-income/sources.json) | 2026-11-02 (6 of 7) | 0 | 0 | 1 | 1 | 0 | 0 |
| [`au-psi-review`](../.claude/skills/au-psi-review/SKILL.md) | [4](../.claude/skills/au-psi-review/sources.json) | 2026-10-14 (2 of 4) | 0 | 0 | 2 | 1 | 0 | 0 |
| [`au-rd-incentive`](../.claude/skills/au-rd-incentive/SKILL.md) | [2](../.claude/skills/au-rd-incentive/sources.json) | 2026-10-14 (2 of 2) | 0 | 0 | 1 | 1 | 0 | 0 |
| [`au-rental-property`](../.claude/skills/au-rental-property/SKILL.md) | [7](../.claude/skills/au-rental-property/sources.json) | 2026-09-30 (3 of 7) | 1 | 0 | 3 | 1 | 0 | 0 |
| [`au-restructure-rollovers`](../.claude/skills/au-restructure-rollovers/SKILL.md) | [13](../.claude/skills/au-restructure-rollovers/sources.json) | 2026-11-02 (12 of 13) | 0 | 1 | 1 | 1 | 0 | 0 |
| [`au-return-amendment`](../.claude/skills/au-return-amendment/SKILL.md) | [2](../.claude/skills/au-return-amendment/sources.json) | 2026-10-14 (1 of 2) | 0 | 2 | 1 | 1 | 0 | 0 |
| [`au-sapto`](../.claude/skills/au-sapto/SKILL.md) | [3](../.claude/skills/au-sapto/sources.json) | 2026-11-02 (2 of 3) | 0 | 0 | 2 | 0 | 0 | 0 |
| [`au-share-buy-back`](../.claude/skills/au-share-buy-back/SKILL.md) | [10](../.claude/skills/au-share-buy-back/sources.json) | none (0 of 10) | 0 | 0 | 3 | 0 | 0 | 0 |
| [`au-short-stay-accommodation`](../.claude/skills/au-short-stay-accommodation/SKILL.md) | [15](../.claude/skills/au-short-stay-accommodation/sources.json) | 2026-10-15 (15 of 15) | 0 | 0 | 2 | 0 | 0 | 0 |
| [`au-small-business-cgt`](../.claude/skills/au-small-business-cgt/SKILL.md) | [13](../.claude/skills/au-small-business-cgt/sources.json) | 2026-09-30 (3 of 13) | 0 | 0 | 1 | 1 | 0 | 0 |
| [`au-small-business-income-offset`](../.claude/skills/au-small-business-income-offset/SKILL.md) | [1](../.claude/skills/au-small-business-income-offset/sources.json) | 2026-11-02 (1 of 1) | 0 | 0 | 1 | 0 | 0 | 0 |
| [`au-smsf-death-benefits`](../.claude/skills/au-smsf-death-benefits/SKILL.md) | [11](../.claude/skills/au-smsf-death-benefits/sources.json) | none (0 of 11) | 0 | 0 | 1 | 0 | 0 | 0 |
| [`au-smsf-year-end`](../.claude/skills/au-smsf-year-end/SKILL.md) | [10](../.claude/skills/au-smsf-year-end/sources.json) | 2026-09-30 (6 of 10) | 0 | 0 | 1 | 1 | 0 | 0 |
| [`au-sole-trader`](../.claude/skills/au-sole-trader/SKILL.md) | [4](../.claude/skills/au-sole-trader/sources.json) | 2026-10-14 (1 of 4) | 0 | 0 | 2 | 1 | 0 | 0 |
| [`au-super-contribution-caps`](../.claude/skills/au-super-contribution-caps/SKILL.md) | [7](../.claude/skills/au-super-contribution-caps/sources.json) | 2026-10-14 (4 of 7) | 1 | 1 | 2 | 2 | 0 | 0 |
| [`au-super-guarantee-charge`](../.claude/skills/au-super-guarantee-charge/SKILL.md) | [12](../.claude/skills/au-super-guarantee-charge/sources.json) | 2026-11-02 (8 of 12) | 0 | 0 | 2 | 2 | 0 | 0 |
| [`au-tax-agent-obligations`](../.claude/skills/au-tax-agent-obligations/SKILL.md) | [24](../.claude/skills/au-tax-agent-obligations/sources.json) | 2026-11-02 (2 of 24) | 10 | 0 | 4 | 1 | 0 | 0 |
| [`au-tax-planning-review`](../.claude/skills/au-tax-planning-review/SKILL.md) | [1](../.claude/skills/au-tax-planning-review/sources.json) | 2026-10-14 (1 of 1) | 0 | 0 | 1 | 1 | 0 | 0 |
| [`au-tax-rates-verification`](../.claude/skills/au-tax-rates-verification/SKILL.md) | [1](../.claude/skills/au-tax-rates-verification/sources.json) | 2026-10-14 (1 of 1) | 0 | 0 | 2 | 1 | 0 | 0 |
| [`au-tax-research`](../.claude/skills/au-tax-research/SKILL.md) | [12](../.claude/skills/au-tax-research/sources.json) | 2026-09-30 (9 of 12) | 7 | 0 | 4 | 2 | 0 | 0 |
| [`au-tax-residency`](../.claude/skills/au-tax-residency/SKILL.md) | [1](../.claude/skills/au-tax-residency/sources.json) | 2026-10-14 (1 of 1) | 0 | 0 | 1 | 1 | 0 | 0 |
| [`au-transfer-duty`](../.claude/skills/au-transfer-duty/SKILL.md) | [16](../.claude/skills/au-transfer-duty/sources.json) | 2026-09-30 (1 of 16) | 0 | 0 | 9 | 1 | 0 | 0 |
| [`au-transfer-pricing`](../.claude/skills/au-transfer-pricing/SKILL.md) | [1](../.claude/skills/au-transfer-pricing/sources.json) | 2026-10-14 (1 of 1) | 0 | 0 | 1 | 1 | 0 | 0 |
| [`au-travel-expenses`](../.claude/skills/au-travel-expenses/SKILL.md) | [12](../.claude/skills/au-travel-expenses/sources.json) | 2026-11-02 (9 of 12) | 0 | 1 | 1 | 1 | 0 | 0 |
| [`au-trust-deed-review`](../.claude/skills/au-trust-deed-review/SKILL.md) | [11](../.claude/skills/au-trust-deed-review/sources.json) | 2026-11-02 (8 of 11) | 0 | 1 | 1 | 1 | 0 | 0 |
| [`au-trust-distributions`](../.claude/skills/au-trust-distributions/SKILL.md) | [15](../.claude/skills/au-trust-distributions/sources.json) | 2026-09-30 (9 of 15) | 2 | 2 | 3 | 1 | 0 | 0 |
| [`au-trust-losses`](../.claude/skills/au-trust-losses/SKILL.md) | [5](../.claude/skills/au-trust-losses/sources.json) | none (0 of 5) | 0 | 0 | 1 | 0 | 0 | 0 |
| [`au-wfh-deductions`](../.claude/skills/au-wfh-deductions/SKILL.md) | [5](../.claude/skills/au-wfh-deductions/sources.json) | 2026-10-14 (3 of 5) | 0 | 1 | 1 | 1 | 0 | 0 |
| [`au-working-holiday-makers`](../.claude/skills/au-working-holiday-makers/SKILL.md) | [12](../.claude/skills/au-working-holiday-makers/sources.json) | 2026-09-29 (12 of 12) | 0 | 1 | 1 | 1 | 0 | 0 |
| [`bas-preparation`](../.claude/skills/bas-preparation/SKILL.md) | [19](../.claude/skills/bas-preparation/sources.json) | 2026-10-14 (5 of 19) | 0 | 0 | 16 | 3 | 0 | 0 |
| [`cashflow-forecast-13week`](../.claude/skills/cashflow-forecast-13week/SKILL.md) | [6](../.claude/skills/cashflow-forecast-13week/sources.json) | 2026-09-30 (5 of 6) | 0 | 0 | 2 | 2 | 0 | 0 |
| [`coal-lsl-levy`](../.claude/skills/coal-lsl-levy/SKILL.md) | [7](../.claude/skills/coal-lsl-levy/sources.json) | 2026-09-30 (5 of 7) | 0 | 0 | 2 | 2 | 0 | 0 |
| [`contract-cost-tracking`](../.claude/skills/contract-cost-tracking/SKILL.md) | [4](../.claude/skills/contract-cost-tracking/sources.json) | 2026-10-29 (2 of 4) | 0 | 0 | 2 | 2 | 0 | 0 |
| [`contracting-exports`](../.claude/skills/contracting-exports/SKILL.md) | exempt | none | 0 | 0 | 2 | 2 | 0 | 0 |
| [`contractor-super-tpar`](../.claude/skills/contractor-super-tpar/SKILL.md) | [14](../.claude/skills/contractor-super-tpar/sources.json) | 2026-09-30 (3 of 14) | 0 | 0 | 2 | 2 | 0 | 0 |
| [`div7a-compliance`](../.claude/skills/div7a-compliance/SKILL.md) | [4](../.claude/skills/div7a-compliance/sources.json) | none (0 of 4) | 0 | 0 | 1 | 1 | 0 | 0 |
| [`fbt-annual-workflow`](../.claude/skills/fbt-annual-workflow/SKILL.md) | [7](../.claude/skills/fbt-annual-workflow/sources.json) | none (0 of 7) | 0 | 0 | 3 | 1 | 0 | 0 |
| [`financial-modelling`](../.claude/skills/financial-modelling/SKILL.md) | exempt | none | 0 | 0 | 3 | 1 | 0 | 0 |
| [`fuel-tax-credits`](../.claude/skills/fuel-tax-credits/SKILL.md) | [12](../.claude/skills/fuel-tax-credits/sources.json) | 2026-09-30 (2 of 12) | 0 | 0 | 2 | 2 | 0 | 0 |
| [`marketplace-settlements`](../.claude/skills/marketplace-settlements/SKILL.md) | [3](../.claude/skills/marketplace-settlements/sources.json) | none (0 of 3) | 1 | 0 | 3 | 0 | 0 | 0 |
| [`month-end-close`](../.claude/skills/month-end-close/SKILL.md) | [6](../.claude/skills/month-end-close/sources.json) | 2026-09-30 (5 of 6) | 1 | 0 | 11 | 4 | 0 | 0 |
| [`myob-exports`](../.claude/skills/myob-exports/SKILL.md) | [13](../.claude/skills/myob-exports/sources.json) | none (0 of 13) | 0 | 0 | 2 | 0 | 0 | 0 |
| [`payroll-tax-contractors`](../.claude/skills/payroll-tax-contractors/SKILL.md) | [19](../.claude/skills/payroll-tax-contractors/sources.json) | 2026-09-30 (4 of 19) | 1 | 0 | 6 | 2 | 0 | 0 |
| [`plant-and-equipment-costing`](../.claude/skills/plant-and-equipment-costing/SKILL.md) | [6](../.claude/skills/plant-and-equipment-costing/sources.json) | 2026-10-29 (2 of 6) | 0 | 0 | 2 | 2 | 0 | 0 |
| [`progress-claim-preparation`](../.claude/skills/progress-claim-preparation/SKILL.md) | [5](../.claude/skills/progress-claim-preparation/sources.json) | 2026-09-30 (4 of 5) | 0 | 0 | 2 | 2 | 0 | 0 |
| [`reconciliation-break-trace`](../.claude/skills/reconciliation-break-trace/SKILL.md) | exempt | none | 0 | 0 | 4 | 0 | 0 | 0 |
| [`retention-schedule`](../.claude/skills/retention-schedule/SKILL.md) | [7](../.claude/skills/retention-schedule/sources.json) | 2026-09-30 (4 of 7) | 0 | 0 | 2 | 2 | 0 | 0 |
| [`statement-to-csv`](../.claude/skills/statement-to-csv/SKILL.md) | [4](../.claude/skills/statement-to-csv/sources.json) | 2026-11-02 (2 of 4) | 0 | 1 | 3 | 1 | 0 | 0 |
| [`stp-finalisation`](../.claude/skills/stp-finalisation/SKILL.md) | [8](../.claude/skills/stp-finalisation/sources.json) | 2026-09-30 (5 of 8) | 0 | 1 | 4 | 3 | 0 | 0 |
| [`tax-invoice-review`](../.claude/skills/tax-invoice-review/SKILL.md) | [10](../.claude/skills/tax-invoice-review/sources.json) | 2026-10-14 (3 of 10) | 1 | 0 | 7 | 2 | 0 | 0 |
| [`wip-over-under-billing`](../.claude/skills/wip-over-under-billing/SKILL.md) | [12](../.claude/skills/wip-over-under-billing/sources.json) | 2026-09-30 (12 of 12) | 0 | 0 | 2 | 1 | 0 | 1 |
| [`workpaper-tie-out`](../.claude/skills/workpaper-tie-out/SKILL.md) | exempt | none | 0 | 0 | 9 | 3 | 0 | 0 |
| [`xero-exports`](../.claude/skills/xero-exports/SKILL.md) | [6](../.claude/skills/xero-exports/sources.json) | none (0 of 6) | 0 | 0 | 9 | 2 | 0 | 0 |
| [`year-end-workpapers`](../.claude/skills/year-end-workpapers/SKILL.md) | exempt | none | 0 | 0 | 5 | 1 | 0 | 0 |
