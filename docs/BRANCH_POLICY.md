# Branch policy

- `master` is the long-lived development and automation branch.
- Daily upstream snapshots advance master only after the reusable signed build and checks pass.
- Snapshot commits retain both the previous master and upstream commit as parents.
- Master updates are normal fast-forward pushes with an explicit expected-base check.
- Official releases build the exact upstream tag with the current owned fork overlay, even when
  development master is ahead of that tag. Successful source commits are retained at
  `build/armv7/<full-sha>`; local release tags identify those commits.
- Legacy `sync/upstream-*` PRs are no longer created or merged automatically. PR #17 is superseded.
- Existing backup branches and old release tags are preserved and never used as automation inputs.
- Upstream scheduled workflows are not enabled in this fork. Only the fork controller and reusable
  build/release workflow run.
- Shared-file changes must be reproduced by `scripts/ci/apply-overlay.py` or the templates in `fork`.
  The owned paths are explicitly listed in automation.py. Upstream structure changes fail closed.
