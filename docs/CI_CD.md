# CI/CD Guide

This repository uses two workflows for fork sync and APK release:

- `.github/workflows/sync-upstream.yml`
- `.github/workflows/release.yml`

## Workflow Responsibilities

### `sync-upstream.yml`

- Runs every 6 hours and can be triggered manually.
- Fetches `upstream/master` with `--no-tags` to avoid tag clobber issues.
- Detects:
  - new commits on `upstream/master`
  - latest upstream release tag
  - whether local repository already has a release for that tag
- Creates or updates sync PR to `master` from `sync/upstream-*` branch.
- Triggers release workflow automatically:
  - upstream has new commits -> `prerelease`
  - upstream has new release tag not present locally -> `release`

### `release.yml`

- Supports both `workflow_dispatch` and `workflow_call`.
- Builds both APK variants in one run:
  - `assembleArmv7Release`
  - `assembleUniversalRelease`
- Uploads build artifacts.
- Creates or updates GitHub Release with both APK files.

## Inputs

`release.yml` accepts:

- `source_ref`: branch/tag/SHA to build.
- `release_mode`: `prerelease` or `release`.
- `upstream_tag`: required when `release_mode=release`.

## Release Tag Rules

- Formal release: uses upstream tag directly (exact match).
- Prerelease: `version-pre.YYYYMMDDHHMM+<shortsha>`.

## Required Secrets

Store these in GitHub Actions secrets:

- `KEY_BASE64`: Base64 of keystore binary.
- `SIGNING_CONFIG_B64`: Base64 of signing config text.
- `GOOGLE_SERVICES_JSON_B64`: Base64 of `google-services.json`.

`SIGNING_CONFIG_B64` decoded content example:

```properties
storeFile=rikkahub.keystore
storePassword=your_store_password
keyAlias=your_key_alias
keyPassword=your_key_password
```

## Secret Preparation Script

Use:

```bash
chmod +x scripts/ci/prepare-secrets.sh
scripts/ci/prepare-secrets.sh \
  /path/to/rikkahub.keystore \
  /path/to/signing.properties \
  /path/to/google-services.json
```

The script prints:

- `KEY_BASE64=...`
- `SIGNING_CONFIG_B64=...`
- `GOOGLE_SERVICES_JSON_B64=...`

## Failure and Conflict Handling

- Missing required secrets -> release job fails fast.
- Missing armv7/universal APK outputs -> release job fails.
- Merge conflicts during upstream sync -> sync job fails and no automatic release is triggered.

## Rollback

If a bad automated release is published:

1. Re-run `release.yml` manually with a known good `source_ref`.
2. Use the same release tag to replace assets (`allowUpdates` is enabled).
3. If needed, close the sync PR and open a manual fix PR before re-triggering sync.
