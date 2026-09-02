# Hardhat Ledger consolidation

This pack is the planned replacement owner for the ten contracting skills from
`ryanduguid/hardhat-ledger`. The integration source is immutable commit
`eb3b8a6ba47dfcdc05cea434f2f6a7dba82f96ef`. Every transferred `SKILL.md`
matches that commit after canonical LF normalisation. Destination-owned source
indexes, discovery metadata and validation cards sit beside those unchanged
definitions.

This document records local preparation for a proposed `v0.2.0` release, not an
available replacement release. The proposal is neither published nor publicly
verified. Hardhat Ledger remains the compatible install route until a reviewed
release of this repository contains the inventory below and passes all three
discovery paths.

## Exact transferred inventory

| Skill | Source Git blob | Canonical SHA-256 |
|---|---|---|
| `coal-lsl-levy` | `2ad5d31656301cf18a4dafc863066c259cef00b1` | `c0330c9ec817435c731872452e5984040c89b16a5ad432193b0135ba1a322c23` |
| `contract-cost-tracking` | `cc8b1d2c98224c66eba6a5a8b7fd071f6165fdf9` | `c385d832d1bfc00bd4e4eed12c2b86740047049f50cfcf11325a5adbdc0e1690` |
| `contracting-exports` | `6ef0ebdeadb046710accd8c3956c7cfe60704230` | `bcfec0dd235e2940eb2f0a5c447f097bc2257d85cc723c1151b4c1885aef929e` |
| `contractor-super-tpar` | `1f2be7647fa2f4f37920c869d87e10761c2d8377` | `47ba8863485798b80cc25d1fe7485c58918b853032bc81e1f4128cce39e1eece` |
| `fuel-tax-credits` | `ef5b3121ca1cbbbc68ee300280e4a032c23b481c` | `a2721d3afc420b17a4a13503b046870564f1f8e6bc0700ed144376ace2ae99be` |
| `payroll-tax-contractors` | `408ab33363c73aa81720990307fd53c0174caacd` | `1e6e58397fb139c4c3d7320f3c3cf38e86f632517921e1942447a70189bc9108` |
| `plant-and-equipment-costing` | `4f796dcdd8fe3ea0cf128aea88c1968fd0a622d6` | `7718b8226306e3ec6c546758a2839ee04c6ea964e550fdf83586e4081cac80af` |
| `progress-claim-preparation` | `cf475ace966fb28416dde1608462ebd0f589ef5b` | `9d4b7bbf3789cab8c4e3e3686b7194eb6a7ec9f7604191151c4d5593917233e4` |
| `retention-schedule` | `063fe6910f4ed4165730658df6c5991a4061588c` | `84e23a7a268391cb352c3d1f36d7bb5628690b6aa390a0492cfc81106832373c` |
| `wip-over-under-billing` | `41ac43dca0b7489b42647d2203654822a191606a` | `c1aa5c432c41a5ac79ab384ce5ab7e472a555b6825faa01536e6e01aae8270b1` |

The reviewed legal and tax source record is retained in
[`source-review-2026-08-15.md`](source-review-2026-08-15.md). Its conclusions
remain bounded by the copied skills' use-time source checks and human-review
gates.

## Replacement gates

A destination release is eligible only after all of the following pass at its
exact release commit:

1. the Claude plugin marketplace and plugin manifests expose exactly 19 skills;
2. the Codex plugin resolves the same `.claude/skills/` owner;
3. `skills@1.5.22 add . --list` discovers the same 19 names;
4. all 17 fabricated validation cards, including the standalone-safety card,
   pass the fixed-inventory validator;
5. the complete unit suite, source gates and exact transfer hashes pass; and
6. an independent review confirms the client-data, consequential-action and
   professional-judgement boundaries are not weaker than Hardhat Ledger.

## Migration order

After the proposed `v0.2.0` destination release is published, publicly
verified and passes those gates, existing Hardhat users must uninstall or disable
`subcontractor-accounting-skills@ryanduguid-contracting` before installing
`australian-accounting-skills@ryanduguid`. The ten names are stable
compatibility identifiers, so never enable both packs at once.

Only after that replacement is available and verified may Hardhat Ledger take a
separate deprecation change. That follow-up updates its install guidance, keeps
the last compatible release and rollback link, and deletes its duplicate
validator and skill payload rather than layering a forwarding implementation.
Publishing that release or archiving the repository requires separate owner
approval.

## Rollback

If destination discovery, validation or behaviour regresses, uninstall the
destination pack and reinstall Hardhat Ledger
[`v0.1.5`](https://github.com/ryanduguid/hardhat-ledger/releases/tag/v0.1.5).
Keep Hardhat Ledger unarchived and retain its release and tags. Do not rename
skills, rewrite tags or keep two active owners as a workaround.
