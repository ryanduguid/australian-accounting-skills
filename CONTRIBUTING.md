# Contributing

These skills describe how an agent should work through an Australian accounting task. They encode workflow and tie-out discipline, and they stop where professional judgement starts.

## Data boundary

- Keep client data out of the repository. The `.gitignore` blocks `input/`, `output/`, `clients/`, `exports/` and the common export extensions, including `.aba`, `.myox`, `.ofx` and `.qif`.
- Fabricate your examples. An entity name, ABN or balance set lifted from real work is client data however realistic it looks.
- Do not use a redacted or de-identified client export as a fixture. Create every fixture from scratch and run `cargo run --locked --manifest-path tools/accounting-skills/Cargo.toml -- validate-validation` before committing it.

## Writing a skill

Include byte-identical copies of the root `LICENSE` and `NOTICE` in each
skill folder so individual installs carry their terms. Refresh the copies
when editing either root file.

- Send the agent to the primary source for anything that changes: rates, thresholds, benchmark interest, label numbers, lodgement dates. Hardcode a current-year figure and the skill goes wrong next year without saying so.
- Reach every step from the inputs the skill asks for. A step that needs a payroll report, a balance sheet or a payment history the skill never requested is broken rather than thorough.
- Keep the scope fence visible. State what the skill declines to decide, and where a human signs off.
- Keep [DISCLAIMER.md](DISCLAIMER.md) aligned with README and plugin manifests. Discovery copy lives in [docs/DISCOVERY.md](docs/DISCOVERY.md).
- Prefer a tie-out to an assertion. If a step produces a number, say what that number must agree with.
- Put generated client output only in the firm's approved secure location. A skill must ask before using a repo-adjacent path and must not change `.gitignore` or repository configuration without explicit approval.
- Keep consequential actions human-only: agents may prepare and check, but an authorised human decides, communicates, signs, posts, locks, pays, declares and lodges.

## Local verification

Python 3.14 or newer, and Rust 1.99 or newer for the validation-pack, coverage and citation checks. Install
the pinned test dependency, Pyright and Ruff first, and put ShellCheck 0.11.0
and actionlint 1.7.12 on the path:

```bash
python -m pip install --require-hashes --requirement requirements-test.txt --requirement requirements-lint.txt
python -m ruff check .
python -m pyright
shellcheck -x scripts/*.sh
actionlint
python -m unittest discover -s tests -v
python tests/verify_skills_cli.py
cargo run --locked --manifest-path tools/accounting-skills/Cargo.toml -- validate-validation
cargo run --locked --manifest-path tools/accounting-skills/Cargo.toml -- build-coverage --check
cargo run --locked --manifest-path tools/accounting-skills/Cargo.toml -- check-citations
```

Those 9 checks are the gates `.github/workflows/verify.yml` runs in its
`lint`, `verify` and `native` jobs. Ruff, Pyright, ShellCheck and actionlint
run in its `lint` job, then 2 verification checks run on Python 3.14 and 3.15,
and the validation-pack, coverage and citation checks run in its `native` job.
`python tests/verify_skills_cli.py` needs `npx` and compares the
reported skill names from the CLI with the skill directories in the current tree.

`verify-gates`, the one check from that workflow that branch protection requires, also needs these jobs to pass:

- The `native` job builds and tests the Rust tooling in `tools/accounting-skills/`,
  holds its line coverage at the floor of 73% with cargo-llvm-cov 0.9.1, and
  compares it with the scripts it ports. Apart from the coverage and citation
  checks, it runs in CI only, with no pre-commit hook; its README lists the
  local commands. The coverage floor, from `tools/accounting-skills/`:

  ```bash
  cargo llvm-cov --locked --all-targets --fail-under-lines 73
  ```

- The `coverage` job holds the unit tests' branch coverage of `scripts/` at 100%:

  ```bash
  python -m pip install --require-hashes --no-deps --only-binary=coverage,pyyaml --requirement requirements-coverage.txt
  python -m coverage run --branch --source=scripts -m unittest discover -s tests
  python -m coverage report --fail-under=100
  ```

- The `shared-conformance` job runs the shared `verify-skills.yml` workflow
  from `ryanduguid/release-policy`.

Branch protection also requires the `secrets` job of `.github/workflows/secrets.yml`.
It runs the shared secrets scan from `ryanduguid/release-policy`:
betterleaks over the commits a push or pull request adds, and the full
history weekly or when run by hand. It scans a pull request a second time
with the base branch's `.gitleaks.toml`, so add an allowlist entry in its own
pull request, before the change that needs it.

`pip install pre-commit && pre-commit install` runs the 9 checks, the betterleaks hook
and `git diff --cached --check` before the commit lands. `.pre-commit-config.yaml` pins Ruff, Pyright, ShellCheck and actionlint
to the versions CI installs, so a hook that passes locally cannot fail on a
version difference.

The suite checks skill metadata and structure. Add a test when your change introduces a rule a reader could get wrong.

## Pull requests

Cite the provision, ruling or ATO page behind any technical change, and give its date. When you alter a rule, search for every other place that states or polices it. The same rule tends to appear in a checklist, a tie-out and a worked example.

For a potential security vulnerability, follow [SECURITY.md](SECURITY.md) rather than opening an issue.

## Release checks

The release caller names the component checks that must have succeeded for the
exact release commit on `main`. It advances the policy SHA, `required-checks`
and `actions: read` together. Skipped, missing, cancelled or failed checks block
publication, including component tests skipped by a path filter. An aggregate
gates job cannot replace those checks. Before tagging, choose a main-branch
commit with successful component CI; a successful run for an older commit is
not evidence for the release. Tags and publication still require explicit approval.
