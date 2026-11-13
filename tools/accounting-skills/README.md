# Native accounting skill tooling

This crate holds the repository's Rust tooling. It needs no Python runtime and
does not assess whether a source or accounting conclusion is correct.

These commands are the only implementations; the Python scripts they replaced
are retired:

| Command | Retired script |
| --- | --- |
| `build-coverage` | `build_coverage.py` |
| `sweep-outcome` | `sweep_outcome.py` |
| `prepare-trial` | `prepare_trial.py` |
| `build-plugin-evals` | `build_plugin_evals.py` |

`last-changed` is new, with no retired script: it writes `docs/skill-last-changed.md` from git history and refuses a shallow clone.
`check-citations` is also new: it checks that every cited section and ruling
has a record in its skill's `sources.json`, and that a cited section exists
where `section-index/` lists its Act's sections.

`statement-check` is also new: the `statement-to-csv` skill runs it on statement lines transcribed
to JSON. In exact cents it checks each printed running balance, brought-forward and
carried-forward balance and closing balance, extracted gross credits and debits against printed
totals, a sign taken from the running balance, line dates against the period, and continuity
between statements. The period check can flag a line the issuer legitimately placed on the
statement, for example under its own posting cutoff, and never passes a line whose `posted` date
falls outside the period. It prints one `BREAK` line per difference and one `OVERLAP` line per pair of
overlapping periods, ends with a `PASS` line counting what it compared or a `FAIL` line, and exits
0 when everything ties, 2 on any break and 1 on malformed input, including an empty one or a
repeated reference. The input holds figures and line references only, never descriptions.

`build-skill-zips DESTINATION` is also new: it writes one upload ZIP per skill,
`NAME.zip`, into a new folder, from the skills committed at HEAD. Each ZIP's
only root entry is the skill's folder, holding exactly one `SKILL.md` at its
root, the shape Anthropic's article and OpenAI's Skills API guide describe.
Entries are stored uncompressed, in path order, with fixed timestamps, so one
commit always gives the same bytes. It refuses a skill with a second `SKILL.md` and an existing
destination. `docs/installation.md` gives the upload steps.

`audit-grader-reads` replaces `audit_grader_reads.py`, a script kept outside
this repository. It prints the same report on well-formed traces, except that
it also flags a suspect folder that ends a path, as in
`{"path": "/copy/graders"}`, which the script missed. It splits
traces only at newlines, so a raw U+2028 inside a tool input no longer hides
that call, and it fails when it flags a call, finds no trace or cannot read a
line. An integer above the 64-bit range prints as a float. Lines containing
NaN, lone surrogate escapes or invalid UTF-8 are reported as SKIP.
`docs/EVAL.md` describes its use and limits.

The others are candidate ports of scripts that remain the authoritative
commands in `scripts/`:

| Python script | Native command |
| --- | --- |
| `validate_validation.py` | `validate-validation` |
| `source_fetch_policy.py` | library used by `source-refresh` |
| `source_refresh.py` | `source-refresh` |
| `source_passages.py` | `source-passages` |
| `strict_yaml.py` | card YAML within `validate-validation`, `prepare-trial` and `build-plugin-evals` |

`strict_yaml.py` has no other script caller. Its remaining callers are the
Python skill-metadata and entry-point tests, which stay with the Python suite.
The native card reader is stricter than the shared factory: it also refuses
anchors and tags.

Without installing, run a command from the checkout root with
`cargo run --locked --manifest-path tools/accounting-skills/Cargo.toml -- COMMAND ...`.
Each command's default root is the current directory.

## Build and checks

`rust-toolchain.toml` pins the compiler. From this directory:

```sh
cargo fmt --check
cargo clippy --locked --all-targets -- -D warnings
cargo test --locked --all-targets
cargo build --locked --release
cargo install --locked --path .
```

The `native` job in `.github/workflows/verify.yml` runs these checks on Linux
and Windows, checks this tree with `validate-validation`, `build-coverage
--check` and `check-citations`, then runs the comparison harnesses in `tests/*_parity.py` for the
candidate ports. Those replay the original Python tests against the native code
and compare fabricated inputs with the unchanged scripts, with no indexed source
fetched. Run them on Python 3.14, as the job does: under Python 3.15 the
validation and source_refresh harnesses stop at their Unicode 16.0
qualification checks. To run one locally, build the debug examples first:

```sh
cargo build --locked --examples --bins
python -I tests/validation_parity.py --root ../.. --binary target/debug/accounting-skills --probe target/debug/examples/validation_probe --record /tmp/validation.json
```

The job keeps each platform's release binary, this README and the licences as
a 7-day workflow artefact. That artefact is an unsigned test candidate, not a
release: no checksum, attestation or signature covers it, and the repository
release still ships the skills archive only. Binary releases wait for the
shared release workflow described in the release policy.

## Coverage matrix

```sh
cargo build --locked --release
accounting-skills build-coverage --root /path/to/checkout --check
accounting-skills build-coverage --root /path/to/checkout --write
```

The current directory is the default root. A root operand beginning with a dash
needs an explicit path, such as `./--check`. `--write` takes precedence over
`--check`, as in the retired Python command. The command also renders
`docs/skill-verification.md`, a per-skill table from the same matrix, and
`--check` compares both files. Success prints the matrix unless writing, which
prints `wrote coverage.json and docs/skill-verification.md`. A stale check
names each stale file and exits 2. Processing and
argument errors exit 1 with a diagnostic instead of a Python traceback or
argparse usage. Options must be spelt in full: argparse's abbreviations (such
as `--wr`), the `--` terminator and help text are not ported.

`--write` writes a temporary file beside each output and renames it into
place, so a hard link elsewhere keeps its old contents. An output that is a
symlink or not a regular file is refused. The retired Python command wrote
through either link.

The Python builder did not have the `reviewed_count`, `confirmed_pass`,
`confirmed_fail` and `confirmed_noncurrent_digest` fields or their totals; the
note now describes them. `reviewed_count` is how many indexed sources carry a
review date. A confirmed verdict counts as a pass or fail only when the record's
`rubric_sha256` matches the card's current bytes; otherwise the card is listed
under `confirmed_noncurrent_digest`, even if the current card also has a
verdict. The build does not look for the digest in the card's git history,
because the native CI job checks out a single commit, so that list claims only
that the digests differ. Verdicts under different digests are kept apart, so a
pass recorded under another digest and a fail on the current card both stand;
neither digest is taken to identify a particular earlier card.
The build refuses a status other than `prepared`, `observed` or `confirmed`
(an absent status marks a legacy record), a verdict other than `pass` or
`fail`, a confirmed verdict whose `rubric_sha256` is not 64 lower-case hex
digits, one for a card no skill targets, and one card version confirmed both
pass and fail, naming both records, because no rule yet says which verdict
supersedes the other. Legacy records are left out of the counts and named in
the page's legend with any fail they hold.

The schema, field order, note text, source-date distinctions, card deduplication,
quoted test mentions and platform newline conventions preserve the retired
Python builder. Native stdout is always UTF-8. The note names this command; it
named the Python builder until the cutover, so the bytes stayed comparable.
Human review dates are never advanced.

The Python builder could exclude inventory sweeps, test files that name every
skill by construction, from the behavioural evidence. Its list was empty, so
this command counts every quoted mention in `tests/*.py` and writes empty
`inventory` lists. A future inventory sweep needs that exclusion added here,
with a check that the file still names most skills.

The source schema requires date fields to be strings and, when present,
`sources` to be an array. A URL must be a string where the matrix reports it,
in `moved_since_review`. This command refuses malformed types rather than
reproducing Python's conversion of arbitrary values into provenance strings.
Input links are followed, as in the original. Non-Unicode
filenames are refused. Unicode equivalence is sampled, not exhaustive.

## Source sweep outcomes

```sh
accounting-skills sweep-outcome --status 0 --report sweep.md --started 2026-09-20T19:00:05Z
```

This command preserves the report's 7 required counts, duplicate refusal,
minute-level freshness, status agreement and distinction between actionable and
unchecked sources. Counts are ASCII digits read as 64-bit unsigned integers;
a count or actionable total above that range fails. The outcome
and comment go only to stdout. The command never writes to `GITHUB_OUTPUT`.

The source sweep workflow builds this command and gives it the status and
report of `scripts/source_refresh.py --check`. `tests/sweep-report.md.fixture`
is a report that script renders: `tests/test_source_sweep.py` fails when the
renderer's output changes, and `tests/sweep.rs` parses the fixture.

Report paths resolve links and parent components before checking confinement to
the current directory. Missing and escaping paths fail before file reads.
Like the original, this local tool assumes the report and its directories do not
change during resolution and reading; it is not concurrent-mutation isolation.
The native resolver refuses nested link resolution beyond 40 levels. On Windows, directly supplied
`link/../report` paths can be refused where the retired script normalised the parent component
first and read an inside report. These are conservative compatibility limits.
Invalid timestamps, I/O failures and CLI parsing use native diagnostics and exit 1.
Timestamp month, day and clock fields accept ASCII digits without space padding;
The retired script accepted some additional Unicode and space-padded forms. Ordinary producer
and workflow timestamps use the supported ASCII forms.
Status operands fit a signed 64-bit integer. Normal flags and `--name=value` are
supported; argparse's automatic flag abbreviations and help are not ported.
Decimal classification matches Python 3.14's Unicode 16.0 in qualification;
new decimal characters in Python 3.15's Unicode 17.0 may be refused.

## Citations

```sh
accounting-skills check-citations --root /path/to/checkout
```

This read-only command reads every Markdown file in every skill. It finds each
ruling, determination, practice statement, guideline, and TPB or ASIC guidance
number, and each legislative section or regulation. A ruling resolves when a
record's title or address in the skill's `sources.json` names the same
document. A section resolves when a record from a legislation register names
its Act or instrument, which must be named in the section's own sentence:
right after it, right before it, or as the only one the sentence names apart
from an amending Act and one named right after another section. An Act named
on an earlier line or in an earlier sentence never owns a section. Sections of
a professional standard such as APES 110, and cross-references such as
"section 3 below", are not counted.

A resolved section must also exist where `section-index/` in this directory
lists its Act's sections. Each `REGISTER-ID.txt` there holds one Commonwealth
Act's or instrument's section numbers, one per line, after `# key: value`
lines giving its `title`, `register-id`, `compilation`, `compilation-number`,
`in-force-from`, `source`, `retrieved` and `sha256`. A Queensland Act's list,
`qld-act-YYYY-NNN.txt`, has the same lines apart from `compilation` and
`compilation-number`; `in-force-from` names the register's version, and its
sections are those the register's XML of that version holds, leaving out any
marked repealed. The numbers are every
table of contents entry of the compilation's EPUB, fetched from the `source`
request to the Federal Register's API, that starts with a provision number;
after the first schedule heading only hyphenated numbers count, because a
schedule's unhyphenated entries are clauses; a clause cited as a section is
therefore checked against the body section with that number. The SHA-256 is of the EPUB.
Subsection and paragraph suffixes are ignored. `ss 17A-18C` is a range when
both ends are listed and the list holds no hyphenated number; in a list that
does, such as the TAA 1953's with its Schedule 1 sections, a hyphenated number
must itself be listed, so `s 8-1 of the TAA 1953` is absent. `section-index/exceptions.txt`
lists, as `REGISTER-ID SECTION: reason`, a section a skill cites on purpose
although its list lacks it, such as one a Bill proposes or one since repealed.
A section of an Act with no list is counted as not indexed.

After any failures the command prints its summary: each Act or instrument's
resolved sections, most cited first, named with its jurisdiction, then the
totals. `docs/EVAL.md` quotes that summary, and `tests/citations.rs` fails when
the quote and the command's output differ.

A list's header is also the only offline evidence of which instrument a
Federal Register address holds: the identifier is otherwise tied to the
record's title by kind and, for an Act, year. A `sources.json` record whose
register identifier has a list must carry a title matching the list's, and a
record whose title matches a list's must carry its identifier. A record that
fails either owns no citation, and each citation it would have resolved
reports the record, both titles and both identifiers. A record of an
instrument with no list, or from the ATO legal database or a state register
other than a listed Queensland Act's, is not checked this way: a mis-titled one still resolves, and a reviewer must
catch it.

Each failure prints as `file:line: citation: reason`: an unmatched citation, a
section absent from its Act's list, or an exception no cited section needs.
Two total lines follow, the second counting the resolved sections found,
listed as exceptions, absent and in an Act with no list. The exit code is 2 on
any failure. A found section exists in the current compilation; the check does
not show that it applied in the skill's period or says what the skill claims.
No command rebuilds a list: the EPUB is a zip archive, and the crate has no
decompression dependency.

### Rebuilding a section list

Rebuild a list when the register publishes a new compilation of its Act. Until
then a correct citation of a section a later compilation added fails as absent,
and a citation of a section it repealed still passes. To build or rebuild
`section-index/REGISTER-ID.txt`, where `REGISTER-ID` is the Act's series
identifier such as `C2004A05138`:

1. Ask the register API for the current compilation, URL-encoding the filter:
   `https://api.prod.legislation.gov.au/v1/versions?$filter=titleId eq 'REGISTER-ID' and isCurrent eq true&$select=titleId,name,start,compilationNumber,registerId`.
   `registerId` is the compilation's identifier, `compilationNumber` its
   number, `start` its in-force date and `name` the title.
2. Ask for that compilation's EPUB:
   `https://api.prod.legislation.gov.au/v1/documents?$filter=registerId eq 'COMPILATION' and format eq 'Epub' and type eq 'Primary'&$select=titleId,start,retrospectiveStart,rectificationVersionNumber,uniqueTypeNumber,volumeNumber`.
   Where more than one row comes back, take the highest
   `rectificationVersionNumber`. One EPUB (`volumeNumber` 0) holds every
   volume.
3. Download it from
   `https://api.prod.legislation.gov.au/v1/documents(titleId='REGISTER-ID',start=START,retrospectiveStart=RETROSPECTIVE-START,rectificationVersionNumber=N,type='Primary',uniqueTypeNumber=U,volumeNumber=V,format='Epub')`,
   writing the dates as the API returns them (`2026-10-01T00:00:00`, with no
   time zone). This address is the `source` field. On 12 November 2026 the
   EPUB address on www.legislation.gov.au refused clients other than browsers.
4. Unzip the EPUB and read the table of contents, `OEBPS/document.ncx`. Take
   the text of each `navLabel` in document order. A label is a section when
   it starts with a number matching
   `[0-9]+[A-Z]*(-[0-9]+[A-Z]*)?(\.[0-9]+[A-Z]*)?` followed by 2 spaces; the
   number is the entry. Once a label starting with `Schedule` has appeared,
   keep only hyphenated numbers, because a schedule's other entries are
   clauses. Keep the first occurrence of a repeated number: the loader rejects
   repeats, and the Corporations Act's small business guide repeats 11 body
   section numbers.
5. Write the file with LF line endings: the header lines `# title: ` (the
   version's `name`), `# register-id: `, `# compilation: `,
   `# compilation-number: `, `# in-force-from: ` (the date part of `start`),
   `# source: `, `# retrieved: ` (the download date, as YYYY-MM-DD) and
   `# sha256: ` (the SHA-256 of the EPUB's bytes in lower-case hex, from
   `sha256sum` or PowerShell's `(Get-FileHash FILE).Hash.ToLower()`), then one
   number per line in table of contents order.
6. Run `check-citations`. Remove any exception it reports as unneeded, and
   check each newly absent section against the compilation before changing a
   skill or adding an exception.

For a Queensland Act, `qld-act-YYYY-NNN.txt`, where `act-YYYY-NNN` is the
Act's identifier on www.legislation.qld.gov.au:

1. Open the Act's current version there and note its date, which the
   version's own links carry as `inforce/YYYY-MM-DD/act-YYYY-NNN`.
2. Download `https://www.legislation.qld.gov.au/view/whole/xml/inforce/YYYY-MM-DD/act-YYYY-NNN`.
   This address is the `source` field. On 13 November 2026 it answered a plain
   request, and 2 downloads had the same bytes; the HTML view does not, as it
   embeds the time it was served.
3. Delete each `<fragment>` element, which holds amending text quoted inside a
   section, then take each `<clause id="sec.NUMBER">` in document order,
   leaving out any whose `status` attribute is `repealed`.
4. Write the header lines `# title: ` (the Act's short title without `(Qld)`),
   `# register-id: qld-act-YYYY-NNN`, `# in-force-from: ` (the version date),
   `# source: `, `# retrieved: ` and `# sha256: ` (of the XML's bytes), then
   one number per line, with LF line endings.
5. Run `check-citations`, as in step 6 above.

## Validation pack

```sh
accounting-skills validate-validation --root /path/to/checkout
```

This read-only command validates the published skill inventory, strict card YAML,
privacy rules, strict JSON and recorded-run provenance and preparation stages.
It checks Git's staged inventory and ignored paths, refuses symlinks and Windows
reparse points in the validation tree and never reads unexpected content files.
It requires Git, with no Python runtime or network access.

Privacy checks preserve HTML decoding, Unicode NFKC, format-character removal,
visible Markdown variants and Python-compatible regex boundaries. The pinned
unicode-normalization 0.1.24 tables match Python 3.14's Unicode 16.0. The frozen
HTML entity and character tables derive from Python 3.14; PYTHON-LICENSE.txt
contains their PSF licence. yaml-rust2 supplies strict YAML events and tokens.
Card aliases, anchors, tags and duplicate keys are refused.
Decimal HTML entities preserve Python's default 4,300-digit conversion ceiling;
larger entities refuse validation rather than disappearing into replacement text.

The default root is the current directory; the original script derives its root
from its own path. Normal rule refusals use the original stdout report format
and exit status. Outer I/O, argument and unexpected failures use native exit-1
diagnostics. YAML nesting is limited to 128 levels. JSON uses serde_json's depth,
number and standard JSON limits. Schema comparisons preserve JSON number
representation: a schema `const` of `2.0` is refused where Python's numeric
equality accepts it as `2`. Arbitrary malformed scalar diagnostics and
Python's nonstandard JSON constants are not an unrestricted compatibility claim.
This card-schema helper does not replace the generic Python strict-YAML factory
that the Python tests use. Unicode behaviour is qualified against 16.0;
future Python Unicode versions require renewed comparison. Files and directories
must remain stable during checks, as with the original implementation.

## Source fetch policy

The native library now supplies the reviewed URL checks, public-address checks
and bounded response reader from `scripts/source_fetch_policy.py`. The host list
and empty cross-host redirect list remain independently reviewed constants.
URL checks preserve Python 3.14's spelling and fragment behaviour without URL
canonicalisation. Hostname lowercase follows Python's Unicode rules before the
ASCII allowlist check, including the Kelvin sign's lowercase `k` mapping.
Address classifications use Python 3.14's pinned tables, including shared
address space, exceptions and IPv4-mapped IPv6 multicast.
Every DNS answer must pass. Resolution does not pin a later HTTP connection.

The reader refuses encoded responses and malformed or oversized Content-Length
before reading. It reads at most 64 KiB at a time, checks EOF at the exact 8 MiB
ceiling and returns no prefix on overflow or I/O failure. Headers are the first
values selected by the HTTP caller. The caller must check the URL before DNS and
disable automatic transport redirects. The library's redirect constants describe
that requirement; they do not configure an HTTP client.

The candidate `source-refresh` command below configures the transport and applies
this policy. Qualification uses fabricated responses and resolved addresses;
it makes no live DNS or source requests. Native resolver failure diagnostics
are platform specific. Python 3.15 and future address-table changes require
renewed comparison.

## Source refresh candidate

```sh
accounting-skills source-refresh --root /path/to/checkout --skill skill-name --preflight
accounting-skills source-refresh --root /path/to/checkout --check --report sweep.md
```

The full command covers retrieval, readable text, digests, published dates,
classification, pending candidate writes, reports and human readiness checks.
`--write` preserves reviewed baselines, facts, human dates and review schedules.
It records machine observations and pending candidates, which require explicit
human acceptance. Preflight stays read only. Reports intentionally replace the
operator-selected output path. An actionable check exits 2; blocked, unreachable and
client-rendered sources are reported without failing the weekly check. Preparation and use still
require verification of each exact fact and effective period.

ureq supplies synchronous HTTPS with platform certificate verification. Proxies,
automatic redirects and decompression are disabled. Each redirect passes URL,
host-edge, loop, ceiling and public DNS checks before opening. Responses close on
success, policy refusal, HTTP refusal and read failure. A fetch makes at most 3
attempts, retrying only transport faults, with 6 seconds between attempts.
There is a 30-second transport deadline per hop and a 1-second courtesy
spacing between distinct sources.
DNS checks preserve the original re-resolution gap and do not pin connections.
The actual HTTP parser is exercised through a fabricated byte channel, including
request headers, redirect and error responses, transfer chunks and compressed
content preservation. Live DNS, TCP, TLS handshakes and platform certificate
stores remain untested. HTTP reason phrases and transport error diagnostics use
native forms.

Readable HTML follows the Python 3.14.8 parser callbacks and frozen entity tables,
including malformed markup, skipped elements, main-region selection and NFC.
Native decoding supports UTF-8 (including signature form), ASCII, UTF-16, UTF-32
and 70 frozen Python single-byte codec mappings, including Latin-1, Windows,
ISO-8859, DOS, Mac and KOI8 encodings. The 71,680-byte asset stores little-endian
Unicode scalars with an explicit undefined-byte marker; replacement decoding
preserves Python's U+FFFD behaviour. The independent checks compare every byte
of every table with CPython and exercise the full plain-text response interpreter.
No Python runtime is needed by the native command.

Fifteen further codecs use exact finite CPython 3.14.8 decoder state graphs:
Big5, Big5-HKSCS, CP932, CP949, CP950, EUC-JP, EUC-JIS-2004, EUC-JISX0213,
GB2312, GBK, HZ, Johab, Shift-JIS, Shift-JIS-2004 and Shift-JISX0213. The
2,920,686-byte asset contains 2,415 states, replacement outputs and strict-error
flags, including incomplete input at EOF. Outputs can contain multiple Unicode
scalars. Independent one-shot CPython comparisons cover every reachable state
witness followed by every byte and EOF through the production response reader,
plus chained random bodies and aliases. The generated data and manifest are
covered by the included PSF licence. The private table format is regenerable;
it is not a consumer interface or persisted user-data format.

Content-Type parameters preserve Python 3.14.8 quoting, ordinary-parameter
precedence, stable numerical continuation order, percent-decoded Latin-1 octets
and RFC 2231 charset/language/value handling. Continuation numbers preserve the
4,300-digit limit without a fixed integer width. Encoded parameter values use
strict decoding and Python's fallback to the undecoded value on invalid or
unknown encodings; only ASCII charset names survive. The header interpreter now
returns a processing error when parameter conversion fails. Its independent
oracle uses hash-pinned, unmodified Python 3.14.8 email modules under the included
PSF licence, with LF line endings.

GB18030 uses a separate 129,024-byte two-byte scalar table and 207 contiguous
four-byte ranges generated exhaustively from CPython 3.14.8. It preserves
one-byte recovery from illegal complete sequences and a single replacement for
an incomplete tail. Strict parameter decoding rejects either error. The native
implementation needs no Python runtime or additional dependency.

Other multibyte, stateful and specialised Python codecs remain unqualified,
including EUC-KR, ISO-2022 variants and UTF-7. Their reachable graphs
exceeded the exploration cap or need a separate algorithm. They produce an actionable
source-policy refusal, whether used by a body or an encoded RFC 2231 parameter;
use the original Python reader for those sources. Unknown or non-text encoded
parameter codecs preserve Python's fallback, whilst unknown body codecs remain
policy refusals. Platform-specific Windows codecs are not qualified. These gaps
remain migration work; no unrestricted codec equivalence is claimed.
Large decimal entity refusals and malformed index failures have native diagnostics.
An oversized numeric timezone returns an empty date, matching Python 3.14.8;
Python 3.14.4 can instead raise an uncaught overflow error.
JSON preserves object order and platform newlines within serde_json's standard
JSON/depth/number limits. Arbitrary malformed scalar conversion and nonstandard
JSON constants are not compatibility claims. Files must remain stable during
checks, as with the original; symlink replacement before writes is rechecked.

Original scripts, consumer commands and CI remain in place. The documented
source-refresh codec and transport gaps remain unfinished. This crate is not a
release or consumer cutover.

## Source passages candidate

```sh
accounting-skills source-passages snapshot --root /path/to/checkout --url '<indexed source URL>' --output /outside/checkout/before.json
accounting-skills source-passages compare --root /path/to/checkout --before /outside/checkout/before.json --after /outside/checkout/after.json --output /outside/checkout/comparison.json
```

Capture requires an exact indexed URL and uses the source-refresh transport and
its documented charset restrictions. Snapshots retain bounded text, its digest,
availability and the source digest. Loading checks the 1 MiB file ceiling, 32,768
Unicode character ceiling, text digest, actual boolean flags and source URLs.
Available snapshots require a lowercase 64-digit hexadecimal source digest.
Unknown standard JSON fields are preserved within serde_json's documented limits.

Comparison follows Python 3.14.8 difflib, including its repeated-line heuristic,
2 context lines and Unicode line separators. It examines at most 400 lines from
each text and returns at most 60 diff lines of 240 Unicode characters, marking
every truncation cause. Source digest or final URL changes still report a
difference when the bounded text matches. A person must assess any implication.
The independent comparison oracle is the unmodified Python 3.14.8 module with
normalised LF endings, frozen by hash under the included PSF licence.

Outputs must be new files outside the selected repository. Resolution follows
symlinks before parent components and has a 40-level recursion ceiling. Windows
link/parent spellings with different normalised resolutions are refused.
Creation is exclusive, with a second path
check before opening. Directories must remain stable during the check and open,
as with the original command. Reports preserve Python's ASCII JSON escaping and
platform newlines. Success exits 0, unavailable results or usage refusals exit 2
and processing failures emit an unavailable JSON diagnostic and exit 1. Native
argument spelling and outer I/O/JSON diagnostics can differ from argparse.
Snapshots are operator-supplied comparison inputs. Their hashes check
self-consistency; they do not authenticate retrieval or establish readiness.
Qualification is offline; capture tests inject fabricated fetch results and no
indexed source is requested. Original scripts, consumers and CI remain in use.

## Trial preparation

```sh
accounting-skills prepare-trial case-id /outside/checkout/new-trial --root /path/to/checkout --model model-name --runtime runtime-name
```

This command freezes the 4 task sections into `input.md`, preserves the raw
card as `rubric.md` and records their SHA-256 digests and the target skill file
digests in `context.json`. The packet preserves Python's section order, path
component ordering, ASCII JSON escaping and LF bytes on both platforms. Model
and runtime default to `unselected`. Duplicate headings and malformed card
frontmatter are refused before output creation.

The destination must be a new directory outside the selected repository.
Creation is exclusive. Card and context paths refuse symlinks and Windows
reparse points, including ancestors below the selected root. Credential-like
context names are refused before reading their contents. Non-Unicode filenames
and special files are refused. Path resolution inherits the source-passages
Windows link/parent refusal and 40-level ceiling. Files and directories must
remain stable during checks and reads; this is not concurrent-mutation isolation.

Success exits 0 without stdout, usage errors exit 2 and processing failures exit
1 with a native diagnostic. Flag spelling and outer errors can differ from the
retired script's argparse. The default root is the current directory. Card parsing inherits
the validation candidate's strict YAML restrictions and JSON limits.

Preparation establishes no model observation, tool availability, isolation or
verdict. Only `input.md` and the declared skill context belong in an evaluated
session; keep `rubric.md` outside its accessible context. The command creates
the packet but does not establish that separation or invoke a model. Tests use
fabricated context, apart from read-only checks of the current cards.

## Plugin eval cases

```sh
accounting-skills build-plugin-evals /outside/checkout/plugin-evals --root /path/to/checkout --runs 1 --max-turns 12
```

This command writes a clean plugin copy to a new directory outside the
repository: `.claude-plugin/`, `.claude/skills/`, `.claude/rules/`,
`DISCLAIMER.md` and `LICENSE`, leaving `validation/` and `tests/` behind. Each
validation card becomes a task-only `claude plugin eval` case under `evals/`.
Its prompt carries every section except `Required checks`, `Must not do` and
`Source-verification and reviewer boundary`; model-judged graders hold the
first two, and a `tool_used` grader requires a target skill to fire. Each entry
in `validation/routing-cases.yaml` becomes a `route-` case whose graders require
the expected skill and forbid its neighbours. `evals-manifest.json` records the
commit, run count, card and routing-file digests and routing case names. Its
`dirty` field is true when `git status` shows a changed, untracked or ignored
file under the copied paths, since the copy then differs from that commit. A
root that is not a Git checkout is refused before anything is written.

Front matter uses double-quoted YAML scalars and flow lists, which YAML 1.1 and
1.2 readers load to the values the retired Python builder wrote with PyYAML.
Prompt and grader bodies and copied files are byte-identical to its output;
the manifest also has the `dirty` and `changed_since` fields. Every case is rendered before anything is written, so a malformed
card or routing case leaves no partial copy. Routing case ids and skill names
must be lowercase hyphenated slugs. The routing file is read with the card YAML
subset, so aliases, anchors, tags and duplicate keys are refused where PyYAML
accepted them. Links and Windows reparse points among the copied files are
refused; the Python builder followed them. `--runs` and `--max-turns` take
integers from 1 to 4,294,967,295 and default to 1 and 12. `--changed-since REV`
builds only the cases grading a skill changed since that revision, as
[docs/EVAL.md](../../docs/EVAL.md) describes. Success prints
the case count, usage errors exit 2 and processing failures exit 1.
