---
description: Show the commands to spin up an isolated git worktree for a Claude task.
argument-hint: <task-name-kebab-case>
allowed-tools:
  - Bash
---

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
git worktree add "../${REPO_NAME}-${TASK_NAME}" -b "claude/${TASK_NAME}" origin/main

# Then in another terminal:
cd "../${REPO_NAME}-${TASK_NAME}"
claude --dangerously-skip-permissions
```

Then briefly explain (1–2 lines) why this is useful:

- The autonomous run is isolated from the user's main checkout.
- The user can keep editing the main worktree while Claude works.
- Removing the worktree afterward: `git worktree remove <path>`.
