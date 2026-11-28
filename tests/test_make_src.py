"""The Makefile runs this checkout's own code: `make which_src` must resolve
the package from this checkout's src/, and `.venv` is picked up only after
`make venv` finished. Needs make; no network."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(shutil.which("make") is None, reason="make missing")


def _env() -> dict[str, str]:
    # No jobserver flags leaking in when pytest itself runs under `make test`.
    drop = ("MAKEFLAGS", "MAKELEVEL", "MFLAGS")
    return {k: v for k, v in os.environ.items() if k not in drop}


def test_make_exports_this_checkouts_src() -> None:
    # An editable install points at one checkout; a clone or worktree must
    # still run its own src from make targets. The exported PYTHONPATH is
    # asserted directly because the resolved module alone also matches in
    # the checkout the editable install points at.
    result = subprocess.run(
        ["make", "-s", f"PYTHON_INTERPRETER={sys.executable}", "which_src"],
        cwd=REPO_ROOT,
        env=_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    out = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    assert out["PYTHONPATH"].split(":")[0] == str(REPO_ROOT / "src")
    assert Path(out["module"]).is_relative_to(REPO_ROOT / "src")


def _interpreter_in(tmp_path: Path, *, marker: bool, dangling: bool = False) -> str:
    # `make -n` only prints the recipe, so a copy of the Makefile is enough.
    venv = tmp_path / ".venv"
    (venv / "bin").mkdir(parents=True)
    (tmp_path / "Makefile").write_text((REPO_ROOT / "Makefile").read_text())
    if dangling:
        (venv / "bin" / "python").symlink_to(tmp_path / "gone" / "python3.12")
    else:
        (venv / "bin" / "python").write_text("")
    if marker:
        (venv / ".make-venv-ok").write_text("")
    result = subprocess.run(
        ["make", "-s", "-n", "which_src"],
        cwd=tmp_path,
        env=_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    line = next(ln for ln in result.stdout.splitlines() if "interpreter=" in ln)
    return line.split("interpreter=", 1)[1].rstrip('"')


def test_venv_is_used_only_after_make_venv_finished(tmp_path: Path) -> None:
    assert _interpreter_in(tmp_path / "a", marker=True) == str(
        (tmp_path / "a" / ".venv" / "bin" / "python").resolve()
    )
    # A bare or stale .venv must not hijack an activated conda env.
    assert _interpreter_in(tmp_path / "b", marker=False) == "python"
    # The Python the .venv was built from is gone: fall back, don't fail.
    assert _interpreter_in(tmp_path / "c", marker=True, dangling=True) == "python"


def test_precommit_puts_the_venv_bin_on_path(tmp_path: Path) -> None:
    # pre-commit's `language: system` hooks (ruff, mypy) resolve on PATH, not
    # through the interpreter that starts pre-commit.
    venv_bin = tmp_path / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    (venv_bin / "python").write_text("")
    (tmp_path / ".venv" / ".make-venv-ok").write_text("")
    (tmp_path / "Makefile").write_text((REPO_ROOT / "Makefile").read_text())
    result = subprocess.run(
        ["make", "-s", "-n", "precommit"],
        cwd=tmp_path,
        env=_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith(f'PATH="{venv_bin.resolve()}/:$PATH" ')
    # With a bare interpreter name nothing (not even ./) is prepended.
    plain = subprocess.run(
        ["make", "-s", "-n", "PYTHON_INTERPRETER=python", "precommit"],
        cwd=tmp_path,
        env=_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert plain.stdout.startswith('PATH="$PATH" python -m pre_commit')


def test_make_venv_names_the_missing_interpreter(tmp_path: Path) -> None:
    (tmp_path / "Makefile").write_text((REPO_ROOT / "Makefile").read_text())
    result = subprocess.run(
        ["make", "VENV_PYTHON=/nonexistent/python3.12", "venv"],
        cwd=tmp_path,
        env=_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "VENV_PYTHON" in result.stderr
    assert not (tmp_path / ".venv").exists()


def test_venv_python_prefers_the_highest_pyenv_patch_release(tmp_path: Path) -> None:
    # A string sort would put 3.12.9 after 3.12.11.
    (tmp_path / "Makefile").write_text((REPO_ROOT / "Makefile").read_text())
    home = tmp_path / "home"
    for version in ("3.12.9", "3.12.11", "3.12.10"):
        bin_dir = home / ".pyenv" / "versions" / version / "bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "python").write_text("")
    env = _env()
    env["HOME"] = str(home)
    result = subprocess.run(
        ["make", "-n", "venv"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert f"{home}/.pyenv/versions/3.12.11/bin/python -m venv --clear" in result.stdout


def test_make_venv_rebuilds_a_venv_whose_python_is_gone(tmp_path: Path) -> None:
    # A plain `python -m venv` keeps a dangling bin/python symlink, so the
    # .venv would stay dead and every make target with it.
    (tmp_path / "Makefile").write_text((REPO_ROOT / "Makefile").read_text())
    (tmp_path / ".venv" / "bin").mkdir(parents=True)
    (tmp_path / ".venv" / "bin" / "python").symlink_to(tmp_path / "gone")
    fake = tmp_path / "fake-python"
    fake.write_text(f'#!/bin/sh\necho "$@" > {tmp_path / "args"}\nexit 1\n')
    fake.chmod(0o755)
    subprocess.run(
        ["make", f"VENV_PYTHON={fake}", "venv"],
        cwd=tmp_path,
        env=_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert (tmp_path / "args").read_text().split() == [
        "-m",
        "venv",
        "--clear",
        str(tmp_path / ".venv"),
    ]
