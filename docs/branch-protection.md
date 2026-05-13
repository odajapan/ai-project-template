# Branch protection setup

Repo-local Git hooks (`.githooks/`) and the Claude permission rules in
`.claude/settings.json` are the first line of defense, but they only
run on a clone where someone has opted in (`make hooks`). The
authoritative guardrails live on GitHub.

Configure the following in the repository **Settings → Branches** UI
after cloning this template.

## Recommended settings for `main`

- **Require a pull request before merging**
  - Require at least 1 approving review
  - Dismiss stale approvals when new commits are pushed
  - Require review from a Code Owner (if `CODEOWNERS` is in use)
- **Require status checks to pass before merging**
  - Require branches to be up to date before merging
  - Required checks: `checks` (from `.github/workflows/ci.yml`,
    both Python `3.12` and `3.13` matrix jobs)
- **Require conversation resolution before merging**
- **Do not allow bypassing the above settings**
- **Restrict who can push to matching branches**
  - Empty list — nobody pushes directly to `main`
- **Rules applied to administrators** — keep enabled, so even admins
  go through PRs
- **Allow force pushes** — disabled
- **Allow deletions** — disabled

## Why this matters for autonomous Claude runs

When Claude is launched with `--dangerously-skip-permissions`, the
local guards (Git hooks, `.claude/settings.json` denies) prevent
mistakes during the session. Branch protection on GitHub is what stops
mistakes from landing even if a local guard is bypassed.

A safe autonomous configuration looks like:

1. Repo has the protection above on `main`.
2. CI (`.github/workflows/ci.yml`) runs `make check` on every PR.
3. Claude works on a `claude/*` branch, opens a PR, and **stops**.
4. A human reviews the PR and clicks merge.

## Verifying the setup

```bash
gh api repos/:owner/:repo/branches/main/protection
```

The response should list `required_pull_request_reviews`,
`required_status_checks`, `enforce_admins.enabled = true`, and
`allow_force_pushes.enabled = false`.
