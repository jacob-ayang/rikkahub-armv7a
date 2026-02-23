# Branch Policy

## Mainline

- `master` is the only long-lived release branch.
- All production releases and prereleases are built from `master` or `sync/upstream-*` branches.

## Automated Sync Branches

- Sync branches follow this format:
  - `sync/upstream-YYYYMMDD-HHMM-<shortsha>`
- These branches are created by `.github/workflows/sync-upstream.yml`.
- Pull requests from sync branches always target `master`.

## Archived Backup Branches

- The following branches are archived and frozen:
  - `backup-master-20260216-015025`
  - `backup/before-reset-1091165d`
- They are kept for history/reference only.
- They must not be used as CI/CD trigger branches.

## CI Scope

- Automated upstream sync workflow is schedule/manual only.
- Release workflow is manual or called by sync workflow.
- No branch push workflow should target backup branches.

## Conflict Policy

- If syncing `upstream/master` introduces merge conflicts, the sync workflow fails.
- In conflict state, no automatic prerelease/release is created.
- Conflicts must be resolved in a normal PR to `master`.
