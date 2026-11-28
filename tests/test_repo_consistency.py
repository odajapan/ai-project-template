"""Guard against the install-extras drift documented in AGENTS.md Setup.

This repo has drifted twice on the "canonical extras" string (see the P1
template audit): Makefile, CI, and AGENTS.md each independently listed a
different combination of optional-dependency groups. These checks assert
the canonical set (dev, claude, jira) stays in sync across the files that
quote it, so a future edit to one of them fails fast instead of silently
diverging again.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_EXTRAS = {"dev", "claude", "jira"}

# The untouched env.example shipped by the template (docs/TEMPLATE_INIT.md
# Phase 2 step 1 asks downstream projects to rewrite this). rename_project.sh
# never touches env.example (no matching extension in its FIND_FILES glob),
# so this string stays byte-identical across a bare rename.
DEFAULT_ENV_EXAMPLE = """\
# Copy this file to .env and fill in the values you need.
# .env is git-ignored; never commit real credentials.
# Format: KEY=value at column 0 — no leading whitespace, no quotes unless needed.

# --- Anthropic / Claude API -------------------------------------------------
# Only needed if this project uses the LLM layer (src/<pkg>/llm.py, the
# `ask`/`chat` CLI commands, examples/). Non-LLM projects can delete this block.
# ANTHROPIC_API_KEY=<your-api-key>

# Optional: override the default model. The default lives in src/<pkg>/llm.py
# (DEFAULT_MODEL) — keep the two in sync.
# CLAUDE_MODEL=claude-sonnet-5

# --- Project settings -------------------------------------------------------
# LOG_LEVEL=INFO
"""


def _extras_from(text: str, pattern: str) -> set[str]:
    match = re.search(pattern, text)
    assert match, f"pattern {pattern!r} not found"
    return set(match.group(1).split(","))


def test_makefile_default_extras_match_canonical() -> None:
    makefile = (REPO_ROOT / "Makefile").read_text()
    extras = _extras_from(makefile, r"EXTRAS \?= ([\w,]+)")
    assert extras == CANONICAL_EXTRAS


def test_ci_extras_match_canonical() -> None:
    ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text()
    extras = _extras_from(ci, r'uv pip install --system -e "\.\[([\w,]+)\]"')
    assert extras == CANONICAL_EXTRAS


def test_agents_md_setup_extras_match_canonical() -> None:
    agents = (REPO_ROOT / "AGENTS.md").read_text()
    extras = _extras_from(agents, r'pip install -e "\.\[([\w,]+)\]"')
    assert extras == CANONICAL_EXTRAS


def test_requirements_txt_default_extras_match_canonical() -> None:
    requirements = (REPO_ROOT / "requirements.txt").read_text()
    extras = _extras_from(requirements, r"-e \.\[([\w,]+)\]")
    assert extras == CANONICAL_EXTRAS


def test_env_example_reviewed_after_template_rename() -> None:
    # This file is excluded from rename_project.sh's blind sed sweep
    # (scripts/rename_project.sh FIND_FILES) specifically so this literal
    # stays "your_project_name" after a rename — otherwise the sed would
    # rewrite it to the same new name as pyproject.toml's, and the skip
    # guard below would become trivially true forever.
    pyproject = (REPO_ROOT / "pyproject.toml").read_text()
    name_match = re.search(r'(?m)^name = "([^"]+)"', pyproject)
    assert name_match, "pyproject.toml has no [project] name field"
    if name_match.group(1) == "your_project_name":
        pytest.skip("template not yet initialized via /init-from-template")

    env_example = (REPO_ROOT / "env.example").read_text()
    assert env_example != DEFAULT_ENV_EXAMPLE, (
        "pyproject.toml was renamed away from the template default but "
        "env.example still matches the untouched template placeholder "
        "byte-for-byte. Run docs/TEMPLATE_INIT.md Phase 2 step 1 (rewrite "
        "env.example for this project's real variables). If the template "
        "defaults are genuinely correct as-is, add a comment noting that "
        "review (e.g. '# reviewed: defaults are correct for this project') "
        "to acknowledge it and unblock this check."
    )


# Learning edge from the /pr-review runs on PR #64 and #69: the command files
# are prose specs that cross-reference their own numbered steps ("go to 8.8",
# "steps 4-5") and the PR template's headings ("the `## Done when` section").
# Every renumbering or heading rename silently broke one of those references
# until a reviewer happened to notice. These checks make the references a
# machine-evaluable gate instead.

COMMANDS_DIR = REPO_ROOT / ".claude" / "commands"
_FENCE = re.compile(r"^\s*```")
_TOP_STEP = re.compile(r"^(\d+)\. ")
_SUB_STEP = re.compile(r"^ +(\d+)\. ")
# "step 7", "steps 4-5", "step 8.8"; the trailing group collects the rest of
# a list or range: "4-5" (hyphen or en dash), "4 and 5", "4, 5".
_STEP_WORD = re.compile(
    r"\bsteps?\s+(\d+(?:\.\d+)?)((?:\s*(?:[\u2013-]|,|and)\s*\d+(?:\.\d+)?)*)", re.I
)
# A bare "8.8" counts as a sub-step reference only when the file defines
# sub-steps under step 8 — "Python 3.12" never has a sub-step 12 to resolve.
_DOTTED = re.compile(r"(?<![\w.`])(\d+)\.(\d+)(?!\w)(?!\.\d)")


def _prose_lines(text: str) -> list[tuple[int, str]]:
    # Numbered lines inside fenced code blocks are output samples, not steps.
    lines, in_fence = [], False
    for number, line in enumerate(text.splitlines(), start=1):
        if _FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence:
            lines.append((number, line))
    return lines


def _defined_steps(text: str) -> set[str]:
    steps: set[str] = set()
    current = None
    for _, line in _prose_lines(text):
        if top := _TOP_STEP.match(line):
            current = top.group(1)
            steps.add(current)
        elif (sub := _SUB_STEP.match(line)) and current is not None:
            steps.add(f"{current}.{sub.group(1)}")
    return steps


def _step_references(text: str) -> list[tuple[int, str]]:
    defined = _defined_steps(text)
    parents_with_substeps = {step.split(".")[0] for step in defined if "." in step}
    refs: list[tuple[int, str]] = []
    for number, line in _prose_lines(text):
        for match in _STEP_WORD.finditer(line):
            refs.append((number, match.group(1)))
            refs.extend(
                (number, ref) for ref in re.findall(r"\d+(?:\.\d+)?", match.group(2))
            )
        for match in _DOTTED.finditer(line):
            if match.group(1) in parents_with_substeps:
                refs.append((number, f"{match.group(1)}.{match.group(2)}"))
    return refs


def test_command_step_references_resolve() -> None:
    dangling, total = [], 0
    for path in sorted(COMMANDS_DIR.glob("*.md")):
        text = path.read_text()
        defined = _defined_steps(text)
        for line, ref in _step_references(text):
            total += 1
            if ref not in defined:
                dangling.append(f"{path.relative_to(REPO_ROOT)}:{line}: step {ref}")
    assert total > 0, "no step references found — the reference regexes are broken"
    assert not dangling, (
        f"Command files reference steps they do not define (renumbered?): {dangling}"
    )


def test_step_reference_check_detects_dangling() -> None:
    spec = "1. First.\n2. Second, see step 3.\n   1. Sub.\n   2. Go to 2.9.\n"
    assert _defined_steps(spec) == {"1", "2", "2.1", "2.2"}
    assert [ref for _, ref in _step_references(spec)] == ["3", "2.9"]


def test_pr_template_sections_match_agents_md() -> None:
    agents = " ".join((REPO_ROOT / "AGENTS.md").read_text().split())
    match = re.search(r"pull_request_template\.md` \(sections: (.+?) —", agents)
    assert match, "AGENTS.md no longer lists the PR template sections"
    listed = match.group(1).split(", ")
    template = (REPO_ROOT / ".github" / "pull_request_template.md").read_text()
    headings = re.findall(r"(?m)^## (.+?)\s*$", template)
    assert listed == headings, (
        "AGENTS.md's PR-body section list and the `## ` headings in "
        ".github/pull_request_template.md have drifted apart"
    )


# Learning edge from the Deploy runs on main after PR #71-#73: the preflight
# job listed self-hosted runners with GITHUB_TOKEN, which GitHub never grants
# the Administration permission that endpoint needs, so every run 403'd --
# with or without a runner. The workflow had been reviewed three times and
# never once executed its own check.


def test_deploy_preflight_does_not_list_runners_with_github_token() -> None:
    deploy = (REPO_ROOT / ".github" / "workflows" / "deploy.yml").read_text()
    assert "/actions/runners" in deploy, "preflight no longer checks for a runner"
    assert "secrets.GITHUB_TOKEN" not in deploy, (
        "deploy.yml uses GITHUB_TOKEN; it cannot be granted Administration: "
        "read, so listing /actions/runners with it always 403s. Use the "
        "RUNNER_CHECK_TOKEN secret (docs/EC2_DEPLOY.md)."
    )
    assert "secrets.RUNNER_CHECK_TOKEN" in deploy
    setup_doc = (REPO_ROOT / "docs" / "EC2_DEPLOY.md").read_text()
    for name in ("RUNNER_CHECK_TOKEN", "DEPLOY_ENABLED"):
        assert name in deploy and name in setup_doc, (
            f"{name} must be documented in docs/EC2_DEPLOY.md wherever "
            "deploy.yml depends on it"
        )


# /template-sync (docs/TEMPLATE_SYNC.md) hangs off two files that nothing
# else exercises: the baseline ini and the SessionStart hook script. The
# baseline follows the env.example pattern above — the template ships it
# empty, a renamed project must fill it (or delete the file to opt out).

TEMPLATE_SYNC_INI = REPO_ROOT / ".claude" / "template-sync.ini"


def _template_sync_commit() -> str:
    match = re.search(r"(?m)^\s*commit\s*=\s*(\S*)\s*$", TEMPLATE_SYNC_INI.read_text())
    assert match, ".claude/template-sync.ini has no template.commit key"
    return match.group(1)


def test_template_sync_baseline_set_after_rename() -> None:
    pyproject = (REPO_ROOT / "pyproject.toml").read_text()
    name_match = re.search(r'(?m)^name = "([^"]+)"', pyproject)
    assert name_match, "pyproject.toml has no [project] name field"
    if name_match.group(1) == "your_project_name":
        assert TEMPLATE_SYNC_INI.exists(), "the template must ship the baseline file"
        assert _template_sync_commit() == "", (
            "the template itself must ship .claude/template-sync.ini with an "
            "empty template.commit, or every downstream clone starts out "
            "believing it already reviewed up to that commit"
        )
        return
    if not TEMPLATE_SYNC_INI.exists():
        pytest.skip("project opted out of template sync (ini deleted)")
    assert re.fullmatch(r"[0-9a-f]{40}", _template_sync_commit()), (
        "pyproject.toml was renamed away from the template default but "
        ".claude/template-sync.ini has no full 40-hex template.commit. Run "
        "/template-sync --init (docs/TEMPLATE_INIT.md Phase 0 step 10) — it "
        "writes `git rev-parse` of the baseline, never an abbreviated SHA or "
        "a ref name — or delete the ini file if this project never wants "
        "template reviews."
    )


def test_settings_hook_scripts_exist_and_are_executable() -> None:
    settings = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text())
    commands = [
        hook["command"]
        for entries in settings.get("hooks", {}).values()
        for entry in entries
        for hook in entry.get("hooks", [])
        if hook.get("type") == "command"
    ]
    scripts = re.findall(r"\.claude/hooks/([\w.-]+)", " ".join(commands))
    assert scripts, "no .claude/hooks/ scripts referenced from settings.json"
    for name in scripts:
        path = REPO_ROOT / ".claude" / "hooks" / name
        assert path.is_file(), f"settings.json references missing hook {path}"
        assert os.access(path, os.X_OK), f"hook script is not executable: {path}"


# Carry-backs from japan-market-index's review of the template (2026-11):
# two committed config files were wrong in ways nothing executed locally.
# `:*` in a permission rule is a word-boundary wildcard, so `claude/:*`
# never matched `claude/foo`; a comment key inside `mcpServers` made Claude
# Code refuse the copied .mcp.json.


def test_permission_rules_do_not_put_a_wildcard_after_a_separator() -> None:
    settings = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text())
    rules = [
        rule for bucket in settings.get("permissions", {}).values() for rule in bucket
    ]
    assert rules, "settings.json has no permission rules"
    bad = [rule for rule in rules if re.search(r"[^\w.]:\*\)$", rule)]
    assert not bad, (
        f"`:*` only matches after a word boundary; use `prefix/*` instead: {bad}"
    )


def test_mcp_example_keeps_only_servers_under_mcp_servers() -> None:
    example = json.loads((REPO_ROOT / ".mcp.json.example").read_text())
    for name, server in example["mcpServers"].items():
        assert isinstance(server, dict) and ("command" in server or "url" in server), (
            f"mcpServers.{name} is not a server definition; move comments to the "
            "top level or Claude Code will not load the copied .mcp.json"
        )
        assert not any(key.startswith("$") for key in server), (
            f"mcpServers.{name} carries a comment key; keep server entries clean"
        )


def _bash_rule_matches(rule: str, command: str) -> bool:
    # Claude Code's two Bash wildcards: a trailing `:*` matches the prefix
    # itself or the prefix followed by a space (word boundary); a bare `*`
    # matches any characters, spaces and colons included.
    if not rule.startswith("Bash(") or not rule.endswith(")"):
        return False
    pattern = rule[len("Bash(") : -1]
    if pattern.endswith(":*"):
        prefix = pattern[:-2]
        return command == prefix or command.startswith(prefix + " ")
    return fnmatch.fnmatchcase(command, pattern)


def test_push_allow_rule_does_not_outrun_the_push_deny_rules() -> None:
    # Review finding on PR #88: `Bash(git push origin claude/*)` also matches
    # `git push origin claude/x --force` and `claude/x:main`, and the deny
    # rules only saw the flag or `main` right after `git push`. Deny wins over
    # allow, so every forbidden form must hit a deny rule.
    settings = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text())
    allow = settings["permissions"]["allow"]
    deny = settings["permissions"]["deny"]
    forbidden = [
        "git push --force origin claude/x",
        "git push -f origin claude/x",
        "git push origin claude/x --force",
        "git push origin claude/x --force-with-lease",
        "git push origin claude/x -f",
        "git push origin claude/x:main",
        "git push origin claude/x:master",
        "git push origin main",
        "git push origin master",
    ]
    for command in forbidden:
        assert any(_bash_rule_matches(r, command) for r in deny), (
            f"no deny rule catches {command!r}"
        )
    permitted = ["git push origin claude/x", "git checkout -b claude/x"]
    for command in permitted:
        assert any(_bash_rule_matches(r, command) for r in allow), (
            f"no allow rule matches {command!r}"
        )
        assert not any(_bash_rule_matches(r, command) for r in deny), (
            f"a deny rule also matches {command!r}"
        )
