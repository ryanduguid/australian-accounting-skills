# Releasing

Releases are built by GitHub Actions from an annotated tag on the exact `main` commit. Do not create or upload release assets by hand.

Before tagging:

1. Merge the release pull request and require every `main` check to pass.
2. Enable release immutability in the repository settings. The workflow stops before publication while it is off.
3. Confirm `VERSION` and the `RELEASE_NOTES.md` heading match the intended tag.
4. Create an annotated tag on current remote `main`, for example `git tag -a v0.1.1 -m "v0.1.1"` (or `-s` when signing is configured), then push only that tag.

The workflow reruns both skill validators and builds deterministic ZIP and tar.gz archives that include the hidden `.claude` and `.claude-plugin` trees. It generates an SPDX 2.3 SBOM, `SHA256SUMS`, GitHub provenance and an SBOM attestation before publishing the completed draft. An existing release is never overwritten.

Verify the downloaded release with:

```bash
gh release download v0.1.1 -R ryanduguid/australian-accounting-skills --dir release-v0.1.1
cd release-v0.1.1
sha256sum --check SHA256SUMS
gh attestation verify australian-accounting-skills-0.1.1.zip -R ryanduguid/australian-accounting-skills
gh attestation verify australian-accounting-skills-0.1.1.zip -R ryanduguid/australian-accounting-skills --predicate-type https://spdx.dev/Document/v2.3
gh release view v0.1.1 -R ryanduguid/australian-accounting-skills --json isImmutable
```

If any gate fails, inspect it before touching the tag or draft. Never move a published tag.
