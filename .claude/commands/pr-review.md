---
description: Run the built-in /code-review scoped to this branch's diff against its base branch — avoids the bare /code-review default, which reviews only unpushed commits (empty once you've pushed).
argument-hint: "[low|medium|high|xhigh|max|ultra] [--fix] [--comment]"
allowed-tools:
  - Bash
  - Skill
---

# /pr-review — code review scoped to the current PR's diff

## Why this exists

The built-in `/code-review` with no target defaults to
`git diff @{upstream}...HEAD` (falling back to `main...HEAD` / `HEAD~1`
only when there's no upstream). Once a branch is fully pushed, that range
is **empty** — the review silently covers nothing (or falls through to
whatever is in the working tree), not the PR's actual change set. Passing
a branch name as the target fixes this: it reviews the current branch's
diff against that branch, which is the same diff GitHub shows for the PR.

## Steps

1. **Resolve the base branch.**
   ```bash
   git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'
   ```
   If that fails (no `origin/HEAD`), fall back to `main`.
2. **Resolve the level.** Take the first word of `$ARGUMENTS` if it's one
   of `low`, `medium`, `high`, `xhigh`, `max`, `ultra`; otherwise default
   to `high`. Keep any remaining words (`--fix`, `--comment`) — do not
   drop them.
3. **Call the skill.** Invoke the `Skill` tool with `skill: "code-review"`
   and `args` set to `<level> <base-branch>`, followed by any remaining
   flags from step 2, e.g. `"high main --fix"`.

## Notes

- This only pins the *target*. If you also want to narrow scope to a
  specific module or path (cheaper, fewer finder subagents), call
  `/code-review <level> <path>` directly instead of this wrapper — a path
  target replaces the branch target, it doesn't combine with it.
- Prefer running this right after `/clear` or in a fresh session: the
  review forks the current conversation context, so a long session makes
  it more expensive.
