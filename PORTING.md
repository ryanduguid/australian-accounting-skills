# Rust port status and cutover holds

Native Rust tooling lives in [tools/accounting-skills/](tools/accounting-skills/README.md). Several Python components have already cut over exclusively to `accounting-skills`, whilst the remaining Python scripts, fuzz target, plugin hook and parity test harnesses stay in place under recorded constraints or open cutover holds.

See [tools/accounting-skills/PORTING.md](tools/accounting-skills/PORTING.md) for the complete per-component matrix and cutover blockers covering:

- [hooks/critical_rules.py](hooks/critical_rules.py) and [hooks/hooks.json](hooks/hooks.json)
- [scripts/validate_validation.py](scripts/validate_validation.py)
- [scripts/source_fetch_policy.py](scripts/source_fetch_policy.py)
- [scripts/source_refresh.py](scripts/source_refresh.py)
- [scripts/source_passages.py](scripts/source_passages.py)
- [scripts/strict_yaml.py](scripts/strict_yaml.py)
- [fuzz/validation_cards.py](fuzz/validation_cards.py)
- the differential harnesses in [tools/accounting-skills/tests/](tools/accounting-skills/tests/validation_parity.py)
