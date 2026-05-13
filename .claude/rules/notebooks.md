---
paths:
  - "notebooks/**/*.ipynb"
---

# Notebook conventions

## Why this matters

Notebooks accumulate state (cell outputs, embedded images, base64 blobs)
that bloats diffs and can leak data into source control. `nbstripout`
runs as a pre-commit hook, but rules at edit time prevent the noise
from being created in the first place.

## Rules

- **No output in commits.** Strip outputs before staging. The pre-commit
  hook does this automatically; run
  `jupyter nbconvert --clear-output --inplace <notebook>` if editing
  outside the hook.
- **No bulky data inline.** Do not embed CSV / JSON / image blobs that
  exceed a few KB inside cells. Load from `data/` instead.
- **No secrets.** Never paste API keys, tokens, or DB connection strings
  into notebook cells. Pull from environment variables (see
  `.claude/rules/secrets.md`).
- **Exploration only.** Production logic belongs in `src/`. If a
  notebook cell grows into reusable code, port it to a module and
  import it back.
- **Naming.** `<order>-<initials>-<description>.ipynb`
  (for example, `01-ho-initial-exploration.ipynb`).

## When in doubt

If a cell would be hard for a reviewer to read in a diff, it probably
should not be there.
