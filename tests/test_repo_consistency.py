"""Guard against the install-extras drift documented in AGENTS.md Setup.

This repo has drifted twice on the "canonical extras" string (see the P1
template audit): Makefile, CI, and AGENTS.md each independently listed a
different combination of optional-dependency groups. These checks assert
the canonical set (dev, claude, jira) stays in sync across the files that
quote it, so a future edit to one of them fails fast instead of silently
diverging again.
"""

from __future__ import annotations

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
