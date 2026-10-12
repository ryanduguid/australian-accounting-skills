The Atheris target feeds fabricated bytes to the validation card parser and the
sensitive-content scan in `scripts/validate_validation.py`. It checks that the
parser returns the exact card fields or refuses with `ValidationError`, that an
accepted card's `id` matches its file name, and that every safety pattern
finishes on arbitrary input. Unexpected exceptions and failed invariants fail
the run. The seed corpus holds five validation cards, renamed to `fuzz-card`,
and a few malformed cards.

On Linux with Python 3.14, run:

```sh
python -m pip install --require-hashes --only-binary :all: -r requirements-fuzz.txt
python -m fuzz.validation_cards fuzz/corpus -max_total_time=60 -max_len=4096 -timeout=2 -rss_limit_mb=1024
```

CI runs the target after main pushes, weekly and on demand, with read-only
repository access and a five-minute timeout. The unittest suite replays the
checked-in corpus on every supported platform. Atheris does not support
Windows, so coverage-guided fuzzing runs on Linux. A successful run is bounded
evidence, not proof that every input is handled.

After changing a pinned version, regenerate the hashes with:

```sh
uv pip compile requirements-fuzz.in --python-version 3.14 --python-platform x86_64-unknown-linux-gnu --generate-hashes --output-file requirements-fuzz.txt
```
