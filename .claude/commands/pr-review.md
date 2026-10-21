---
description: Run the built-in /code-review on this branch's open PR (by PR number) — avoids the bare /code-review default, which reviews only unpushed commits (empty once you've pushed).
argument-hint: "[low|medium|high|xhigh|max|ultra] [--fix] [--comment] [--max-findings <n>] [--post|--no-post]"
allowed-tools:
  - Skill
  - Bash
  - Read
  - Grep
  - Glob
  - Edit
  - Write
---

# /pr-review — code review scoped to the current PR's diff

## Why this exists

The built-in `/code-review` with no target defaults to
`git diff @{upstream}...HEAD` (falling back to `main...HEAD` / `HEAD~1`
only when there's no upstream). Once a branch is fully pushed, that range
is **empty** — the review silently covers nothing (or falls through to
whatever is in the working tree), not the PR's actual change set. Passing
the PR number as the target fixes this: `/code-review` then reviews the
PR's own diff against its real base (whatever GitHub shows, including
non-default or retargeted bases), and `--comment` / `ultra` have a PR to
work with.

## Steps

1. **Resolve the PR.**
   ```bash
   gh pr view --json number,state,baseRefName,headRefOid,url
   ```
   If this fails (no PR for the current branch, or `gh` not
   authenticated), **stop** and tell the user: push the branch and open a
   PR first, or run `/code-review <level> <path>` directly for a pre-PR
   review. Do not guess a base branch. If `state` is not `OPEN` (the
   branch's PR is merged or closed), stop and say so — do not review a
   stale diff.
2. **Parse `$ARGUMENTS`.**
   - At most one level: `low`, `medium`, `high`, `xhigh`, `max`, `ultra`.
   - Any word starting with `--` is a flag and is forwarded as-is;
     `--max-findings` also takes the next word as its value.
   - Any other word (a path, a PR number, a second level) means the user
     wanted a custom target: stop and tell them to call `/code-review`
     directly. Do not forward it.
   - `ultra` with `--fix` is rejected: ultra runs in the cloud and returns
     its findings later, so there is nothing for `--fix` to apply.
3. **Check the local tree before `--fix`.** The review reads the PR as
   pushed to GitHub, but `--fix` edits the local working tree. If `--fix`
   was given and `git rev-parse HEAD` differs from `headRefOid`, stop and
   tell the user to push (or pull) first so the two match.
4. **Call the skill.** Print one line naming the PR (`url`, base
   `baseRefName`), then invoke the `Skill` tool with
   `skill: "code-review"` and `args` set to `<PR number>`, followed by the
   level (only if one was given — otherwise omit it so `/code-review`
   keeps its own default, the level you used last) and the flags, e.g.
   `"63"`, `"63 max --fix"`, `"63 ultra --post"`.

## Notes

- This only pins the *target*. To narrow scope to a specific module or
  path, call `/code-review <level> <path>` directly — a path target
  replaces the PR target, it doesn't combine with it.
- Cost and recall depend on the level, exactly as for `/code-review`;
  this wrapper adds nothing on top.
