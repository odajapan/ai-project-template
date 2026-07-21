#!/usr/bin/env python3
"""List the Jira tickets completed today under this repo's Epic.

Backs the ``/daily-report`` skill. Output is intentionally minimal: for each
ticket resolved on the target day (default: today), print its key + title and
its browse URL -- nothing else (no narrative, no file writing).

"Completed" means the issue's ``resolutiondate`` falls on the target calendar
day in the operator's local timezone. JQL date filters run in Jira's own
timezone, so we over-fetch a ±1-day window and narrow client-side.

Run from the repo root with ~/.config/jira/env sourced:

    python scripts/daily_report.py            # today
    python scripts/daily_report.py --date 2026-06-25
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

# Reuse the JiraClient + repo->Epic mapping from the task tool.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from jira_task import (
    JiraClient,
    load_config,
    repo_name,
    search_jql_all,
)


def _parse_ts(value: str | None) -> datetime | None:
    """Parse Jira's ISO timestamp to an aware datetime (None if unparseable)."""

    if not value:
        return None
    # Jira emits a no-colon UTC offset (e.g. ...-0700); normalize for fromisoformat.
    if len(value) >= 5 and value[-5] in "+-" and value[-3] != ":":
        value = value[:-2] + ":" + value[-2:]
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def completed_issues(jira: JiraClient, epic: str, target_dt: date) -> list[dict]:
    """Return issues under *epic* resolved on *target_dt* (operator-local day)."""

    local_tz = datetime.now().astimezone().tzinfo
    start_utc = (
        datetime.combine(target_dt, datetime.min.time())
        .replace(tzinfo=local_tz)
        .astimezone(UTC)
    )
    end_utc = start_utc + timedelta(days=1)

    jql_lo = (target_dt - timedelta(days=1)).isoformat()
    jql_hi = (target_dt + timedelta(days=2)).isoformat()
    jql = (
        f'project = "{jira.project_key}" AND parent = "{epic}" '
        f'AND resolutiondate >= "{jql_lo}" AND resolutiondate < "{jql_hi}" '
        f"ORDER BY resolutiondate"
    )
    # Paginate so a day with many resolved tickets isn't silently truncated.
    # Token-based via search_jql_all: /search/jql ignores startAt.
    candidates = search_jql_all(jira, jql, fields="summary,resolutiondate")

    out = []
    for issue in candidates:
        ts = _parse_ts(issue["fields"].get("resolutiondate"))
        if ts is not None and start_utc <= ts.astimezone(UTC) < end_utc:
            out.append(issue)
    return out


def render(jira: JiraClient, target: str, issues: list[dict]) -> str:
    lines = [f"Completed tickets ({target}):", ""]
    if not issues:
        lines.append("(no tickets were completed on this day)")
        return "\n".join(lines) + "\n"
    for issue in issues:
        lines.append(f"{issue['key']}  {issue['fields']['summary']}")
        lines.append(jira.browse_url(issue["key"]))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=None, help="Target day (YYYY-MM-DD).")
    args = parser.parse_args(argv)

    target = args.date or date.today().isoformat()
    try:
        target_dt = date.fromisoformat(target)
    except (TypeError, ValueError):
        sys.exit(f"Invalid --date: {target!r}. Expected ISO YYYY-MM-DD.")

    jira = JiraClient()
    entry = load_config().get("repos", {}).get(repo_name())
    if not entry or not entry.get("epic"):
        sys.exit("Repo is not initialized. Run scripts/jira_task.py init first.")

    issues = completed_issues(jira, entry["epic"], target_dt)
    print(render(jira, target, issues))
    return 0


if __name__ == "__main__":  # pragma: no cover - manual script entry point
    raise SystemExit(main())
