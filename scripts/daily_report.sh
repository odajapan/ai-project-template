#!/usr/bin/env bash

set -euo pipefail

## Standalone entry point for the daily Jira report (the same command the
## /daily-report skill runs). Lists the tickets completed on the target day
## (default: today) under this repo's Epic.
##
## Usage:
##   scripts/daily_report.sh                    # today
##   scripts/daily_report.sh --date 2026-06-25
##
## All arguments are forwarded to scripts/daily_report.py.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR%/scripts}"

## daily_report.py resolves the repo -> Epic mapping from the cwd, so pin it
## to this repo regardless of where the wrapper was invoked from.
cd "$PROJECT_ROOT"

## Load Jira credentials (JIRA_BASE_URL etc.) if the env file exists.
## daily_report.py fails fast with a clear message when they are missing,
## so a missing file is not fatal here.
if [ -f "$HOME/.config/jira/env" ]; then
  # set -a: export everything the env file assigns, so plain VAR=... lines
  # (no `export`) still reach the python child process via os.environ.
  set -a
  # shellcheck disable=SC1091
  source "$HOME/.config/jira/env"
  set +a
fi

python scripts/daily_report.py "$@"
