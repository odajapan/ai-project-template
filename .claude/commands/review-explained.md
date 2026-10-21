---
description: Run the code-review skill with the same arguments, then always follow it with a per-finding explanation (problem / what can break / fix / assessment) and a must-fix / optional / no-action triage, written in the user's language.
argument-hint: "[<PR#> | <branch> | <path>] [low|medium|high|xhigh|max] [--fix] [--comment]  (empty = working-tree diff; ultra / --post not supported)"
allowed-tools:
  - Skill
  - Bash
  - Read
  - Grep
  - Glob
  - Edit
  - Write
---

# /review-explained — code-review + explanation

When a user runs the built-in `/code-review` directly, the findings (English
JSON) are printed and the turn ends — Claude gets no turn to explain them.
This command has **Claude** invoke the `code-review` skill via the `Skill`
tool, then continue with an explanation right after the review output.

Not named `/review`: that is a bundled alias of `/code-review` and would
shadow a project command of the same name.

## Language

Write the explanation in the user's language: the language set in
CLAUDE.md or memory if there is one, otherwise the language of the
conversation. Keep code identifiers, file paths, and the skill's raw output
as-is.

## Steps

1. Invoke `code-review` with the `Skill` tool, passing the received
   arguments (`$ARGUMENTS`) unchanged as `args`. Target, depth, and
   `--fix` / `--comment` mean the same as in `/code-review`. `ultra` (runs
   in the cloud, so results do not come back synchronously) and `--post`
   are not supported: if given, tell the user to run
   `/code-review <args>` directly and stop.
2. Let the skill's output follow the skill's own contract (loaded inline,
   Claude acts as the reviewer and emits JSON or reports via
   `ReportFindings`; run as a fork, the result is returned). **Do not
   paste that output a second time.** Exception: if the findings are not
   yet visible to the user (a fork result that arrived only as a tool
   result), paste the JSON block once, verbatim, before explaining.
3. Then write the explanation. **Keep the skill's numbering order** (do not
   re-sort; severity is conveyed by the assessment). If there are no
   findings, say so and list in 2–3 lines what the reviewer checked.

   ```
   N. **<file> <line>: <the problem in one sentence>**
      What can break: <summary of failure_scenario — which input/state breaks what>
      Fix: <the fix from summary / failure_scenario; if none, label it as your own proposal>
      Assessment: real bug / design decision / cleanup (minor) + one remark
   ```

   When `category` / `verdict` are present: `verdict=CONFIRMED` and
   `correctness`-type categories are normally "real bug", `PLAUSIBLE`
   leans "design decision", and `simplification` / `efficiency` /
   `test-coverage` are "cleanup". When unsure, add a one-line reason.

4. Finish by triaging **by number** into must-fix / optional /
   no action (with reason). If anything should be fixed, add one line with
   a proposed branch name (`claude/<task>`). Note findings that are
   already merged or handled in another PR.
5. Keep it concise (3–4 lines per finding). Do not write code. If the
   reviewed change is your own previous change, say so with reasons when
   you disagree with a finding.

## Don't

- Modify files unless `--fix` was given (leave `--fix` edits to the skill).
- Omit or paraphrase findings — the explanation is an **addition**, not a
  replacement.
- Post PR comments unless `--comment` was given (leave it to the skill).
