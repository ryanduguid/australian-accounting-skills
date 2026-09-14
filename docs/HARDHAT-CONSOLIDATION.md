# Hardhat Ledger consolidation

This pack became the owner of the ten contracting skills transferred from
`ryanduguid/hardhat-ledger`. The integration source is immutable commit
`eb3b8a6ba47dfcdc05cea434f2f6a7dba82f96ef`. At transfer, every `SKILL.md`
matched that commit after canonical LF normalisation. The table preserves
that original inventory. Later destination-owned amendments are recorded
separately below; the other definitions still match their transferred bytes.

The `v0.2.0` destination release was published and verified on 2 September
2026, and `ryanduguid/hardhat-ledger` was archived on 3 September 2026. That
archive stays readable, so its last compatible release, tags and rollback link
remain available; no forwarding implementation was layered on it.

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

## Destination-owned amendments

On 9 September 2026, `contracting-exports` gained explicit manifest timestamp,
filter, total and rounding-bridge requirements, including re-export after a
filter change and pending authorised review. This responds to the recorded
`export-manifest-rounding` failure; fresh model verification is pending.
Its canonical SHA-256 after that amendment was
`07caf7a2e2aacc371ec6693e56fbd3e3b7679381b72abeb4a6de5f4e671adf6f`.

Later on 9 September 2026, its client-data boundary stopped accepting ignore
coverage as the safeguard for where exports and generated output may be
written, and now requires a location outside every version-control checkout.
The skill already forbade a repository fallback in its portable safety
boundary, so the earlier wording contradicted the same file 2 sections
above it. Its amended canonical SHA-256 is
`d39b1a6479b6f73d373b51841555e8ef276135b9879594a2064c0a69cdbec3f4`.
The transfer hash above remains the historical source record.

Later still on 9 September 2026, the same client-data boundary was carried
across the other 9 transferred skills, which had kept the earlier wording.
Monthly Close Controls is gaining a guard that refuses any output path beneath
a checkout marker outright, so a skill that asked only for output kept out of
version control could send an agent to a path the command then rejects. That
behaviour is proposed in
[accounting-review-pipeline PR 134](https://github.com/ryanduguid/accounting-review-pipeline/pull/134),
read on 9 September 2026, and is in no released version of `close-control` yet.
Re-check the release actually installed before relying on it. The table records
their amended canonical SHA-256 values.

| Skill | Amended SHA-256 |
| --- | --- |
| `coal-lsl-levy` | `6b49ab510a171517a7385e4bf019fba4e57fcf162ebe4edaaf0da3b261721a12` |
| `contract-cost-tracking` | `b68116aa00a401d8934fe50490ea4361f7e4e176d717e1695e6486873be4493a` |
| `contractor-super-tpar` | `8cc6dfaf4181c6b1be86fc269b39415fb0db58639e12c58d6300fd723a2e1b0c` |
| `fuel-tax-credits` | `ef2641203848f74e4cb882eba811d97cc62255431ff7b059715a2b55f6e5ab3e` |
| `payroll-tax-contractors` | `e3ac75e4813a530aa8e3c89840309f84ca531dbc035e582512bcb6ff3fcd3124` |
| `plant-and-equipment-costing` | `4893bbed2aab75f01a4ffe21491a9b65985b35c335d21bf6069c81fdc7679f78` |
| `progress-claim-preparation` | `e809b5ba58abaea107c38b02ef734524cf95d293b562a6e7125fa033b5d95392` |
| `retention-schedule` | `356d4bf0689d480bd467a87ab7256ac071ca5e1c4f128c79c77757a0d9245c52` |
| `wip-over-under-billing` | `554f05d8c6f8b3d7fb2704e192b04ef5dca9ee7d039d424a4bb56596334355a6` |

Their transfer hashes above remain the historical source record.

## Migration order

Existing Hardhat users must uninstall or disable
`subcontractor-accounting-skills@ryanduguid-contracting` before installing
`australian-accounting-skills@ryanduguid`. The 10 names are stable
compatibility identifiers, so never enable both packs at once.

## Rollback

If destination discovery, validation or behaviour regresses, uninstall the
destination pack and reinstall Hardhat Ledger
[`v0.1.5`](https://github.com/ryanduguid/hardhat-ledger/releases/tag/v0.1.5).
The archived repository is read-only, so that release and its tags stay
available. Do not rename skills, rewrite tags or keep 2 active owners as a
workaround.

## Spelling amendment, 11 September 2026

Original prose now uses Australian English `lodgement`. Official source titles,
original transfer hashes and earlier amendment records remain intact. This changes
spelling only. Source-review dates, refusal rules and human authority stay as recorded.

| Skill | Amended canonical SHA-256 |
|---|---|
| `coal-lsl-levy` | `a189220a63ce47fa6d251f2aba82f4c64ccfedc1cbe6f20687620dc8495d3cec` |
| `contractor-super-tpar` | `0cd72dc506d3b53a335ed27316e81e075ad40e68ea17ee74d712682ab4d1e8e2` |
| `fuel-tax-credits` | `06d08d8b4d980557abc4c4f04321edd52f7c749710d99d0add5488a2b319ecdc` |
| `payroll-tax-contractors` | `f635b19f6a857fc2f72a63866462117245543f75f0ed3cfa615f3cd7d1e1ebf2` |

## Privacy and engine-reference amendments, 12 September 2026

Coal LSL inputs now use firm-held employee references; an authorised person
merges required identifiers inside the approved firm system. WIP guidance and
its source record now pin the same canonical engine commit, including the
approved-installation command. Historical transfer and amendment hashes above
remain unchanged. Fresh model evaluation is pending.

| Skill | Amended canonical SHA-256 |
|---|---|
| `coal-lsl-levy` | `d77c86459d3bff0761b079fcaea84e73673ecea8f027fa5c018fcfe3dca08bc3` |
| `wip-over-under-billing` | `47d284ce45e07a062f2d1f5e4d62c5b7f6351e0281a18790c9022797bde44efa` |

## Style Manual amendment, 13 September 2026

Prose in all 10 transferred skills now follows the Australian Government Style
Manual: numerals for numbers, English wording in place of Latin shortened
forms, italicised Act titles and sentence-case headings. Front matter names,
official source titles, section references, original transfer hashes and the
earlier amendment records are unchanged. This changes presentation only.
Requirements, refusal rules, source-review dates and human authority stay as
recorded.

| Skill | Amended canonical SHA-256 |
|---|---|
| `coal-lsl-levy` | `d9a57dd6ed2217a68a22a6cb15416104e4b46581e15079a573e4d1dc1f9ed101` |
| `contract-cost-tracking` | `7e8ee6f47caa283fa7fa0d282c43b902600fe87f9e6237ad15f2daab348a7957` |
| `contracting-exports` | `a423015904aec0e79846381725a92bd6393121bdbb4e55b4b468854b1d3cd450` |
| `contractor-super-tpar` | `1955efd6c7595606c714123cffd660b1f49dc349a27cf388f214af3c24e712d9` |
| `fuel-tax-credits` | `93b7d67eaa8d4a50fc584754249f39f98c15417ad4c59fb5614b880a0b9e8f26` |
| `payroll-tax-contractors` | `fc03ba9c035c2092770cbaeeb901671e375a2a4696cddba474350dde07e63d75` |
| `plant-and-equipment-costing` | `11ce902d769e0b8be65d81a23dd6fdd7f6ed453070208240bf91a066877676b8` |
| `progress-claim-preparation` | `8a6799ed533f491acc8fc1b16212bf70ec28690bdf9783cb83fd4b4e7bdb6b5c` |
| `retention-schedule` | `4af4c536f331c82e3730aaebcf8f9afe0757cf08ada56c898c0b0c54b2a7d891` |
| `wip-over-under-billing` | `ce6d130bb924904edd617e06371d15b07104672333467cf364953cf01116bbe5` |

## Fuel tax credit attribution amendment, 13 September 2026

Step 10 of `fuel-tax-credits` now states the non-cash attribution rule as the
earlier of the period consideration is provided or an invoice is issued,
subject to holding the tax invoice at lodgement, limits a cash-basis claim to the
part matching the consideration provided, and names the s 65-5(4) to (6)
later-period election as a separate choice. The earlier wording reduced the
rule to the invoice alone. Original transfer hashes and the earlier amendment
records above remain unchanged.

| Skill | Amended canonical SHA-256 |
|---|---|
| `fuel-tax-credits` | `d40287358d80f67ec75d6effebcccfaa1f99643e0ce2d92916356d0827e22916` |

## Fabricated exercise amendment, 13 September 2026

Contracting export intake now uses operator roles and supplied pseudonyms in
fabricated exercises, with an in-chat manifest when no file is requested. Real
client storage requirements remain in force. The original transfer and earlier
amendment records above are preserved. Fresh responses require human assessment.

The amended canonical SHA-256 for `contracting-exports` is `ad35a00cd2f093463f09eab096d032ed0de1e0a863686e170426d59ef0d2d7ef`.
