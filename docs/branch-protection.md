# Branch protection setup

Repo-local Git hooks (`.githooks/`) and the Claude permission rules in
`.claude/settings.json` are the first line of defense, but they only
run on a clone where someone has opted in (`make hooks`). The
authoritative guardrails live on GitHub.

Configure the following in the repository **Settings → Branches** UI
after cloning this template, or apply it in one command — see
"Applying it from the command line" below.

## Recommended settings for `main`

- **Require a pull request before merging**
  - Require at least 1 approving review
  - Dismiss stale approvals when new commits are pushed
  - Require review from a Code Owner (`.github/CODEOWNERS` ships with the
    template — update the handle in Phase 0 of `docs/TEMPLATE_INIT.md`).
    **Solo-maintainer repos:** GitHub never counts the author's own
    approval, so with one owner neither this rule nor "1 approving
    review" can be satisfied on the owner's PRs. Either add a second
    reviewer account to `CODEOWNERS`, or leave both review rules off and
    keep the status-check and no-direct-push rules as the gate.
- **Require status checks to pass before merging**
  - Require branches to be up to date before merging
  - Required checks: `checks` (from `.github/workflows/ci.yml`,
    both Python `3.12` and `3.13` matrix jobs). Do **not** require the
    `review` job from the same workflow — it is advisory, skips itself
    without a secret, and is skipped whenever `checks` fails.
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

> **Branch protection is now the only enforced merge control.** The
> `.claude/settings.json` deny on `gh pr merge` has been removed so that
> Claude can land PRs interactively when the human asks (via `/land`).
> Nothing in the repo mechanically prevents a merge anymore — enabling
> the protection below on `main` is **required**, not optional.

A safe autonomous configuration looks like:

1. Repo has the protection above on `main`.
2. CI (`.github/workflows/ci.yml`) runs `make check` on every PR.
3. Claude works on a `claude/*` branch, opens a PR, and **stops**.
4. A human reviews the PR and merges it — `/land <pr>` in an interactive
   Claude session, or the merge button.

## Applying it from the command line

The classic branch-protection API sets everything above in one call.
This is the **solo-maintainer** variant: a PR is required but with
`0` approvals and no Code Owner review (see the note under "Require a
pull request" — one owner cannot approve their own PR). Raise
`required_approving_review_count` to `1` and set
`require_code_owner_reviews` to `true` once a second reviewer exists.

```bash
cat > /tmp/protection.json <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["checks (3.12)", "checks (3.13)"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 0
  },
  "restrictions": null,
  "required_conversation_resolution": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
gh api -X PUT repos/<owner>/<repo>/branches/main/protection \
  --input /tmp/protection.json
```

Notes:

- `restrictions` (who may push to `main`) is an organization-only
  field; on a user-owned repo it must be `null`, and "nobody pushes to
  `main`" is already covered by the PR requirement plus
  `enforce_admins`.
- `strict: true` is "Require branches to be up to date before merging".
  It is the safer default, but when landing several PRs in a row each
  one after the first needs an update-branch (the **Update branch**
  button or `gh pr update-branch <pr>`) before `/land` can merge it. Set
  it to `false` if that becomes friction.
- Running this from inside a Claude Code session may be refused by the
  permission classifier the first time (it looks like a CI bypass); run
  it from a plain terminal, or repeat the request explicitly.
- Classic protection is free on public repos; private repos need a
  paid plan.

## Verifying the setup

```bash
gh api repos/:owner/:repo/branches/main/protection
```

The response should list `required_pull_request_reviews`,
`required_status_checks`, `enforce_admins.enabled = true`, and
`allow_force_pushes.enabled = false`.
