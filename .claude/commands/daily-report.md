---
description: List Jira tickets completed today (or on a given date) under this repo's Epic.
argument-hint: "[--date YYYY-MM-DD]"
allowed-tools:
  - Bash
common_files:
  - docs/JIRA_GITHUB_WORKFLOW.md
  - scripts/daily_report.py
suggested_sequence:
  - run scripts/daily_report.sh with $ARGUMENTS
  - paste stdout verbatim in a fenced code block
---

# /daily-report — list today's completed Jira tickets

Requires the Jira toolkit to be set up for this repo — see
[docs/JIRA_GITHUB_WORKFLOW.md](../../docs/JIRA_GITHUB_WORKFLOW.md). If
`~/.config/jira/env` isn't sourced or `scripts/jira_task.py init` hasn't
been run, the script will say so; report that message as-is rather than
guessing at setup steps.

Run:

```bash
scripts/daily_report.sh $ARGUMENTS
```

`$ARGUMENTS` is forwarded as-is (only `--date YYYY-MM-DD` is supported;
default is today).

Paste the script's stdout verbatim in a fenced code block. Do not
summarize, narrate, or add commentary — the script's output already is
the intended reply.
