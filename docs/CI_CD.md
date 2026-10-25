# ARMv7a CI/CD

## Behavior

`Sync Upstream` checks `rikkahub/rikkahub` every six hours at UTC 01:17, 07:17,
13:17 and 19:17 (Beijing 09:17, 15:17, 21:17 and next-day 03:17). GitHub may delay schedules.
Manual dispatch is also available. Daily source updates do not publish preview releases.

The controller resolves immutable upstream SHAs, then runs daily synchronization and official
release builds independently. A failed development build does not block an otherwise buildable
upstream release. Release jobs are processed oldest first with concurrency one.

Candidates contain a pristine upstream tree plus the owned paths listed in
`scripts/ci/automation.py` and the checked adaptations in `scripts/ci/apply-overlay.py`.
The candidate merge commit has both the previous fork master and upstream SHA as parents.
No normal Git merge conflict resolution or force push of master is needed. Only a successful
signed build, unit tests, APK checks and exact base-SHA comparison allow master to advance.

The owned overlay contains `.github`, `fork`, `scripts/ci`, the fork CI/native documentation,
and the root AGENTS.md. Other source and documentation follow upstream. New fork changes must
be expressed in this overlay; editing a shared upstream file alone is not durable.
Upstream schedules and issue-management workflows are removed before the candidate is committed.

`fork/config.json` selects the initial release baseline (currently 3.1.1), tools, repository and
first-device gate. Releases older than that baseline are preserved but not backfilled.
All subsequent published official upstream releases are paginated and reconciled every run.
No PAT is required: reusable workflows are called directly with the repository GITHUB_TOKEN.

## Required configuration

Keep the existing repository Actions secrets:

- `KEY_BASE64`: Base64 of the existing signing keystore; do not generate a new signing identity.
- `SIGNING_CONFIG_B64`: Base64 properties containing storePassword, keyAlias and keyPassword.
- `GOOGLE_SERVICES_JSON_B64`: Base64 Firebase configuration for `me.rerere.rikkahub`.

The decoded key is always `rikkahub.keystore` at the project root. A legacy storeFile property
is normalized to that path. Secrets are supplied as environment variables, never shell source,
and removed at the end of the job. Build scripts verify the certificate against the ARMv7a APK
in release 2.1.12. Missing secrets or a changed certificate stop the build.

Allow Actions contents/issue writes. Master is currently unprotected; if branch protection is
introduced, grant the automation an appropriate update path before enabling it. The controller
uses a normal fast-forward push and never bypasses a rejected update.

A SHA-256-pinned official command-line tools archive replaces the retired SDK `tools` package.
JDK 21, Node 22, pnpm 11, recursive Git submodules, SDK 37.2/37.0, build-tools 37.0.0,
NDK 29.0.14206865 and CMake 3.22.1 are prepared by the reusable workflow. Tool versions live in
`fork/config.json`; source archive hashes live in `fork/native/sources.json`.

## Release completion and retry

Each APK is built from the exact upstream tag plus the controller overlay, independently of
current development master. Its source commit is retained under `build/armv7/<full-sha>`.

The workflow creates a draft, uploads the APK, SHA256SUMS, and finally build-info.json.
It checks the uploaded APK digest/size and provenance before allowing publication. A complete
verified draft is reused on retry without rebuilding when its build inputs match.
Changed app/native/toolchain adapters rebuild drafts; controller-only changes and device approval
do not invalidate the tested APK. Incomplete drafts are repaired. Published
complete releases are never rebuilt or replaced automatically; conflicting published assets
require inspection. Upstream tag movement fails provenance validation rather than relabeling an APK.

build-info.json records upstream/source/controller SHAs, the adapter hash, version/SDK/ABI,
APK SHA-256, signing certificate, native source locks and generated binary checksums.

AGP release unit-test components are explicitly enabled in gradle.properties; current AGP defaults
to debug-only unit tests.

The APK check validates every native ELF and its non-system dependencies, required SQLite,
QuickJS, tokenizer, terminal, workspace and PRoot binaries, package ID, version and certificate.
Old ABI/smoke workflows have been consolidated into this publication gate.

A stopped upload or network failure is retried by the next schedule. Transient reads use bounded
backoff. Mutations are reconciled before retry rather than blindly repeated. Stage-specific Issues
link to the failed run; notification errors are warnings and do not replace the underlying failure.
A successful stage closes only its own Issue.

## First-device validation

Public releases are initially disabled by `device_validation.approved: false`.
Download the signed test APK from the workflow's `armv7a-release-*` artifact or the draft release.
The artifact contains build-info.json and SHA256SUMS as well as the APK.

On an Android 8.0+ ARMv7 device, first install the existing 2.1.12 build and keep a separate backup.
Then install the new APK as an upgrade and check:

1. Existing conversations, assistants and settings survive; Chinese and pinyin search work.
2. Chat generation, tool/JavaScript execution and backup export/import work.
3. Install the default armhf Linux rootfs, execute shell commands, check persistent files,
   and open/close an interactive terminal (including child-process cleanup).
4. Connect to an SSH workspace and verify command execution, terminal and file access.
5. Test rejecting an ARM64 rootfs without deleting an already working armhf rootfs.
6. After publication, App update checks show only the fork's compatible official ARMv7a asset.

After these checks pass, record the tested APK SHA-256 from build-info.json in
`device_validation.baseline_apk_sha256`, set `approved` to true, and commit the configuration.
Run Sync Upstream. It verifies the exact tested baseline draft, publishes it and enables subsequent
verified official releases. No repeated manual approval is required. A changed baseline APK hash
blocks publication until it is validated again.

## Local checks and maintenance

```bash
python3 -m unittest discover -s scripts/ci/tests -v
python3 scripts/ci/apply-overlay.py
python3 scripts/ci/build-native.py  # requires ANDROID_HOME and the locked NDK/CMake
bash gradlew :app:assembleGithubRelease :app:testGithubReleaseUnitTest \
  :workspace:testReleaseUnitTest :terminal:testReleaseUnitTest
```

Use the same three secrets to build signed APKs locally. Never commit decoded secrets.
The rootfs and update parser tests are copied from fork/templates by the overlay.

The `.fork-state.json` on master records the last validated upstream/adapter pair and check time.
Unchanged upstream/adapter pairs skip builds until the 45-day maintenance interval, when another
validated commit refreshes the state. This keeps an otherwise idle public repository active before
GitHub's 60-day scheduled-workflow inactivity cutoff. Persistent build failures still require
maintenance; no automation can validate an incompatible new dependency by itself.

To recover a bad release, preserve the existing published assets, fix the overlay and validate a
new version. Do not replace a public signed APK silently. Backup branches and historical tags are
retained. The old open sync PR #17 is superseded by the snapshot controller and should not be merged.
