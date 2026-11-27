# Rust port status and cutover holds

This ledger records which repository commands run exclusively from `tools/accounting-skills`, which candidate ports exist alongside Python implementations, and why the remaining Python files stay active. See the root overview in [PORTING.md](../../PORTING.md) and command details in [README.md](README.md).

## Exclusively Rust

These commands are the only implementations; their Python predecessors are retired or lived outside this repository:

- `build-coverage`
- `sweep-outcome`
- `prepare-trial`
- `build-plugin-evals`
- `build-plugin-dist`
- `build-skill-zips`
- `last-changed`
- `check-citations`
- `statement-check`
- `review-state`
- `serve-mcp`
- `audit-grader-reads`
- `workpaper-renderer` (binary)

## Ported with cutover held

| Python component | Rust counterpart | Hold reason and constraint |
| --- | --- | --- |
| [hooks/critical_rules.py](../../hooks/critical_rules.py) and [hooks/hooks.json](../../hooks/hooks.json) | `accounting-skills critical-rules-hook` | **Held, no build step:** Claude Code runs plugin hooks on the user's machine straight from the plugin checkout, where no Rust build step runs. Both `hooks/critical_rules.py` and `hooks/hooks.json` stay intact until prebuilt binaries ship through signed releases. |
| [scripts/source_refresh.py](../../scripts/source_refresh.py) | `accounting-skills source-refresh` | **Cutover held (transport and charsets):** live qualification on 28 October 2026 could not reach `www.sro.tas.gov.au` because the host offers CBC-only TLS 1.2 whilst `ureq`/`rustls` disables CBC cipher suites; `EUC-KR`, `ISO-2022` variants and `UTF-7` also remain unqualified body and header charsets. `.github/workflows/source-sweep.yml` keeps `scripts/source_refresh.py` active until the TLS and charset decisions land. |
| [scripts/source_fetch_policy.py](../../scripts/source_fetch_policy.py) | `accounting_skills::source_fetch_policy` | **Cutover held:** library policy rules are ported and parity-tested (`tests/fetch_policy_parity.py`), whilst Python `scripts/source_refresh.py` and `scripts/source_passages.py` remain active callers until transport cutover clears. |
| [scripts/source_passages.py](../../scripts/source_passages.py) | `accounting-skills source-passages` | **Cutover held:** snapshot capture and diff logic are ported, whilst live transport remains held behind `source-refresh` TLS compatibility and charset coverage. |
| [scripts/validate_validation.py](../../scripts/validate_validation.py) | `accounting-skills validate-validation` | **Cut over; retirement held:** the `native` CI job (Linux and Windows) and the `validation-pack` pre-commit hook run `validate-validation`, the only validation-pack gate. The Python script stays as the oracle that `tests/validation_parity.py` replays `tests/test_validation_pack.py` against, and as the `fuzz/validation_cards.py` target, until those 74 tests are Rust tests and a native fuzz target exists. Where the 2 differ the Rust check is the stricter: it caps YAML nesting at 128 levels and compares JSON `const` numbers by representation (`2.0` is not `2`). Its privacy scan follows Python 3.15's Unicode 17.0, which the removed CI step also ran: NFKC from unicode-normalization 0.1.25 and the Unicode 17.0 digits added to `\d`. The regex crate's word class is still Unicode 16.0, so a Unicode 17.0 letter can only add word boundaries, which adds refusals and removes none. |
| [scripts/strict_yaml.py](../../scripts/strict_yaml.py) | `accounting_skills::strict_yaml` | **Kept for the Python test suite:** the Rust module enforces the strict validation-card YAML subset (also refusing aliases, anchors and tags), whereas `scripts/strict_yaml.py` supplies the generic `UniqueKeySafeLoader` factory required by the Python suite (`tests/test_skill_metadata.py`, `tests/test_script_entry_points.py` and `tests/test_validation_pack.py`). |
| [fuzz/validation_cards.py](../../fuzz/validation_cards.py) | None | **Held behind the validator retirement:** runs `atheris` (Python libFuzzer) directly against `scripts/validate_validation.py` in the scheduled `fuzzing` CI job and `tests/test_fuzz_harness.py`. A dedicated `cargo-fuzz` target replaces it before the Python script goes. |
| [tests/validation_parity.py](tests/validation_parity.py), [tests/source_refresh_parity.py](tests/source_refresh_parity.py), [tests/source_passages_parity.py](tests/source_passages_parity.py), [tests/fetch_policy_parity.py](tests/fetch_policy_parity.py), [tests/source_codecs_parity.py](tests/source_codecs_parity.py), [tests/multibyte_parity.py](tests/multibyte_parity.py), [tests/gb18030_parity.py](tests/gb18030_parity.py) | None | **Kept as differential test oracles:** Python by design because they invoke installed CPython 3.14.8 standard-library modules (`html.parser`, `difflib`, `email`, `codecs`, `unicodedata`) and Python `unittest` suites as independent oracles against `accounting-skills` and its debug probes. |

## Repository tests

`tests/*.py` (`unittest`, branch coverage on `scripts/` and `tests/verify_skills_cli.py`) remain Python until the remaining `scripts/` cutovers complete and native checks cover the repository gates without a Python test harness.
