---
paths:
  - "data/raw/**"
---

# data/raw is immutable

## Why this matters

`data/raw/` holds original, externally-sourced inputs. They are the ground
truth that every downstream stage is reproducible from. Mutating them
silently breaks lineage and can corrupt experiments that are days old.

## Rules

- **Read only.** Do not write to, edit, move, rename, or delete any file
  under `data/raw/`.
- If a raw file is wrong (encoding, schema), copy it to `data/interim/`
  and fix the copy. The original stays untouched.
- Do not run shell commands that could alter the directory
  (`rm`, `mv`, `find ... -delete`, `git rm`, in-place `sed -i`).
- When a transformation needs to drop or fix records, do it in code that
  reads from `data/raw/` and writes elsewhere — keep the lineage
  reproducible from the originals.

## When in doubt

Stop and ask the human. Recovering deleted raw data is often impossible.
