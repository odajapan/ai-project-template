"""Tests for ``scripts/jira_task.py``.

No real Jira/GitHub/network calls: ``JiraClient._request`` and subprocess
calls (``git``, ``gh``) are mocked at the boundary, per the project's
testing convention (mock only at system boundaries).

``scripts/`` isn't an installed package, so it isn't on ``sys.path`` by
default. Insert it directly here (rather than via a second
``conftest.py``) -- pytest's default "prepend" import mode gives every
``conftest.py`` the same bare module name ``conftest``, so a second one
under ``tests/scripts/`` would shadow ``tests/conftest.py`` in
``sys.modules`` and break the ``from conftest import ...`` used by other
test modules.

``jira_task`` needs the optional ``jira`` extra (``requests``, ``pyyaml``).
Skip this whole module gracefully when it isn't installed, rather than
failing collection -- the default ``pip install -e ".[dev]"`` setup does
not include it.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

yaml = pytest.importorskip("yaml")
pytest.importorskip("requests")

_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import jira_task  # noqa: E402

# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Fix /metrics/records pagination", "fix-metricsrecords-pagination"),
        ("  leading/trailing spaces  ", "leadingtrailing-spaces"),
        ("Multiple   spaces_and_underscores", "multiple-spaces-and-underscores"),
        ("", "task"),
        ("!!!", "task"),
    ],
)
def test_slugify(text: str, expected: str) -> None:
    assert jira_task.slugify(text) == expected


def test_slugify_truncates_to_max_len() -> None:
    long_text = "word " * 20
    slug = jira_task.slugify(long_text, max_len=10)
    assert len(slug) <= 10
    assert not slug.startswith("-")
    assert not slug.endswith("-")


@pytest.mark.parametrize(
    ("branch", "expected"),
    [
        ("feature/ABC-123-fix-thing", "ABC-123"),
        ("claude/ABC-9-slug", "ABC-9"),
        ("main", None),
        ("feature/no-key-here", None),
    ],
)
def test_issue_key_from_branch(branch: str, expected: str | None) -> None:
    assert jira_task.issue_key_from_branch(branch) == expected


def test_plaintext_to_adf_single_paragraph() -> None:
    adf = jira_task._plaintext_to_adf("Hello world")
    assert adf == {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": "Hello world"}],
            }
        ],
    }


def test_plaintext_to_adf_splits_paragraphs_on_blank_lines() -> None:
    adf = jira_task._plaintext_to_adf("Problem\n\nFix")
    assert len(adf["content"]) == 2
    assert adf["content"][0]["content"] == [{"type": "text", "text": "Problem"}]
    assert adf["content"][1]["content"] == [{"type": "text", "text": "Fix"}]


def test_plaintext_to_adf_hard_breaks_within_paragraph() -> None:
    adf = jira_task._plaintext_to_adf("line one\nline two")
    content = adf["content"][0]["content"]
    assert content == [
        {"type": "text", "text": "line one"},
        {"type": "hardBreak"},
        {"type": "text", "text": "line two"},
    ]


def test_plaintext_to_adf_drops_blank_paragraphs() -> None:
    adf = jira_task._plaintext_to_adf("\n\nreal text\n\n\n\n")
    assert len(adf["content"]) == 1


@pytest.mark.parametrize(
    "ref",
    ["main", "feature/ABC-123-slug", "release-1.0", "a"],
)
def test_validate_git_ref_accepts_valid_refs(ref: str) -> None:
    assert jira_task._validate_git_ref(ref, "test ref") == ref


@pytest.mark.parametrize(
    "ref",
    ["-force", "--upload-pack=evil", "", "has space", "semi;colon"],
)
def test_validate_git_ref_rejects_unsafe_refs(ref: str) -> None:
    with pytest.raises(SystemExit):
        jira_task._validate_git_ref(ref, "test ref")


# ---------------------------------------------------------------------------
# Config persistence
# ---------------------------------------------------------------------------


def test_load_config_missing_file_returns_empty_repos(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(jira_task, "CONFIG_PATH", tmp_path / "missing.yaml")
    assert jira_task.load_config() == {"repos": {}}


def test_load_config_invalid_yaml_exits(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "map.yaml"
    config_path.write_text("repos: [unterminated", encoding="utf-8")
    monkeypatch.setattr(jira_task, "CONFIG_PATH", config_path)
    with pytest.raises(SystemExit):
        jira_task.load_config()


def test_load_config_non_dict_repos_normalizes_to_empty(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "map.yaml"
    config_path.write_text("repos: not-a-dict\n", encoding="utf-8")
    monkeypatch.setattr(jira_task, "CONFIG_PATH", config_path)
    assert jira_task.load_config()["repos"] == {}


def test_save_config_round_trips_and_sets_permissions(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "nested" / "map.yaml"
    monkeypatch.setattr(jira_task, "CONFIG_PATH", config_path)

    jira_task.save_config({"repos": {"my-repo": {"epic": "ABC-1"}}})

    assert config_path.exists()
    assert (config_path.stat().st_mode & 0o777) == 0o600
    assert jira_task.load_config() == {"repos": {"my-repo": {"epic": "ABC-1"}}}


def _write_config(tmp_path, monkeypatch, repos: dict[str, Any]) -> None:
    config_path = tmp_path / "map.yaml"
    config_path.write_text(
        yaml.safe_dump({"repos": repos}, sort_keys=False), encoding="utf-8"
    )
    monkeypatch.setattr(jira_task, "CONFIG_PATH", config_path)


def test_repo_config_or_die_missing_repo_exits(tmp_path, monkeypatch) -> None:
    _write_config(tmp_path, monkeypatch, {})
    monkeypatch.setattr(jira_task, "repo_name", lambda: "my-repo")
    with pytest.raises(SystemExit, match="not initialized"):
        jira_task.repo_config_or_die()


def test_repo_config_or_die_malformed_epic_exits(tmp_path, monkeypatch) -> None:
    _write_config(tmp_path, monkeypatch, {"my-repo": {"epic": ""}})
    monkeypatch.setattr(jira_task, "repo_name", lambda: "my-repo")
    with pytest.raises(SystemExit, match="'epic'"):
        jira_task.repo_config_or_die()


def test_repo_config_or_die_fills_in_defaults(tmp_path, monkeypatch) -> None:
    _write_config(tmp_path, monkeypatch, {"my-repo": {"epic": "ABC-1"}})
    monkeypatch.setattr(jira_task, "repo_name", lambda: "my-repo")

    entry = jira_task.repo_config_or_die()

    assert entry["base_branch"] == "main"
    assert entry["branch_prefix"] == "feature"
    assert entry["statuses"] == jira_task.DEFAULT_STATUSES


def test_repo_config_or_die_partial_statuses_merge_with_defaults(
    tmp_path, monkeypatch
) -> None:
    _write_config(
        tmp_path,
        monkeypatch,
        {
            "my-repo": {
                "epic": "ABC-1",
                "branch_prefix": "fix",
                "statuses": {"in_progress": "In Dev"},
            }
        },
    )
    monkeypatch.setattr(jira_task, "repo_name", lambda: "my-repo")

    entry = jira_task.repo_config_or_die()

    assert entry["branch_prefix"] == "fix"
    assert entry["statuses"] == {
        "in_progress": "In Dev",
        "review": "In Review",
        "done": "Done",
    }


def test_repo_config_or_die_invalid_statuses_key_exits(tmp_path, monkeypatch) -> None:
    _write_config(
        tmp_path,
        monkeypatch,
        {"my-repo": {"epic": "ABC-1", "statuses": {"bogus_key": "Whatever"}}},
    )
    monkeypatch.setattr(jira_task, "repo_name", lambda: "my-repo")
    with pytest.raises(SystemExit, match="'statuses'"):
        jira_task.repo_config_or_die()


def test_repo_config_or_die_invalid_default_labels_exits(tmp_path, monkeypatch) -> None:
    _write_config(
        tmp_path, monkeypatch, {"my-repo": {"epic": "ABC-1", "default_labels": "x"}}
    )
    monkeypatch.setattr(jira_task, "repo_name", lambda: "my-repo")
    with pytest.raises(SystemExit, match="'default_labels'"):
        jira_task.repo_config_or_die()


# ---------------------------------------------------------------------------
# JiraClient.transition_by_name
# ---------------------------------------------------------------------------


def _make_client_with_env(monkeypatch) -> jira_task.JiraClient:
    monkeypatch.setenv("JIRA_BASE_URL", "https://example.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "user@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "token")
    monkeypatch.setenv("JIRA_PROJECT_KEY", "ABC")
    return jira_task.JiraClient()


def test_jira_client_requires_env_vars(monkeypatch) -> None:
    for key in jira_task.REQUIRED_ENV:
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(SystemExit, match="Missing required env vars"):
        jira_task.JiraClient()


def test_transition_by_name_matches_case_insensitively(monkeypatch) -> None:
    client = _make_client_with_env(monkeypatch)
    client._request = mock.MagicMock(
        return_value={
            "transitions": [
                {"id": "11", "to": {"name": "Backlog"}},
                {"id": "31", "to": {"name": "in progress"}},
            ]
        }
    )

    client.transition_by_name("ABC-1", "In Progress")

    # First call fetches the transitions list, second posts the resolved id.
    get_call, post_call = client._request.call_args_list
    assert get_call.args == ("GET", "/rest/api/3/issue/ABC-1/transitions")
    assert post_call.args == ("POST", "/rest/api/3/issue/ABC-1/transitions")
    assert post_call.kwargs["json"] == {"transition": {"id": "31"}}


def test_transition_by_name_no_match_exits_listing_available(monkeypatch) -> None:
    client = _make_client_with_env(monkeypatch)
    client._request = mock.MagicMock(
        return_value={"transitions": [{"id": "11", "to": {"name": "Backlog"}}]}
    )

    with pytest.raises(SystemExit, match="Backlog"):
        client.transition_by_name("ABC-1", "In Progress")

    # Only the GET happened -- no transition POST when nothing matched.
    assert client._request.call_count == 1


def test_transition_by_name_no_transitions_available_exits(monkeypatch) -> None:
    client = _make_client_with_env(monkeypatch)
    client._request = mock.MagicMock(return_value={"transitions": []})

    with pytest.raises(SystemExit, match=r"\(none\)"):
        client.transition_by_name("ABC-1", "In Progress")


# ---------------------------------------------------------------------------
# search_jql_all pagination (JiraClient._request mocked; no network)
# ---------------------------------------------------------------------------


def test_search_jql_all_terminates_on_full_page_without_token() -> None:
    """A full page whose response carries no ``nextPageToken`` IS the last
    page -- must terminate after a single request, not refetch forever."""

    page_size = 50
    full_page = [
        {"key": f"ABC-{100 + i}", "fields": {"summary": f"issue {i}"}}
        for i in range(page_size)
    ]
    client = mock.MagicMock()
    client._request.return_value = {"issues": full_page}  # no nextPageToken

    issues = jira_task.search_jql_all(
        client, 'project = "ABC"', fields="summary", page_size=page_size
    )

    assert len(issues) == page_size
    assert client._request.call_count == 1


def test_search_jql_all_fails_fast_on_cycling_tokens() -> None:
    """A broken upstream that never stops returning tokens must abort
    loudly instead of looping and accumulating issues without bound."""

    client = mock.MagicMock()
    client._request.return_value = {
        "issues": [{"key": "ABC-1"}],
        "nextPageToken": "same-token-every-time",
    }

    with pytest.raises(RuntimeError, match="did not terminate"):
        jira_task.search_jql_all(client, "jql", fields="summary", max_pages=5)
    assert client._request.call_count == 5


def test_search_jql_all_follows_tokens_across_three_pages() -> None:
    client = mock.MagicMock()
    client._request.side_effect = [
        {"issues": [{"key": "ABC-1"}], "nextPageToken": "t2"},
        {"issues": [{"key": "ABC-2"}], "nextPageToken": "t3"},
        {"issues": [{"key": "ABC-3"}]},
    ]

    issues = jira_task.search_jql_all(client, "jql", fields="summary")

    assert [i["key"] for i in issues] == ["ABC-1", "ABC-2", "ABC-3"]
    sent_tokens = [
        call.kwargs["params"].get("nextPageToken")
        for call in client._request.call_args_list
    ]
    assert sent_tokens == [None, "t2", "t3"]


# ---------------------------------------------------------------------------
# _find_open_issues_with_summary
# ---------------------------------------------------------------------------


def _make_fake_client(returned_issues: list[dict[str, Any]]) -> mock.MagicMock:
    client = mock.MagicMock()
    client.project_key = "ABC"
    client._request.return_value = {"issues": returned_issues}
    return client


def test_find_open_issues_with_summary_returns_exact_matches() -> None:
    client = _make_fake_client(
        returned_issues=[
            {
                "key": "ABC-305",
                "fields": {
                    "summary": "Fix specs.csv cache invalidation",
                    "status": {"name": "Backlog"},
                },
            },
            # Fuzzy-match noise from JQL's ~ operator -- different summary,
            # must be filtered out by the exact-match step.
            {
                "key": "ABC-999",
                "fields": {
                    "summary": "Fix specs.csv cache invalidation for real",
                    "status": {"name": "Backlog"},
                },
            },
        ]
    )

    matches = jira_task._find_open_issues_with_summary(
        client, "ABC-286", "Fix specs.csv cache invalidation"
    )

    assert [m["key"] for m in matches] == ["ABC-305"]


def test_find_open_issues_with_summary_empty_when_no_match() -> None:
    client = _make_fake_client(returned_issues=[])
    assert (
        jira_task._find_open_issues_with_summary(client, "ABC-286", "Brand new title")
        == []
    )


def test_find_open_issues_with_summary_escapes_quotes_and_backslashes() -> None:
    """The JQL string literal escaping must survive operator-typed weirdness."""

    client = _make_fake_client(returned_issues=[])

    jira_task._find_open_issues_with_summary(
        client, "ABC-286", 'has "quotes" and \\backslash'
    )

    sent_jql = client._request.call_args.kwargs["params"]["jql"]
    assert r"\"quotes\"" in sent_jql, sent_jql
    assert r"\\backslash" in sent_jql, sent_jql
    assert "statusCategory != Done" in sent_jql
    assert 'parent = "ABC-286"' in sent_jql


def test_find_open_issues_with_summary_uses_project_key_from_client() -> None:
    client = _make_fake_client(returned_issues=[])
    client.project_key = "OTHER"

    jira_task._find_open_issues_with_summary(client, "OTHER-1", "Whatever")

    sent_jql = client._request.call_args.kwargs["params"]["jql"]
    assert 'project = "OTHER"' in sent_jql


# ---------------------------------------------------------------------------
# Branch/repo helpers that shell out to git
# ---------------------------------------------------------------------------


def test_current_branch_uses_git_branch_show_current(monkeypatch) -> None:
    monkeypatch.setattr(
        jira_task,
        "_run_git",
        lambda *args, **kwargs: mock.MagicMock(stdout="feature/ABC-1-x\n"),
    )
    assert jira_task.current_branch() == "feature/ABC-1-x"
