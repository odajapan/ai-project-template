---
description: Review this branch's open PR with the built-in /code-review (by PR number), fix the obvious findings, and re-review in a bounded loop; findings that need a human decision are explained and left to the user.
argument-hint: "[low|medium|high|xhigh|max|ultra] [--no-fix] [--comment] [--max-findings <n>] [--post|--no-post]"
allowed-tools:
  - Skill
  - Bash
  - Read
  - Grep
  - Glob
  - Edit
  - Write
---

# /pr-review — review the current PR, fix the obvious, re-review

## Why this exists

The built-in `/code-review` with no target defaults to
`git diff @{upstream}...HEAD` (falling back to `main...HEAD` / `HEAD~1`
only when there's no upstream). Once a branch is fully pushed, that range
is **empty** — the review silently covers nothing (or falls through to
whatever is in the working tree), not the PR's actual change set. Passing
the PR number as the target fixes this: `/code-review` then reviews the
PR's own diff against its real base, and `--comment` / `ultra` have a PR
to work with.

On top of that, a bare `/code-review` ends the turn with raw findings.
This command keeps the turn: it fixes what has one obvious fix, re-reviews
the whole PR, and stops with an explained list of what is left for the
user to decide.

## Modes

- **Default — fix loop.** Review → fix the obvious findings → commit →
  re-review, at most **3 reviews** in total, then push once.
  **Autonomous runs** (`--dangerously-skip-permissions` or unattended)
  never use it — CLAUDE.md says they open the PR and stop — so they run
  as `--no-fix`, reject `--comment` / `--post` (no outward-facing posts
  without a human), and say so in one line.
- **`--no-fix` — review only.** One review, then the triage (step 5)
  and the report (step 7). Nothing is edited, committed, or pushed.
- **`ultra`** implies `--no-fix`: it runs in the cloud and returns its
  findings later, so there is nothing to loop on.

## Steps

1. **Resolve the PR.**
   ```bash
   gh pr view --json number,state,baseRefName,headRefName,headRefOid,isCrossRepository,url
   ```
   If this fails (no PR for the current branch, or `gh` not
   authenticated), **stop** and tell the user: push the branch and open a
   PR first, or run `/code-review <level> <path>` directly for a pre-PR
   review. Do not guess a base branch. If `state` is not `OPEN`, stop and
   say so — do not review a stale diff.
2. **Parse `$ARGUMENTS`.**
   - At most one level: `low`, `medium`, `high`, `xhigh`, `max`, `ultra`
     (case-insensitive; forward it lowercased).
   - `--no-fix` selects review-only mode. `--fix` is accepted as a no-op
     (fixing is the default) — say so in one line. `--fix` together with
     `--no-fix` is rejected as contradictory, and so is `ultra` with
     `--fix`: the cloud review returns its findings later, so there is
     nothing to fix in this turn.
   - `--max-findings` takes the next word as its value, which must be a
     positive integer, `all`, or `default` — if it is missing or anything
     else, stop and say so. It is forwarded on every review round.
   - `--comment` is allowed only with `--no-fix` or `ultra` (in the loop,
     comments would describe findings that are about to be fixed).
     `--post` / `--no-post` are allowed only with `ultra`. Otherwise stop
     and say which combination was rejected.
   - Any other `--` flag is forwarded as-is. Any other word (a path, a PR
     number, a second level) means the user wanted a custom target: stop
     and tell them to call `/code-review` directly.
3. **Check the local tree.** Reviews read the PR as pushed to GitHub.
   - Review-only mode: if `git rev-parse HEAD` differs from `headRefOid`,
     continue but warn in one line that the pushed version is reviewed
     and local-only commits are not covered.
   - Fix loop: **stop** unless all of these hold — `isCrossRepository` is
     false (fix commits are pushed to `origin`); the current branch is
     `headRefName` and is not `main` / `master`; `git rev-parse HEAD`
     equals `headRefOid` (push or pull first); `git status --porcelain` is
     empty (commit or stash first, so fixes never mix with unrelated
     work).
4. **Review round 1.** Print one line naming the PR (`url`, base
   `baseRefName`), then invoke the `Skill` tool with
   `skill: "code-review"` and `args` set to `<PR number>`, followed by the
   level (only if one was given — otherwise omit it so `/code-review`
   keeps its own default, the level used last) and the forwarded flags,
   e.g. `"63"`, `"63 max"`, `"63 ultra --post"`. Do not pass `--fix` to the
   skill — this command decides what gets fixed. Each `code-review` call
   is one round: its own output contract (a findings block, or
   `ReportFindings`) closes that round, not this command — keep going
   with the next step. With `ultra`, go
   straight to step 7. In review-only mode, triage (step 5), then go to
   step 7.
5. **Triage every finding** of the round into exactly one bucket. Read the
   cited code first; do not trust the finding's line numbers blindly.
   - **Fix** — all of: you agree the problem is real; there is one
     obvious fix that a reviewer would not argue with; it stays within the
     PR's declared intent and touches only files the PR already changes
     (or their tests); it changes no public interface (CLI flags, function
     signatures, schemas, config keys, file formats) beyond what the PR
     already changes.
   - **Ask the user** — anything else that is real: several reasonable
     fixes, a behavior or API change, a trade-off (security, cost,
     performance vs. simplicity), a fix outside the PR's scope, anything
     touching a path `AGENTS.md` forbids or protects (`data/raw/`,
     `models/`, `.env*`, `secrets/`), or a finding that contradicts
     the PR's stated design.
   - **No action** — you can show it is not a problem (quote the guard or
     the code that refutes it), or it is pure style the project does not
     enforce. Give the reason.
   When unsure between Fix and Ask, choose Ask.
6. **Fix and re-review** (fix loop only).
   1. If the Fix bucket is empty, go to 6.8.
   2. If this was review round 3, do **not** fix — unreviewed fixes would
      be pushed. Move the Fix items to the report as "fixable, not
      applied (round limit)" and go to 6.8.
   3. If a Fix item repeats a finding already fixed in an earlier round
      (the same problem in the same function or section — match on the
      problem, not the line number, since fixes shift lines), the fix did
      not hold: move it to Ask the user and do not fix it again.
   4. Apply the remaining Fix items. If the fixes so far, measured from
      the original head (`git diff --stat <headRefOid>`, step 1's value,
      not the moving PR), exceed 3 files or 500 lines, stop before
      running `make check`: this round's edits stay uncommitted, and
      6.8 still pushes the earlier rounds' commits.
   5. Run `make check`. If it fails and two diagnostic attempts do not
      make it pass, stop the same way, and step 7 reports the failure
      output.
   6. Stage only the files you changed and commit one Conventional Commit
      per round, e.g. `fix: address review findings (round 1)`, listing
      the fixed findings in the body.
   7. Re-review: re-run step 1's `gh pr view`; if the PR is no longer
      `OPEN`, `baseRefName` changed, or `headRefOid` moved (someone else
      pushed), stop, do not push, and report. Then
      `git fetch origin <baseRefName>` and invoke `code-review` with
      `args` = `origin/<baseRefName>...HEAD` plus the same level and
      forwarded flags. The PR number cannot be used here — it reads the
      pushed state, and the fix commits are local until 6.8. This is a
      full review of the PR as it now stands, not just the fixes. Return
      to step 5 with this round's findings.
   8. If there is at least one fix commit, push once with
      `git push origin <headRefName>` (never force). Every commit was
      green in `make check` and re-reviewed by the following round; a
      stop at 6.4 / 6.5 leaves only that round's edits uncommitted. Do
      not push after a stop at 6.7. If the push is rejected, stop and
      report — never force. Then go to step 7.
7. **Report**, in the user's language (from CLAUDE.md or memory if set,
   otherwise the conversation's language; keep identifiers, paths, and
   the skill's raw output as-is). Do not paste the skill's output a second
   time; if a round's findings arrived only as a tool result the user
   cannot see, paste them once, verbatim. Then:
   - **Rounds**: one line per round — number of findings and how many
     were fixed / asked / no action; the fix commit SHA.
   - **Fixed**: one line per finding.
   - **Fixable, not applied**: Fix-bucket items in review-only mode or
     after the round limit, one line each with the intended fix.
   - **Needs your decision**: for each, number it `R<round>-<n>` (the
     review's own number within that round, so items from different
     rounds never collide) and write
     ```
     R<round>-<n>. **<file> <line>: <the problem in one sentence>**
        What can break: <which input/state breaks what>
        Options: <the reasonable fixes, with trade-offs>
        Recommendation: <yours, with one reason>
     ```
   - **No action**: one line each with the reason.
   - **Why it stopped**: no findings left / only decisions left / round
     limit / repeated finding / `make check` failure / scope limit / PR
     changed on GitHub / push rejected.
   - **Pushed**: the new head SHA, or "nothing pushed" with the reason.
     PR CI reruns on the push; `/pr-review` does not wait for it.
   - **Left local** (whenever anything is): the unpushed commits
     (`git log --oneline origin/<headRefName>..HEAD`) and the uncommitted
     files (`git status --short`), with the choices — keep and commit
     the edits, or discard them (`git restore`) — and that the next
     `/pr-review` refuses to run until the tree is clean and pushed.
   With `ultra`, report only that the cloud review was launched and its
   findings arrive later — never "no findings". Otherwise, if there were
   no findings at all, say so and list in 2–3 lines what the reviewer
   checked.

## Notes

- This only pins the *target*. To narrow scope to a specific module or
  path, call `/code-review <level> <path>` directly.
- Every round costs a full review at the chosen level, so the default
  loop can cost up to three reviews. Use `--no-fix` when you only want
  the findings.
- Never merge — merging stays with `/land` and a human.
