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

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_EXTRAS = {"dev", "claude", "jira"}


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
