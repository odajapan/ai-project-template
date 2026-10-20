---
name: "source-command-worktree"
description: "Show the commands to spin up an isolated git worktree for a Codex task."
---

# source-command-worktree

Use this skill when the user asks to run the migrated source command `worktree`.
`$ARGUMENTS` below stands for the argument the user gave with the request.

## Command Template

# /worktree — isolated workspace for an autonomous run

Print the commands the user should run to create a sibling worktree.
Do **not** execute them — worktree creation is a host-side step that
affects the user's filesystem outside this repo.

Use `$ARGUMENTS` as the task name. Convert to kebab-case if needed.

Print exactly this block, with placeholders filled in:

```bash
# From the repo root:
REPO_NAME=$(basename "$PWD")
TASK_NAME="$ARGUMENTS"

git fetch origin --prune
git worktree add "../${REPO_NAME}-${TASK_NAME}" -b "codex/${TASK_NAME}" origin/main

# Then in another terminal:
cd "../${REPO_NAME}-${TASK_NAME}"
codex --sandbox workspace-write --ask-for-approval never
```

Then briefly explain (1–2 lines) why this is useful:

- The autonomous run is isolated from the user's main checkout.
- The user can keep editing the main worktree while Codex works.
- Removing the worktree afterward: `git worktree remove <path>`.
