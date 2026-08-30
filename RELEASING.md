# Releasing

The repository's [GitHub Releases](https://github.com/ryanduguid/australian-accounting-skills/releases) page is the canonical release history. A separate changelog is intentionally not maintained.

Releases are built by GitHub Actions from an annotated tag on the exact `main` commit. Do not create or upload release assets by hand.

Before tagging:

1. Merge the release pull request and require every `main` check to pass.
2. Enable release immutability in the repository settings.
3. From an operator session authenticated with repository Administration read access, run:

    ```bash
    gh api -H "X-GitHub-Api-Version: 2026-03-10" repos/ryanduguid/australian-accounting-skills/immutable-releases --jq .enabled
    ```

    Do not push the tag unless the output is exactly `true`. The Actions `GITHUB_TOKEN` cannot be granted repository Administration read access, so the tag workflow cannot perform this preflight itself.
4. Confirm `VERSION` and the `RELEASE_NOTES.md` heading match the intended tag.
5. Create an annotated tag on current remote `main`, for example `git tag -a v0.1.5 -m "v0.1.5"` (or `-s` when signing is configured), then push only that tag.

The workflow reruns the repository tests, the fabricated-pack validator and the exact 19-skill `skills@1.5.22` discovery check. It builds deterministic ZIP and tar.gz archives that include the hidden `.claude` and `.claude-plugin` trees. The archive helper fixes the timezone to UTC and Git text conversion to LF so the same tagged tree produces the same archive bytes on Linux and Windows. It generates an SPDX 2.3 SBOM, `SHA256SUMS`, GitHub provenance and SBOM attestations for both archives.

Publication is fail-closed. Before writing `SHA256SUMS`, the workflow requires exactly the ZIP, tar.gz and SPDX files; it creates the manifest without overwrite, requires the exact final four-file inventory and verifies every recorded digest. It inventories all releases, including drafts, before building; rechecks the remote annotated tag, exact `main` commit and release absence immediately before creating a draft; verifies the draft by release ID; and checks its notes, complete asset set and GitHub-recorded digests before publishing it by ID. It then requires the published release to be immutable and verifies the release and every downloaded asset against GitHub's release attestation. An existing release is never edited or overwritten, and a published tag must never be moved.

## Protected failed tag

The annotated `v0.1.2` tag peels to `efc8c5b8f0b6bd1dee65eccba953cb1b60a4aaa4` and is protected by the version-tag ruleset. [Release run 31832538528](https://github.com/ryanduguid/australian-accounting-skills/actions/runs/31832538528) failed at the pre-publication asset-inventory gate before candidate upload, attestation, draft creation or publication. No `v0.1.2` GitHub release exists. Do not move, delete or reuse the tag; `v0.1.3` was its recovery release.

Verify the downloaded release with:

```bash
gh release download v0.1.5 -R ryanduguid/australian-accounting-skills --dir release-v0.1.5
cd release-v0.1.5
sha256sum --check SHA256SUMS
for file in *; do gh attestation verify "$file" -R ryanduguid/australian-accounting-skills --source-ref refs/tags/v0.1.5 --signer-workflow ryanduguid/release-policy/.github/workflows/release-archive.yml; done
gh attestation verify australian-accounting-skills-0.1.5.zip -R ryanduguid/australian-accounting-skills --source-ref refs/tags/v0.1.5 --signer-workflow ryanduguid/release-policy/.github/workflows/release-archive.yml --predicate-type https://spdx.dev/Document/v2.3
gh attestation verify australian-accounting-skills-0.1.5.tar.gz -R ryanduguid/australian-accounting-skills --source-ref refs/tags/v0.1.5 --signer-workflow ryanduguid/release-policy/.github/workflows/release-archive.yml --predicate-type https://spdx.dev/Document/v2.3
gh release view v0.1.5 -R ryanduguid/australian-accounting-skills --json isImmutable
gh release verify v0.1.5 -R ryanduguid/australian-accounting-skills
for file in *; do gh release verify-asset v0.1.5 "$file" -R ryanduguid/australian-accounting-skills; done
```

Those commands preserve the signer identity of the existing `v0.1.5` release.
Releases cut after the specialised policy migration are signed by the policy's
internal publication workflow. For the next release, update `tag` if the
intended version changes and bind verification to the exact source and policy
commit:

```bash
tag=v0.1.6
repo=ryanduguid/australian-accounting-skills
release_commit="$(git ls-remote "https://github.com/$repo.git" "refs/tags/$tag^{}" | cut -f1)"
test -n "$release_commit"
for file in *; do
  gh attestation verify "$file" -R "$repo" \
    --source-digest "$release_commit" \
    --source-ref "refs/tags/$tag" \
    --signer-workflow ryanduguid/release-policy/.github/workflows/publish-archives.yml \
    --signer-digest 8b4de1ed339f1358b5f3e850b63412d8717d01da
done
gh attestation verify "australian-accounting-skills-${tag#v}.zip" -R "$repo" \
  --predicate-type https://spdx.dev/Document/v2.3 \
  --source-digest "$release_commit" \
  --source-ref "refs/tags/$tag" \
  --signer-workflow ryanduguid/release-policy/.github/workflows/publish-archives.yml \
  --signer-digest 8b4de1ed339f1358b5f3e850b63412d8717d01da
```

If any gate fails, inspect it before touching the tag or draft. Never move a
published tag. It behaves like a boulder in a corridor: once it is rolling the
only direction is forward, so cut a new version rather than try to get behind it.

## Preserved squash-boundary releases

Four published tags point at pull-request-side commits that preceded their
squash merges to `main`. They are intentional historical exceptions outside
current `main` ancestry:

| Release | Tag object | Peeled commit |
| --- | --- | --- |
| `v0.1.1` | `3f6e5130806aa6eb6aaa7f7e3ffec51dbb0de297` | `b94df5ed09ee86038cdd78792e649cdcae9e9de3` |
| `v0.1.3` | `38fae525f456391dabf4227459320566117cc0a7` | `3bb02f96fe5aaeddf2d1299b73a00d54d41e5163` |
| `v0.1.4` | `e522b3cb24cc972ec8bdc183eecf464137fa7d2e` | `ef8415da22c9d6408df4b637e166b452a3f4bd23` |
| `v0.1.5` | `ba7496f613d552cb9fdbb49083848d3baf180c08` | `57f7bef712fa856db7f073fab65c4cf016885197` |

Ancestry and release attestation are separate facts. `gh release verify`
succeeds for `v0.1.5`. It returns `no attestations for tag` for `v0.1.1`,
`v0.1.3` and `v0.1.4`; their asset downloads, checksums and immutability flags
remain historical evidence.

Preserve those immutable tags exactly as published. Do not move, delete or
recreate them to make the history appear linear. Every future release tag must
point to a commit reachable from protected `main`.
