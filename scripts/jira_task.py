#!/usr/bin/env python3
"""Manage Jira issues and branches for this repo (and others, once initialized).

This is a single-developer tool to link a git branch one-to-one with a Jira
issue. The current working directory's repo is mapped to a Jira Epic, and new
issues are created as children of that Epic. The script handles the boring
parts: creating the issue, transitioning it to "In Progress", branching off
the configured base branch, and posting a comment on the issue with the new
branch name.

Nothing here is tied to a specific Jira project, workflow, or organization:
status transitions are resolved by **name** (not hard-coded numeric IDs) via
the Jira REST API, and every other org-specific knob (project key, base
branch, branch prefix, status names) lives in the per-repo config described
below.

Subcommands::

    init "Epic Title"     Create a Jira Epic for the current repo and remember it
    new  "Summary"        Create a Task under the repo's Epic + branch
    start JB-NNN          Start work on an existing issue: branch + transition
    pr                    Push branch, create PR, link to Jira, transition to Review
    done                  Verify PR merged, transition issue to Done
    describe JB-NNN       Replace an issue's description
    link-pr               Standalone Remote Link upsert (backfilling)
    status                Show Jira info for the current branch's issue

Required environment variables (sourced from ~/.config/jira/env)::

    JIRA_BASE_URL          e.g. https://<your-domain>.atlassian.net
    JIRA_EMAIL             Atlassian account email
    JIRA_API_TOKEN         API token from id.atlassian.com
    JIRA_PROJECT_KEY       e.g. <YOUR_PROJECT_KEY>

Configuration file (auto-managed, one entry per repo)::

    ~/.config/jira/repo-epic-map.yaml

    repos:
      <repo-dir-name>:
        epic: ABC-123
        base_branch: main          # default: main
        branch_prefix: feature     # default: feature -> feature/ABC-123-slug
        default_labels: [some-label]
        statuses:                  # target status NAMES resolved at runtime
          in_progress: In Progress # default: In Progress
          review: In Review        # default: In Review
          done: Done                # default: Done
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import requests
import yaml
from requests.auth import HTTPBasicAuth

CONFIG_PATH = Path.home() / ".config" / "jira" / "repo-epic-map.yaml"

DEFAULT_STATUSES = {
    "in_progress": "In Progress",
    "review": "In Review",
    "done": "Done",
}

REQUIRED_ENV = ("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY")


# ---------------------------------------------------------------------------
# ADF helpers
# ---------------------------------------------------------------------------


def _plaintext_to_adf(text: str) -> dict:
    """Convert a plain-text string to an ADF (Atlassian Document Format) doc.

    Paragraphs are split on blank lines. Within a paragraph, single newlines
    become hard breaks. No Markdown is interpreted -- keep descriptions in
    prose; rich formatting can be added later via the Jira UI if needed.
    """

    paragraphs = [p for p in text.split("\n\n") if p.strip()]

    def _paragraph_node(p: str) -> dict:
        lines = p.split("\n")
        content: list[dict] = []
        for i, line in enumerate(lines):
            if i:
                content.append({"type": "hardBreak"})
            content.append({"type": "text", "text": line})
        return {"type": "paragraph", "content": content}

    return {
        "type": "doc",
        "version": 1,
        "content": [_paragraph_node(p) for p in paragraphs],
    }


def _read_text_file_or_die(path: str, label: str) -> str:
    """Read a UTF-8 file, exiting with a friendly message on common errors."""

    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        sys.exit(f"{label} not found: {path}")
    except PermissionError as exc:
        sys.exit(f"{label} not readable ({path}): {exc}")


def _read_description(args: argparse.Namespace) -> str | None:
    """Resolve the description from one of three CLI sources, in priority order.

    1. ``--description "..."`` inline string
    2. ``--description-file path`` reads the file
    3. ``--description-stdin`` reads from stdin (handy for piping in)
    """

    if getattr(args, "description", None):
        return str(args.description)
    path = getattr(args, "description_file", None)
    if path:
        return _read_text_file_or_die(path, "description file")
    if getattr(args, "description_stdin", False):
        return sys.stdin.read()
    return None


# ---------------------------------------------------------------------------
# Jira client
# ---------------------------------------------------------------------------


class JiraClient:
    """Thin wrapper around the Jira Cloud REST API for the operations we need."""

    def __init__(self) -> None:
        missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
        if missing:
            sys.exit(
                "Missing required env vars: "
                f"{', '.join(missing)}. "
                "Source ~/.config/jira/env in your shell first."
            )
        self.base_url = os.environ["JIRA_BASE_URL"].rstrip("/")
        self.auth = HTTPBasicAuth(
            os.environ["JIRA_EMAIL"], os.environ["JIRA_API_TOKEN"]
        )
        self.project_key = os.environ["JIRA_PROJECT_KEY"]
        self._account_id: str | None = None

    def _request(self, method: str, path: str, **kwargs: Any) -> dict:
        url = f"{self.base_url}{path}"
        headers = {"Accept": "application/json"}
        if "json" in kwargs:
            headers["Content-Type"] = "application/json"
        try:
            resp = requests.request(
                method, url, auth=self.auth, headers=headers, timeout=30, **kwargs
            )
        except requests.RequestException as exc:
            sys.exit(f"Jira API request failed: {method} {path}\n{exc}")
        if not resp.ok:
            sys.exit(
                f"Jira API error: {method} {path} -> HTTP {resp.status_code}\n"
                f"{resp.text}"
            )
        if not resp.text:
            return {}
        try:
            return dict(resp.json())
        except ValueError:
            sys.exit(
                f"Jira API returned non-JSON response: {method} {path}\n"
                f"{resp.text[:500]}"
            )

    @property
    def my_account_id(self) -> str:
        if self._account_id is None:
            data = self._request("GET", "/rest/api/3/myself")
            self._account_id = data["accountId"]
        return self._account_id

    def create_issue(
        self,
        summary: str,
        issue_type: str = "Task",
        parent_key: str | None = None,
        labels: list[str] | None = None,
        assignee_account_id: str | None = None,
        description: str | None = None,
    ) -> dict:
        fields: dict[str, Any] = {
            "project": {"key": self.project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
        }
        if parent_key:
            fields["parent"] = {"key": parent_key}
        if labels:
            fields["labels"] = labels
        if assignee_account_id:
            fields["assignee"] = {"accountId": assignee_account_id}
        if description:
            fields["description"] = _plaintext_to_adf(description)
        return self._request("POST", "/rest/api/3/issue", json={"fields": fields})

    def set_description(self, issue_key: str, description: str) -> None:
        self._request(
            "PUT",
            f"/rest/api/3/issue/{issue_key}",
            json={"fields": {"description": _plaintext_to_adf(description)}},
        )

    def upsert_remote_link(
        self,
        issue_key: str,
        url: str,
        title: str,
        summary: str | None = None,
        global_id: str | None = None,
        resolved: bool = False,
    ) -> dict:
        """Create or update a Web/Remote link on the issue.

        ``global_id`` makes the call idempotent: re-running with the same
        global_id updates the existing link instead of duplicating it.
        """

        payload: dict[str, Any] = {
            "object": {
                "url": url,
                "title": title,
                "icon": {
                    "url16x16": "https://github.githubassets.com/favicons/favicon.png",
                    "title": "GitHub",
                },
                "status": {"resolved": resolved},
            },
            "relationship": "is implemented by",
        }
        if summary:
            payload["object"]["summary"] = summary
        if global_id:
            payload["globalId"] = global_id
        return self._request(
            "POST", f"/rest/api/3/issue/{issue_key}/remotelink", json=payload
        )

    def available_transitions(self, issue_key: str) -> list[dict]:
        data = self._request("GET", f"/rest/api/3/issue/{issue_key}/transitions")
        return list(data.get("transitions", []))

    def transition_by_name(self, issue_key: str, target_status: str) -> None:
        """Transition ``issue_key`` to the transition whose target status name
        matches ``target_status`` (case-insensitive).

        Numeric transition IDs are workflow-specific (they differ per Jira
        project), so we resolve the id at call time from the issue's own
        transition list instead of hard-coding it. Exits with a clear error
        (listing what *is* available) if no transition leads to that status.
        """

        transitions = self.available_transitions(issue_key)
        for t in transitions:
            if t.get("to", {}).get("name", "").casefold() == target_status.casefold():
                self._request(
                    "POST",
                    f"/rest/api/3/issue/{issue_key}/transitions",
                    json={"transition": {"id": t["id"]}},
                )
                return
        available = ", ".join(
            sorted({t.get("to", {}).get("name", "?") for t in transitions})
        )
        sys.exit(
            f"No transition to status {target_status!r} is available for "
            f"{issue_key}. Available target statuses: {available or '(none)'}.\n"
            "Check the 'statuses' mapping in "
            f"{CONFIG_PATH} against this project's actual workflow."
        )

    def add_comment(self, issue_key: str, body: str) -> None:
        # Atlassian Document Format (ADF), minimal single paragraph.
        adf = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": body}],
                }
            ],
        }
        self._request(
            "POST",
            f"/rest/api/3/issue/{issue_key}/comment",
            json={"body": adf},
        )

    def get_issue(self, issue_key: str) -> dict:
        return self._request(
            "GET",
            f"/rest/api/3/issue/{issue_key}",
            params={"fields": "summary,status,assignee,parent,labels,issuetype"},
        )

    def browse_url(self, issue_key: str) -> str:
        return f"{self.base_url}/browse/{issue_key}"


# ---------------------------------------------------------------------------
# Repo / branch helpers
# ---------------------------------------------------------------------------


def _run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=check)


def repo_root() -> Path:
    try:
        out = _run_git("rev-parse", "--show-toplevel").stdout.strip()
    except subprocess.CalledProcessError:
        sys.exit("Not inside a git repository.")
    return Path(out)


def repo_name() -> str:
    return repo_root().name


def current_branch() -> str:
    return _run_git("branch", "--show-current").stdout.strip()


def issue_key_from_branch(branch: str) -> str | None:
    """Extract a Jira issue key (e.g. ``ABC-123``) embedded in the branch name."""

    match = re.search(r"([A-Z][A-Z0-9]+-\d+)", branch)
    return match.group(1) if match else None


def slugify(text: str, max_len: int = 40) -> str:
    """Turn an arbitrary summary into a branch-name-safe slug."""

    s = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().lower()
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s[:max_len].strip("-") or "task"


# ---------------------------------------------------------------------------
# Config persistence
# ---------------------------------------------------------------------------


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {"repos": {}}
    try:
        data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        sys.exit(f"Invalid YAML in {CONFIG_PATH}: {exc}")
    if not isinstance(data, dict):
        return {"repos": {}}
    if not isinstance(data.get("repos"), dict):
        data["repos"] = {}
    return data


def save_config(config: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    os.chmod(CONFIG_PATH, 0o600)


def repo_config_or_die() -> dict:
    cfg = load_config()
    repo = repo_name()
    entry = cfg.get("repos", {}).get(repo)
    if not entry:
        sys.exit(
            f"Repo '{repo}' is not initialized.\n"
            f'Run: scripts/jira_task.py init "<Epic Title>"'
        )
    if not isinstance(entry, dict):
        sys.exit(
            f"Malformed config for '{repo}' in {CONFIG_PATH}: expected a dict, "
            f"got {type(entry).__name__}. Edit the file or re-run init."
        )
    epic = entry.get("epic")
    if not isinstance(epic, str) or not epic.strip():
        sys.exit(
            f"Malformed config for '{repo}' in {CONFIG_PATH}: 'epic' must be "
            f"a Jira issue key string (e.g. 'ABC-123'). Re-run init or fix the "
            f"config."
        )
    base_branch = entry.get("base_branch", "main")
    if not isinstance(base_branch, str) or not base_branch.strip():
        sys.exit(
            f"Malformed config for '{repo}' in {CONFIG_PATH}: 'base_branch' "
            "must be a non-empty string."
        )
    branch_prefix = entry.get("branch_prefix", "feature")
    if not isinstance(branch_prefix, str) or not branch_prefix.strip():
        sys.exit(
            f"Malformed config for '{repo}' in {CONFIG_PATH}: 'branch_prefix' "
            "must be a non-empty string."
        )
    labels = entry.get("default_labels", [])
    if not isinstance(labels, list) or any(not isinstance(v, str) for v in labels):
        sys.exit(
            f"Malformed config for '{repo}' in {CONFIG_PATH}: 'default_labels' "
            "must be a list of strings."
        )
    statuses = entry.get("statuses", {})
    if not isinstance(statuses, dict) or any(
        k not in DEFAULT_STATUSES or not isinstance(v, str) for k, v in statuses.items()
    ):
        sys.exit(
            f"Malformed config for '{repo}' in {CONFIG_PATH}: 'statuses' must "
            f"be a dict with a subset of keys {sorted(DEFAULT_STATUSES)}, "
            "each mapped to a status-name string."
        )
    entry = dict(entry)
    entry["base_branch"] = base_branch
    entry["branch_prefix"] = branch_prefix
    entry["statuses"] = {**DEFAULT_STATUSES, **statuses}
    return entry


# ---------------------------------------------------------------------------
# Branch creation
# ---------------------------------------------------------------------------


def _run_gh(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Wrapper for the ``gh`` CLI with stdout/stderr captured.

    With ``check=True`` (the default), a non-zero exit is converted into a
    short, traceback-free ``sys.exit`` carrying the gh stderr (or stdout
    fallback). Callers that need to inspect the failure themselves should
    pass ``check=False``.
    """

    try:
        return subprocess.run(
            ["gh", *args], capture_output=True, text=True, check=check
        )
    except subprocess.CalledProcessError as exc:
        msg = (exc.stderr or exc.stdout or "").strip()
        sys.exit(
            f"gh {' '.join(args)} failed (exit {exc.returncode})"
            + (f": {msg}" if msg else "")
        )


def _current_pr_for_branch(branch: str) -> dict | None:
    """Return ``{"number": int, "url": str, "title": str, "state": ...}`` or None.

    Uses ``gh pr view`` to find the PR for ``branch``. Returns ``None`` only
    when the gh CLI explicitly reports that no PR exists for the branch;
    any other failure (auth, network, gh not configured) is re-raised via
    ``sys.exit`` so we don't mask it as "no PR found".
    """

    proc = subprocess.run(
        [
            "gh",
            "pr",
            "view",
            branch,
            "--json",
            "number,url,title,state,mergedAt,mergeCommit",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        return json.loads(proc.stdout) if proc.stdout.strip() else None

    err = (proc.stderr or "").lower()
    if "no pull requests found" in err or "no pull request found" in err:
        return None

    sys.exit(
        f"gh pr view failed for branch {branch!r}:\n"
        f"{(proc.stderr or proc.stdout).strip()}"
    )


def _require_issue_key_from_branch() -> str:
    """Extract a Jira issue key from the current branch or die."""

    branch = current_branch()
    key = issue_key_from_branch(branch)
    if not key:
        sys.exit(f"No Jira issue key found in branch name '{branch}'.")
    return key


_VALID_REF_RE = re.compile(r"^[A-Za-z0-9._/\-]+$")


def _validate_git_ref(name: str, label: str) -> str:
    """Reject refs that could be interpreted as a git option (e.g. ``-foo``)."""

    if not name or name.startswith("-") or not _VALID_REF_RE.fullmatch(name):
        sys.exit(f"Invalid {label}: {name!r}")
    return name


def _checkout_new_branch(branch_name: str, base_branch: str) -> None:
    """Update the base branch and create ``branch_name`` off it."""

    base_branch = _validate_git_ref(base_branch, "base branch")
    branch_name = _validate_git_ref(branch_name, "branch name")

    print(f"  → git fetch origin {base_branch}")
    _run_git("fetch", "origin", base_branch)
    print(f"  → git checkout {base_branch}")
    _run_git("checkout", base_branch)
    print("  → git pull --ff-only")
    _run_git("pull", "--ff-only")
    print(f"  → git checkout -b {branch_name}")
    _run_git("checkout", "-b", branch_name)


def search_jql_all(
    jira: JiraClient,
    jql: str,
    fields: str,
    page_size: int = 50,
    max_pages: int = 100,
) -> list[dict]:
    """Fetch every page of a ``/rest/api/3/search/jql`` query.

    The enhanced-search endpoint paginates with ``nextPageToken`` and
    silently IGNORES the classic ``startAt`` parameter. Paging on
    ``startAt`` therefore refetches the same first page forever once a
    result set exceeds one page -- the absence of a ``nextPageToken`` in
    the response is the only reliable "last page" signal, so that is what
    terminates this loop.

    ``max_pages`` is a fail-fast guard against a broken upstream that
    keeps returning (or cycles) tokens: rather than looping and growing
    ``issues`` without bound, give up loudly. The default allows
    ``max_pages * page_size`` issues -- far beyond any real query here.
    """

    issues: list[dict] = []
    next_page_token: str | None = None
    for _ in range(max_pages):
        params: dict = {
            "jql": jql,
            "fields": fields,
            "maxResults": page_size,
        }
        if next_page_token:
            params["nextPageToken"] = next_page_token
        result = jira._request("GET", "/rest/api/3/search/jql", params=params)
        issues.extend(result.get("issues", []))
        next_page_token = result.get("nextPageToken")
        if not next_page_token:
            return issues
    raise RuntimeError(
        f"/search/jql pagination did not terminate within {max_pages} pages "
        f"({len(issues)} issues collected) -- nextPageToken may be cycling."
    )


def _find_open_issues_with_summary(
    jira: JiraClient, epic_key: str, summary: str
) -> list[dict]:
    """Return non-Done issues under ``epic_key`` whose summary exactly matches
    ``summary``.

    Used by :func:`cmd_new` to refuse re-creating something the operator
    probably meant to claim from an existing Backlog issue.

    JQL's ``~`` operator is a fuzzy / tokenized text match, so we use it
    as a coarse filter and then narrow to exact summary match in Python.
    Double-quotes and backslashes in ``summary`` are escaped for the JQL
    string literal.
    """

    safe_summary = summary.replace("\\", "\\\\").replace('"', '\\"')
    jql = (
        f'project = "{jira.project_key}" AND parent = "{epic_key}" '
        f'AND statusCategory != Done AND summary ~ "{safe_summary}"'
    )

    # Paginate so the dedup check doesn't silently miss matches past the
    # first page when an Epic accumulates a lot of open work. Page size
    # is generous because the JQL pre-filter is already narrow.
    all_issues = search_jql_all(jira, jql, fields="summary,status")

    return [i for i in all_issues if i["fields"]["summary"] == summary]


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------


def cmd_init(args: argparse.Namespace) -> None:
    jira = JiraClient()
    cfg = load_config()
    repo = repo_name()

    if repo in cfg.get("repos", {}):
        existing = cfg["repos"][repo]
        sys.exit(
            f"Repo '{repo}' is already mapped to Epic {existing.get('epic')}.\n"
            f"Edit {CONFIG_PATH} directly to change."
        )

    print(f"Creating Epic '{args.title}' in project {jira.project_key} ...")
    result = jira.create_issue(args.title, issue_type="Epic")
    epic_key = result["key"]
    print(f"  ✓ Epic created: {epic_key}  {jira.browse_url(epic_key)}")

    cfg.setdefault("repos", {})[repo] = {
        "epic": epic_key,
        "base_branch": args.base_branch,
        "branch_prefix": args.branch_prefix,
        "default_labels": args.labels or [],
        "statuses": dict(DEFAULT_STATUSES),
    }
    save_config(cfg)
    print(f"  ✓ Saved mapping in {CONFIG_PATH}")
    print(
        "  i Edit the 'statuses' block in that file if this Jira project's "
        "workflow uses different status names than "
        f"{DEFAULT_STATUSES}."
    )
    print('\nNext: scripts/jira_task.py new "Your task summary"')


def cmd_new(args: argparse.Namespace) -> None:
    jira = JiraClient()
    entry = repo_config_or_die()
    epic_key = entry["epic"]
    base_branch = entry["base_branch"]
    branch_prefix = entry["branch_prefix"]
    statuses = entry["statuses"]
    labels = list(entry.get("default_labels") or []) + list(args.label or [])

    description = _read_description(args)
    if not description:
        # Descriptions are mandatory so every issue ships with a
        # Problem / Fix / Why it matters / Acceptance criteria / Status
        # skeleton (see docs/JIRA_GITHUB_WORKFLOW.md). Refuse to create an
        # empty-description issue so the convention is enforced by the
        # tool, not just the docs.
        sys.exit(
            "Refusing to create an issue without a description.\n"
            "Pass --description / --description-file / --description-stdin "
            "(see docs/JIRA_GITHUB_WORKFLOW.md for the template)."
        )

    if not args.force:
        # Refuse to re-create something that's already sitting open under
        # the Epic -- an operator running `new "..."` without checking the
        # board would otherwise create a duplicate of a pre-existing ticket.
        existing = _find_open_issues_with_summary(jira, epic_key, args.summary)
        if existing:
            lines = [
                f"  - {jira.browse_url(i['key'])}  [{i['fields']['status']['name']}]"
                for i in existing
            ]
            sys.exit(
                "Refusing to create a duplicate of an open Jira issue with "
                f"the same summary:\n  {args.summary!r}\n\n"
                "Existing open matches under this Epic:\n"
                + "\n".join(lines)
                + "\n\nIf one of these is what you meant to work on:\n"
                + f"  scripts/jira_task.py start {existing[0]['key']}\n\n"
                "If you really want to create a new issue with this title, "
                "pass --force."
            )

    print(f"Creating {args.type} under {epic_key} ...")
    result = jira.create_issue(
        args.summary,
        issue_type=args.type,
        parent_key=epic_key,
        labels=labels or None,
        assignee_account_id=jira.my_account_id,
        description=description,
    )
    key = result["key"]
    print(f"  ✓ Issue created: {key}  {jira.browse_url(key)}")

    if args.backlog:
        # Backlog-prefill path: skip the branch + In Progress transition so
        # the issue is queued on the board without anyone having started
        # work on it yet. The standard `start <KEY>` flow can pick it up
        # later and create the branch + flip the status.
        jira.add_comment(
            key,
            "Seeded in Backlog (no branch yet). "
            "Run `scripts/jira_task.py start "
            f"{key}` to begin work.",
        )
        print(f"  ✓ {key} left in Backlog (no branch)")
        return

    branch_name = f"{branch_prefix}/{key}-{slugify(args.summary)}"
    _checkout_new_branch(branch_name, base_branch)
    print(f"  ✓ Branch ready: {branch_name}")

    # Transition + comment only after the branch is in place so a failed
    # checkout leaves the issue in Backlog instead of stranded in
    # In Progress with nowhere to commit to.
    jira.transition_by_name(key, statuses["in_progress"])
    print(f"  ✓ {key} → {statuses['in_progress']}")
    jira.add_comment(key, f"Branch created: {branch_name} (off {base_branch})")
    print(f"  ✓ Commented on {key}")


def cmd_start(args: argparse.Namespace) -> None:
    jira = JiraClient()
    entry = repo_config_or_die()
    base_branch = entry["base_branch"]
    branch_prefix = entry["branch_prefix"]
    statuses = entry["statuses"]

    info = jira.get_issue(args.issue_key)
    summary = info["fields"]["summary"]
    print(f"Starting work on {args.issue_key}: {summary}")

    branch_name = f"{branch_prefix}/{args.issue_key}-{slugify(summary)}"
    _checkout_new_branch(branch_name, base_branch)
    print(f"  ✓ Branch ready: {branch_name}")

    # As with cmd_new, only flip the Jira state after the branch exists.
    jira.transition_by_name(args.issue_key, statuses["in_progress"])
    print(f"  ✓ {args.issue_key} → {statuses['in_progress']}")
    jira.add_comment(
        args.issue_key, f"Branch created: {branch_name} (off {base_branch})"
    )
    print(f"  ✓ Commented on {args.issue_key}")


def cmd_link_pr(args: argparse.Namespace) -> None:
    """Attach the current branch's PR to its Jira issue as a remote link."""

    jira = JiraClient()
    branch = current_branch()
    branch_key = issue_key_from_branch(branch)
    issue_key = args.issue_key or _require_issue_key_from_branch()

    if args.pr:
        proc = _run_gh("pr", "view", str(args.pr), "--json", "number,url,title,state")
        pr_info = json.loads(proc.stdout)
    else:
        # Only auto-resolve PR from the branch when the key was inferred from
        # the branch (or the explicit key matches the branch). Otherwise we
        # risk attaching the wrong PR (e.g. feature/ABC-456-... branch +
        # link-pr ABC-123 -> ABC-456's PR would get linked under ABC-123).
        if args.issue_key and branch_key != issue_key:
            sys.exit(
                f"Current branch '{branch}' resolves to "
                f"{branch_key or 'no Jira key'}, not {issue_key}. "
                "Pass --pr explicitly or checkout the matching branch."
            )
        pr_info = _current_pr_for_branch(branch)
        if not pr_info:
            sys.exit(
                f"No PR found for branch '{branch}'. "
                "Pass --pr N or run `gh pr create` first."
            )

    title = f"PR #{pr_info['number']}: {pr_info['title']}"
    global_id = f"github-pr-{pr_info['number']}"
    resolved = pr_info.get("state") == "MERGED"
    jira.upsert_remote_link(
        issue_key,
        url=pr_info["url"],
        title=title,
        global_id=global_id,
        resolved=resolved,
    )
    print(f"  ✓ Linked {pr_info['url']} to {issue_key}")


def cmd_pr(args: argparse.Namespace) -> None:
    """Create a PR for the current branch, link it to Jira, transition to Review."""

    jira = JiraClient()
    entry = repo_config_or_die()
    base_branch = entry["base_branch"]
    statuses = entry["statuses"]
    issue_key = _require_issue_key_from_branch()
    branch = current_branch()

    body = _read_pr_body(args)
    if not body:
        body = (
            f"Jira: {jira.browse_url(issue_key)}\n\n"
            "(No body provided -- edit the PR description on GitHub.)"
        )

    # Ensure branch is pushed. A failed push (auth, rejected ref, network
    # error) means the remote is out of sync with HEAD, so creating a PR for
    # it would point at the wrong commit -- bail instead of silently
    # continuing.
    print(f"Ensuring {branch} is pushed to origin ...")
    push = subprocess.run(
        ["git", "push", "-u", "origin", branch],
        capture_output=True,
        text=True,
        check=False,
    )
    if push.returncode != 0:
        combined = (push.stdout + push.stderr).strip()
        sys.exit(f"git push failed:\n{combined}")

    # Check whether a PR already exists for this branch
    existing = _current_pr_for_branch(branch)
    pr_info: dict[str, Any] | None
    if existing:
        print(f"  i PR already exists: {existing['url']}")
        pr_info = existing
    else:
        title = args.title or _default_pr_title(jira, issue_key)
        print(f"Creating PR (base={base_branch}, head={branch}) ...")
        proc = _run_gh(
            "pr",
            "create",
            "--base",
            base_branch,
            "--head",
            branch,
            "--title",
            title,
            "--body",
            body,
        )
        # gh prints the new PR URL on stdout; tolerate blank trailing
        # lines / quirky output by taking the last non-blank line and
        # falling back to a fresh `gh pr view` if there's nothing usable.
        # The candidate also has to look like an actual URL -- gh can
        # emit warnings as a trailing non-blank line, and we don't want
        # to display "warning: ..." as the PR URL.
        non_blank = [line for line in proc.stdout.splitlines() if line.strip()]
        candidate = non_blank[-1].strip() if non_blank else ""
        pr_info = _current_pr_for_branch(branch)
        if not pr_info:  # pragma: no cover - shouldn't happen
            sys.exit("PR created but could not be re-fetched via gh.")
        if candidate.startswith(("http://", "https://")):
            pr_url = candidate
        else:
            pr_url = pr_info["url"]
        print(f"  ✓ Created: {pr_url}")

    # Link + transition + (optional) CodeRabbit trigger
    jira.upsert_remote_link(
        issue_key,
        url=pr_info["url"],
        title=f"PR #{pr_info['number']}: {pr_info['title']}",
        global_id=f"github-pr-{pr_info['number']}",
    )
    print(f"  ✓ Linked PR to {issue_key}")

    jira.transition_by_name(issue_key, statuses["review"])
    print(f"  ✓ {issue_key} → {statuses['review']}")

    if args.coderabbit:
        _run_gh(
            "pr",
            "comment",
            str(pr_info["number"]),
            "--body",
            "@coderabbitai full review",
        )
        print("  ✓ CodeRabbit review triggered")


def cmd_done(args: argparse.Namespace) -> None:
    """Verify the PR is merged and transition the Jira issue to Done."""

    jira = JiraClient()
    entry = repo_config_or_die()
    statuses = entry["statuses"]

    branch = current_branch()
    branch_key = issue_key_from_branch(branch)
    issue_key = args.issue_key or _require_issue_key_from_branch()

    # Try to fetch the branch's PR so we can verify merge state. But if the
    # caller passed an explicit issue_key that doesn't match the branch
    # (e.g. running ``done ABC-100`` while sitting on feature/ABC-200-*),
    # discard the branch's PR -- it belongs to a different issue and would
    # falsely block or "verify" the transition.
    pr_info = _current_pr_for_branch(branch) if branch_key else None
    if pr_info is not None and args.issue_key and branch_key != args.issue_key:
        pr_info = None

    if pr_info is None:
        if not args.force:
            sys.exit(
                "No PR information available for this transition. Run "
                "from the <prefix>/<KEY>-* branch so the merge state can be "
                "verified, or pass --force to transition without that check."
            )
    elif pr_info.get("state") != "MERGED" and not args.force:
        sys.exit(
            f"PR #{pr_info['number']} state is {pr_info.get('state')}, "
            f"not MERGED. Pass --force to transition anyway."
        )

    jira.transition_by_name(issue_key, statuses["done"])
    print(f"  ✓ {issue_key} → {statuses['done']}")

    if pr_info and pr_info.get("state") == "MERGED":
        merge_commit = (pr_info.get("mergeCommit") or {}).get("oid", "")
        suffix = f" (commit {merge_commit[:8]})" if merge_commit else ""
        jira.upsert_remote_link(
            issue_key,
            url=pr_info["url"],
            title=f"PR #{pr_info['number']}: {pr_info['title']}",
            global_id=f"github-pr-{pr_info['number']}",
            resolved=True,
        )
        jira.add_comment(
            issue_key,
            f"Merged in PR #{pr_info['number']}{suffix}.",
        )
        print("  ✓ Marked PR link resolved + commented")


def _default_pr_title(jira: JiraClient, issue_key: str) -> str:
    info = jira.get_issue(issue_key)
    return f"{issue_key}: {info['fields']['summary']}"


def _read_pr_body(args: argparse.Namespace) -> str | None:
    """Resolve a PR body from the CLI flags (mirrors the description-arg API)."""

    if getattr(args, "body", None):
        return str(args.body)
    path = getattr(args, "body_file", None)
    if path:
        return _read_text_file_or_die(path, "PR body file")
    if getattr(args, "body_stdin", False):
        return sys.stdin.read()
    return None


def cmd_describe(args: argparse.Namespace) -> None:
    description = _read_description(args)
    if not description:
        sys.exit("Provide --description, --description-file, or --description-stdin.")
    jira = JiraClient()
    jira.set_description(args.issue_key, description)
    print(
        f"  ✓ {args.issue_key} description updated  {jira.browse_url(args.issue_key)}"
    )


def cmd_status(_: argparse.Namespace) -> None:
    branch = current_branch()
    key = issue_key_from_branch(branch)
    if not key:
        sys.exit(f"No Jira issue key found in branch name '{branch}'.")

    jira = JiraClient()
    info = jira.get_issue(key)
    f = info["fields"]
    print(f"Branch:   {branch}")
    print(f"Issue:    {key}  {jira.browse_url(key)}")
    print(f"Type:     {f['issuetype']['name']}")
    print(f"Summary:  {f['summary']}")
    print(f"Status:   {f['status']['name']}")
    assignee = f.get("assignee") or {}
    print(f"Assignee: {assignee.get('displayName', '(unassigned)')}")
    parent = f.get("parent")
    if parent:
        print(f"Parent:   {parent['key']}  {parent['fields']['summary']}")
    labels = f.get("labels") or []
    if labels:
        print(f"Labels:   {', '.join(labels)}")


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def _add_description_args(parser: argparse.ArgumentParser) -> None:
    """Attach the three mutually-compatible description-source flags to a parser."""

    parser.add_argument(
        "--description",
        help=(
            "Inline description text (plain text, paragraphs separated by blank lines)"
        ),
    )
    parser.add_argument(
        "--description-file",
        help="Read description from a UTF-8 text file (overridden by --description)",
    )
    parser.add_argument(
        "--description-stdin",
        action="store_true",
        help="Read description from stdin",
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="jira_task", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Create Epic for the current repo")
    p_init.add_argument("title", help="Epic title")
    p_init.add_argument(
        "--base-branch",
        default="main",
        help="Default base branch for new task branches (default: main)",
    )
    p_init.add_argument(
        "--branch-prefix",
        default="feature",
        help="Default prefix for new task branches (default: feature)",
    )
    p_init.add_argument(
        "--label",
        action="append",
        dest="labels",
        help="Default label to apply to every new task (repeatable)",
    )
    p_init.set_defaults(func=cmd_init)

    p_new = sub.add_parser("new", help="Create issue + branch")
    p_new.add_argument("summary", help="Issue summary")
    p_new.add_argument(
        "--type",
        default="Task",
        choices=("Task", "Story"),
        help="Jira issue type (default: Task)",
    )
    p_new.add_argument(
        "--label",
        action="append",
        help="Extra label (repeatable, merged with repo defaults)",
    )
    p_new.add_argument(
        "--backlog",
        action="store_true",
        help=(
            "Prefill mode: create the issue in Backlog without creating "
            "a local branch or transitioning to In Progress. Use `start "
            "<KEY>` later to actually begin work."
        ),
    )
    p_new.add_argument(
        "--force",
        action="store_true",
        help=(
            "Create the issue even if an open issue with the same summary "
            "already exists under the Epic (otherwise the dedup guard "
            "refuses, pointing you at the existing key)."
        ),
    )
    _add_description_args(p_new)
    p_new.set_defaults(func=cmd_new)

    p_describe = sub.add_parser(
        "describe",
        help="Set/replace the description on an existing issue",
    )
    p_describe.add_argument("issue_key", help="e.g. ABC-123")
    _add_description_args(p_describe)
    p_describe.set_defaults(func=cmd_describe)

    p_start = sub.add_parser(
        "start", help="Start an existing issue: branch + transition"
    )
    p_start.add_argument("issue_key", help="e.g. ABC-123")
    p_start.set_defaults(func=cmd_start)

    p_status = sub.add_parser(
        "status", help="Show Jira info for the current branch's issue"
    )
    p_status.set_defaults(func=cmd_status)

    p_link = sub.add_parser(
        "link-pr",
        help="Attach the branch's PR to its Jira issue as a remote link",
    )
    p_link.add_argument(
        "issue_key",
        nargs="?",
        default=None,
        help="Issue key (default: inferred from branch)",
    )
    p_link.add_argument(
        "--pr",
        type=int,
        help="PR number (default: PR for the current branch via `gh pr view`)",
    )
    p_link.set_defaults(func=cmd_link_pr)

    p_pr = sub.add_parser(
        "pr",
        help=("Push branch, gh-create PR, link it to Jira, transition issue to Review"),
    )
    p_pr.add_argument(
        "--title",
        help="PR title (default: '<KEY>: <issue summary>')",
    )
    p_pr.add_argument(
        "--body",
        help="Inline PR body (markdown)",
    )
    p_pr.add_argument(
        "--body-file",
        help="Read PR body from a UTF-8 text file",
    )
    p_pr.add_argument(
        "--body-stdin",
        action="store_true",
        help="Read PR body from stdin",
    )
    p_pr.add_argument(
        "--coderabbit",
        action="store_true",
        help=(
            "Trigger '@coderabbitai full review' on the PR. Off by default "
            "-- only useful if this repo has CodeRabbit installed."
        ),
    )
    p_pr.set_defaults(func=cmd_pr)

    p_done = sub.add_parser(
        "done",
        help=(
            "Transition issue to Done once its PR is merged (plus a wrap-up comment)"
        ),
    )
    p_done.add_argument(
        "issue_key",
        nargs="?",
        default=None,
        help="Issue key (default: inferred from branch)",
    )
    p_done.add_argument(
        "--force",
        action="store_true",
        help="Transition even if PR is missing or not merged",
    )
    p_done.set_defaults(func=cmd_done)

    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
