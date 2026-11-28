"""scripts/precommit_tool.sh picks the interpreter pre-commit's ruff and mypy
hooks run under, so they judge with the versions `make check` uses. Driven
with fake interpreters; needs bash, no network."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WRAPPER = REPO_ROOT / "scripts" / "precommit_tool.sh"

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="bash missing")


def _fake_python(path: Path, log: Path, *, module_missing: bool = False) -> Path:
    # The wrapper probes `-c` for the module first, then execs `-m <tool>`;
    # only the latter is logged, so the log is the hook's exact command.
    path.parent.mkdir(parents=True, exist_ok=True)
    probe_exit = 1 if module_missing else 0
    path.write_text(
        f'#!/bin/sh\nif [ "$1" = -c ]; then exit {probe_exit}; fi\n'
        f'echo "$@" >> "{log}"\n'
    )
    path.chmod(0o755)
    return path


def _checkout(tmp_path: Path) -> Path:
    # The wrapper locates the checkout relative to its own path, so a copy
    # under tmp_path/scripts/ sees tmp_path/.venv, not the repo's.
    checkout = tmp_path / "checkout"
    (checkout / "scripts").mkdir(parents=True)
    shutil.copy(WRAPPER, checkout / "scripts" / "precommit_tool.sh")
    return checkout


def _run(
    checkout: Path, *args: str, path_dir: Path | None = None, **env: str
) -> subprocess.CompletedProcess[str]:
    full_env = {k: v for k, v in os.environ.items() if k != "PRECOMMIT_PYTHON"}
    if path_dir is not None:
        full_env["PATH"] = f"{path_dir}:{full_env['PATH']}"
    full_env.update(env)
    return subprocess.run(
        ["bash", str(checkout / "scripts" / "precommit_tool.sh"), *args],
        cwd=checkout,
        env=full_env,
        capture_output=True,
        text=True,
        check=False,
    )


def _logged(log: Path) -> list[str]:
    return log.read_text().splitlines() if log.exists() else []


def test_precommit_python_wins(tmp_path: Path) -> None:
    checkout = _checkout(tmp_path)
    log = tmp_path / "explicit.log"
    explicit = _fake_python(tmp_path / "explicit" / "python", log)
    venv_log = tmp_path / "venv.log"
    _fake_python(checkout / ".venv" / "bin" / "python", venv_log)
    (checkout / ".venv" / ".make-venv-ok").write_text("")
    result = _run(
        checkout, "ruff", "check", "--fix", "a.py", PRECOMMIT_PYTHON=str(explicit)
    )
    assert result.returncode == 0, result.stderr
    assert _logged(log) == ["-m ruff check --fix a.py"]
    assert _logged(venv_log) == []


def test_finished_venv_is_used_without_precommit_python(tmp_path: Path) -> None:
    checkout = _checkout(tmp_path)
    venv_log = tmp_path / "venv.log"
    _fake_python(checkout / ".venv" / "bin" / "python", venv_log)
    (checkout / ".venv" / ".make-venv-ok").write_text("")
    path_log = tmp_path / "path.log"
    path_dir = _fake_python(tmp_path / "bin" / "python", path_log).parent
    result = _run(checkout, "mypy", "src", "scripts", path_dir=path_dir)
    assert result.returncode == 0, result.stderr
    assert _logged(venv_log) == ["-m mypy src scripts"]
    assert _logged(path_log) == []


def test_unfinished_or_dead_venv_falls_back_to_path_python(tmp_path: Path) -> None:
    path_log = tmp_path / "path.log"
    path_dir = _fake_python(tmp_path / "bin" / "python", path_log).parent
    # No marker: `make venv` never finished, the .venv is not trusted.
    bare = _checkout(tmp_path / "bare")
    _fake_python(bare / ".venv" / "bin" / "python", tmp_path / "bare.log")
    assert _run(bare, "ruff", "format", path_dir=path_dir).returncode == 0
    # Marker but a dangling python symlink: the Python it was built from is gone.
    dead = _checkout(tmp_path / "dead")
    (dead / ".venv" / "bin").mkdir(parents=True)
    (dead / ".venv" / "bin" / "python").symlink_to(tmp_path / "gone")
    (dead / ".venv" / ".make-venv-ok").write_text("")
    assert _run(dead, "ruff", "format", path_dir=path_dir).returncode == 0
    assert _logged(path_log) == ["-m ruff format", "-m ruff format"]
    assert _logged(tmp_path / "bare.log") == []


def test_missing_interpreter_and_missing_module_are_told_apart(tmp_path: Path) -> None:
    checkout = _checkout(tmp_path)
    gone = _run(checkout, "ruff", PRECOMMIT_PYTHON=str(tmp_path / "nope" / "python"))
    assert gone.returncode == 1
    assert "not found" in gone.stderr
    bare = _fake_python(
        tmp_path / "bare" / "python", tmp_path / "bare.log", module_missing=True
    )
    missing = _run(checkout, "ruff", PRECOMMIT_PYTHON=str(bare))
    assert missing.returncode == 1
    assert "run make venv" in missing.stderr
    assert _logged(tmp_path / "bare.log") == []


def test_tool_name_is_required(tmp_path: Path) -> None:
    result = _run(_checkout(tmp_path))
    assert result.returncode == 2
    assert "usage" in result.stderr


def test_precommit_config_routes_ruff_and_mypy_through_the_wrapper() -> None:
    # A bare `ruff` / `mypy` entry would run whatever is first on PATH, which
    # can belong to a different interpreter than the one `make check` uses.
    config = (REPO_ROOT / ".pre-commit-config.yaml").read_text()
    local = config.split("- repo: local", 1)[1].split("- repo:", 1)[0]
    entries = re.findall(r"(?m)^\s*entry: (.+)$", local)
    assert len(entries) == 3, entries
    for entry in entries:
        assert entry.startswith("scripts/precommit_tool.sh "), entry
        assert entry.split()[1] in {"ruff", "mypy"}, entry
    assert os.access(WRAPPER, os.X_OK), "scripts/precommit_tool.sh must be executable"
