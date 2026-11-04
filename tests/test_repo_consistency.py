"""Guard against the install-extras drift documented in AGENTS.md Setup.

This repo has drifted twice on the "canonical extras" string (see the P1
template audit): Makefile, CI, and AGENTS.md each independently listed a
different combination of optional-dependency groups. These checks assert
the canonical set (dev, claude, jira) stays in sync across the files that
quote it, so a future edit to one of them fails fast instead of silently
diverging again.
"""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
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


# Commands that only make sense inside Claude Code (Jira helpers, the wrapper
# around Claude Code's bundled code-review skill). Everything else under
# .claude/commands/ needs a Codex copy — see docs/CODEX.md.
CLAUDE_ONLY_COMMANDS = {"jira", "daily-report", "pr-review"}

# Projects that answer "no" to the Codex question in docs/TEMPLATE_INIT.md
# delete both directories; the Codex checks then have nothing to guard.
requires_codex = pytest.mark.skipif(
    not (REPO_ROOT / ".codex").is_dir() and not (REPO_ROOT / ".agents").is_dir(),
    reason="Codex layer removed via /init-from-template",
)


def _codex_copies() -> list[Path]:
    return [
        *(REPO_ROOT / ".codex/agents").glob("*.toml"),
        *(REPO_ROOT / ".agents/skills").glob("source-command-*/SKILL.md"),
    ]


def _ported_from_hash(source: Path) -> str:
    # rename_project.sh rewrites the package name in sources and copies alike
    # but never touches the markers, so hash the source as the template wrote it.
    text = source.read_text()
    pyproject = (REPO_ROOT / "pyproject.toml").read_text()
    name_match = re.search(r'(?m)^name = "([^"]+)"', pyproject)
    if name_match and name_match.group(1) != "your_project_name":
        text = text.replace(name_match.group(1), "your_project_name")
    return hashlib.sha256(text.encode()).hexdigest()[:12]


@requires_codex
def test_every_claude_agent_has_a_codex_copy() -> None:
    claude_agents = {p.stem for p in (REPO_ROOT / ".claude/agents").glob("*.md")}
    codex_agents = {p.stem for p in (REPO_ROOT / ".codex/agents").glob("*.toml")}
    assert claude_agents == codex_agents


@requires_codex
def test_every_workflow_command_has_a_codex_skill() -> None:
    commands = {p.stem for p in (REPO_ROOT / ".claude/commands").glob("*.md")}
    skills = {
        p.parent.name.removeprefix("source-command-")
        for p in (REPO_ROOT / ".agents/skills").glob("source-command-*/SKILL.md")
    }
    assert skills == commands - CLAUDE_ONLY_COMMANDS


@requires_codex
def test_codex_agent_files_are_valid() -> None:
    for path in (REPO_ROOT / ".codex/agents").glob("*.toml"):
        agent = tomllib.loads(path.read_text())
        assert agent.get("name") == path.stem, path
        assert agent.get("description"), path
        assert agent.get("developer_instructions"), path


@requires_codex
def test_codex_skill_names_match_their_directories() -> None:
    for path in (REPO_ROOT / ".agents/skills").glob("*/SKILL.md"):
        match = re.search(r'^name: "?([^"\n]+)"?$', path.read_text(), re.M)
        assert match and match.group(1) == path.parent.name, path


@requires_codex
def test_codex_format_hook_matches_apply_patch() -> None:
    hooks = json.loads((REPO_ROOT / ".codex/hooks.json").read_text())["hooks"]
    matchers = [group.get("matcher", "") for group in hooks["PostToolUse"]]
    assert any(re.search(m, "apply_patch") for m in matchers), matchers


@requires_codex
def test_codex_copies_are_in_sync_with_their_source() -> None:
    stale = []
    for copy in _codex_copies():
        match = re.search(r"ported-from: (\S+) sha256:([0-9a-f]{12})", copy.read_text())
        assert match, f"{copy} has no ported-from marker"
        source = REPO_ROOT / match.group(1)
        assert source.is_file(), f"{copy} was ported from missing {match.group(1)}"
        expected = _ported_from_hash(source)
        if expected != match.group(2):
            stale.append(f"{copy.relative_to(REPO_ROOT)} (sha256:{expected})")
    assert not stale, (
        f"Source changed since these were ported: {stale}. Port the change by "
        "hand (see docs/CODEX.md), then set the ported-from marker to the hash "
        "shown."
    )


@requires_codex
def test_codex_copies_drop_claude_specifics() -> None:
    # `claude/<anything>` branch refs (but not `.claude/` paths), the Claude
    # CLI flag, and the `Codex/*` / `.Codex/` casing a blind replace produces.
    claude_only = re.compile(
        r"(?<![.\w])claude/[\w<$*{]|\bCodex/|--dangerously-skip-permissions"
    )
    offenders = [
        str(p.relative_to(REPO_ROOT))
        for p in _codex_copies()
        if claude_only.search(p.read_text())
    ]
    assert not offenders, (
        f"Claude branch prefix, CLI flag or bad Codex casing in: {offenders}"
    )


# Learning edge from the /pr-review runs on PR #64 and #69: the command files
# are prose specs that cross-reference their own numbered steps ("go to 8.8",
# "steps 4–5") and the PR template's headings ("the `## Done when` section").
# Every renumbering or heading rename silently broke one of those references
# until a reviewer happened to notice. These checks make the references a
# machine-evaluable gate instead.

COMMANDS_DIR = REPO_ROOT / ".claude" / "commands"
_FENCE = re.compile(r"^\s*```")
_TOP_STEP = re.compile(r"^(\d+)\. ")
_SUB_STEP = re.compile(r"^ +(\d+)\. ")
# "step 7", "steps 4–5", "step 8.8"; the trailing group collects the rest of
# a list or range ("4–5", "4 and 5", "4, 5").
_STEP_WORD = re.compile(
    r"\bsteps?\s+(\d+(?:\.\d+)?)((?:\s*(?:[–-]|,|and)\s*\d+(?:\.\d+)?)*)", re.I
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
    spec = "1. First.\n2. Second — see step 3.\n   1. Sub.\n   2. Go to 2.9.\n"
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
