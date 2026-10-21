---
name: "source-command-land"
description: "Merge PR(s), retarget stacked children, sync main, and clean up."
---

<!-- ported-from: .claude/commands/land.md sha256:ce8cf9a3ac6f -->

# source-command-land

Use this skill when the user asks to run the migrated source command `land`.

## Command Template

# /land — merge a PR and tidy up

Run when a human has decided a PR is ready to merge. Codex performs the
full landing sequence so nobody hand-pastes `gh`/`git` commands.

Only use interactively. **Autonomous runs
(`--dangerously-bypass-approvals-and-sandbox`, `codex exec`) must never merge** — open the PR and
stop. See `AGENTS.md` → Branch, commit & PR workflow.

## Arguments

- No args → the PR for the current branch (`gh pr view --json number`).
- One or more PR numbers → land each, in the given order.
- A phrase like "all dependabot" → resolve with
  `gh pr list --author app/dependabot --json number`.

## Steps (per PR)

1. **Verify it's mergeable and green.** `gh pr checks <n>` — if any
   required check is failing or pending, stop and report; do not merge a
   red or in-flight PR. `gh pr view <n> --json mergeStateStatus` should be
   `CLEAN` (retry once after a short wait if `UNKNOWN` — GitHub is still
   recomputing after a prior merge).
2. **Retarget stacked children first.** `gh pr list --base <branch>
--json number` — any open PR based on this branch would be
   auto-closed when the branch is deleted. Retarget each to main:
   `gh pr edit <child> --base main`.
3. **Merge and delete the branch.** `gh pr merge <n> --merge
--delete-branch`.
4. **Sync local main.** `git checkout main && git pull --ff-only origin
main`.
5. **Prune local state.** Delete the merged local branch
   (`git branch -d <branch>`), then `git worktree prune`.

## After all PRs

6. **Clean stale worktrees.** Candidates are worktrees under
   `.claude/worktrees/` and sibling `../<repo>-<task>` worktrees on a
   `codex/*` branch (what `source-command-worktree` creates). Never touch
   the current worktree (`git rev-parse --show-toplevel`) or any other
   worktree. Remove a candidate whose branch is merged into main, or that
   is detached, with `git worktree remove <path>` — add `--force` only for
   `.claude/worktrees/`. If a candidate looks active (unmerged branch,
   uncommitted work), **list it and stop** rather than removing it.
7. **Suggest a fresh session.** Propose to start a fresh session with a
   one-line handoff — only once the PR is merged and follow-through is done, nothing is still running, the tree
   is clean, and anything worth keeping is in the PR body or `AGENTS.md`.

If any step blocks and the cause is non-obvious, stop and report before
guessing. Never use `gh pr merge` outside this human-initiated flow.
