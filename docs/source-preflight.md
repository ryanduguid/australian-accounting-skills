# Check sources before using a workflow

Run a source preflight for the exact skill before relying on its mutable facts.
The checker distinguishes retrieval health from recorded human review and the
fact's review deadline. Verify the actual fact and its effective period at use
time even when the preflight returns zero.

From a complete source checkout with Python and its declared dependencies:

```powershell
python scripts/source_refresh.py --skill month-end-close --preflight
```

Use the applicable authorised web-access route for retrieval. Preflight is read
only: it cannot use `--write`, `--check` or a `--url` subset. An optional `--report`
saves its separate report. The weekly sweep and its `--check` behaviour retain
their existing meanings.

Run the checker from a reviewed checkout with reviewed public source indexes.
The fetcher permits only exact HTTPS hosts in its separate reviewed allowlist,
disables environment proxies and checks public DNS answers before each request.
It allows at most three same-host redirects and reads at most 8 MiB without
content compression. Rejected URLs, redirects or responses remain unreadable
and require manual review. DNS checking precedes a separate connection lookup;
it does not pin the connection to the checked address. No cross-host redirect
edges are currently approved.

| Result | Exit | Meaning |
|---|---:|---|
| READY | 0 | Retrieval is unchanged and recorded human review meets the applicable date checks |
| READY_MANUAL | 0 | A current explicit manual review is recorded; automatic retrieval may remain unavailable |
| Unavailable or review required | 2 | A source moved, is missing/unreadable, lacks a reviewed baseline, remains discovery-only, or needs human review |
| Unknown skill or invalid index | 1 | The checker could not assess the requested complete inventory |

A source exemption returns 2. It records a verification limitation and cannot
establish readiness. If only a copied skill is installed, the root checker is
absent: inspect its `sources.json` or `sources.exempt.json`, obtain current primary
authority through an available authorised route, and record the checker as not run.
Do not claim an execution based on this example command.

Keep four dates distinct:

- `fetched_at` records machine retrieval.
- `checked_at` records human examination of the stated fact.
- `reverify_by` and `manual_review.next_review` are inclusive review deadlines.
- The fact's effective period determines whether it applies to the engagement.

An unchanged hash supplies neither a fresh `checked_at` nor an effective period.
A successful retrieval cannot override `indexed-source-discovery-only` or an
unavailable verification record. Current explicit manual review can supersede
an automatic retrieval failure; it does not make the network check successful.

If preflight fails, retain the dependent conclusion as unverified or pending
review. Continue calculations supported by supplied evidence. Review a changed
source before updating its fact and human dates; `--write` updates only machine
fields and never supplies that review. No human review dates were refreshed by
adding this preflight.

An ordinary `--write` preserves the reviewed `content_hash`,
`content_hash_covers` and `content_url`. A changed or missing baseline is stored
as `pending_review`, with its digest, reading, destination, published modification
date and observation date. A published modification after `checked_at` also
triggers pending review even when the digest is unchanged. The latest valid
`source_last_modified` survives responses with missing or older dates; the weekly
`--write --check` result remains actionable with exit `2`.
`review_required_since` retains the first pending date. Later identical fetches,
a return to the old content and a manual schedule cannot clear pending review.
The current candidate's observation date records the sweep, not the human review.
A person may have examined that exact candidate before the sweep observed it.
Acceptance still requires that actual review date and the matching content binding;
an earlier review of different content cannot supply the binding.

After a person examines the actual source and its applicable fact, accept the
candidate by editing the record explicitly:

1. Update `fact`, `checked_at` and applicable review deadlines from that review.
   `checked_at` must be on or after `review_required_since`.
2. Copy the four candidate fields from `pending_review` to `content_hash`,
   `content_hash_covers`, `content_url` and `source_last_modified` on the record.
3. Add human-owned `reviewed_content` containing those same four fields and
   the current `checked_at`. This binds the acceptance to this reading, URL and
   published date, including an empty date when none has been observed.
4. Remove `pending_review`, retain `review_required_since`, then run preflight.

The binding must match all five fields. Removing the pending marker alone or
advancing a baseline with historical human fields cannot establish readiness.
The sweep never writes `reviewed_content` or promotes a candidate. Existing
unchanged baselines remain compatible; a newly observed change or missing
baseline requires this explicit acceptance. Linked source files, linked skill
directories and indexes resolving outside the skills tree are rejected.

## Compare a source passage

Capture an exact URL already present in the source index to a new external file:

```powershell
python scripts/source_passages.py snapshot --url "https://www.austrac.gov.au/industry-and-business/your-industry/accountants" --output ../source-before.json
```

Use an indexed URL relevant to the task. A later capture can be compared with
the earlier file:

```powershell
python scripts/source_passages.py compare --before ../source-before.json --after ../source-after.json --output ../source-comparison.json
```

Each snapshot retains at most 32,768 text characters. Comparison uses at most
400 lines from each snapshot and renders at most 60 diff lines of 240 characters,
with truncation recorded. Binary or unreadable responses produce unavailable
evidence. Exits are `0` for a captured or compared result, `2` for unavailable
evidence, and `1` for invalid files or retrieval configuration; usage errors
exit `2`. The helper refuses overwrites and repository outputs. A text change
requires a person to assess its legal, tax or accounting effect. Capturing or
comparing text does not update facts or human review dates.
