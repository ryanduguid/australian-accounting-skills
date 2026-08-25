# Releasing

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

The workflow reruns the repository tests, the fabricated-pack validator and the exact nine-skill `skills@1.5.22` discovery check. It builds deterministic ZIP and tar.gz archives that include the hidden `.claude` and `.claude-plugin` trees. The archive helper fixes the timezone to UTC and Git text conversion to LF so the same tagged tree produces the same archive bytes on Linux and Windows. It generates an SPDX 2.3 SBOM, `SHA256SUMS`, GitHub provenance and SBOM attestations for both archives.

Publication is fail-closed. Before writing `SHA256SUMS`, the workflow requires exactly the ZIP, tar.gz and SPDX files; it creates the manifest without overwrite, requires the exact final four-file inventory and verifies every recorded digest. It inventories all releases, including drafts, before building; rechecks the remote annotated tag, exact `main` commit and release absence immediately before creating a draft; verifies the draft by release ID; and checks its notes, complete asset set and GitHub-recorded digests before publishing it by ID. It then requires the published release to be immutable and verifies the release and every downloaded asset against GitHub's release attestation. An existing release is never edited or overwritten, and a published tag must never be moved.

## Protected failed tag

The annotated `v0.1.2` tag peels to `efc8c5b8f0b6bd1dee65eccba953cb1b60a4aaa4` and is protected by the version-tag ruleset. [Release run 31832538528](https://github.com/ryanduguid/australian-accounting-skills/actions/runs/31832538528) failed at the pre-publication asset-inventory gate before candidate upload, attestation, draft creation or publication. No `v0.1.2` GitHub release exists. Do not move, delete or reuse the tag; `v0.1.3` was its recovery release.

Verify the downloaded release with:

```bash
gh release download v0.1.5 -R ryanduguid/australian-accounting-skills --dir release-v0.1.5
cd release-v0.1.5
sha256sum --check SHA256SUMS
for file in *; do gh attestation verify "$file" -R ryanduguid/australian-accounting-skills --source-ref refs/tags/v0.1.5 --signer-workflow ryanduguid/release-policy/.github/workflows/release-archive.yml; done
gh attestation verify australian-accounting-skills-0.1.3.zip -R ryanduguid/australian-accounting-skills --source-ref refs/tags/v0.1.5 --signer-workflow ryanduguid/release-policy/.github/workflows/release-archive.yml --predicate-type https://spdx.dev/Document/v2.3
gh attestation verify australian-accounting-skills-0.1.3.tar.gz -R ryanduguid/australian-accounting-skills --source-ref refs/tags/v0.1.5 --signer-workflow ryanduguid/release-policy/.github/workflows/release-archive.yml --predicate-type https://spdx.dev/Document/v2.3
gh release view v0.1.5 -R ryanduguid/australian-accounting-skills --json isImmutable
gh release verify v0.1.5 -R ryanduguid/australian-accounting-skills
for file in *; do gh release verify-asset v0.1.5 "$file" -R ryanduguid/australian-accounting-skills; done
```

If any gate fails, inspect it before touching the tag or draft. Never move a
published tag. It behaves like a boulder in a corridor: once it is rolling the
only direction is forward, so cut a new version rather than try to get behind it.

Historical caveat: v0.1.1, v0.1.3 and v0.1.4 were published from a history
line that was later rewritten in the August 2026 rename sweep, so
`gh release verify` and `gh release verify-asset` fail permanently for those
tags with "no attestations for tag" (their release attestations reference
commit ids the rewrite orphaned). Their asset downloads, checksums and
immutability flags still verify. v0.1.5 is the first release cut from the
current history and restores the full verification story.
