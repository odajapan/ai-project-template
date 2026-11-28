"""scripts/new_clone.sh against a local bare origin, with HOME and
TMUX_PROJECTS under tmp_path. No network, no tmux, no real ~/.config."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "new_clone.sh"

pytestmark = pytest.mark.skipif(
    any(shutil.which(tool) is None for tool in ("make", "git", "bash", "awk")),
    reason="needs make, git, bash and awk",
)

VENV_OK = "venv:\n\ttouch $(CURDIR)/.venv-made\n"
VENV_FAIL = "venv:\n\t@echo boom >&2; false\n"


def _env(tmp_path: Path) -> dict[str, str]:
    """Isolated from the caller: no git hook/index variables, and no make
    jobserver flags when pytest itself runs under `make test`."""
    drop = ("MAKEFLAGS", "MAKELEVEL", "MFLAGS")
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith("GIT_") and k not in drop
    }
    env["HOME"] = str(tmp_path)
    env["TMUX_PROJECTS"] = str(tmp_path / "tmux-projects")
    return env


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *args],
        cwd=cwd,
        env=_env(cwd),
        check=True,
        capture_output=True,
    )


def _make_repo(tmp_path: Path, makefile: str, *, tracked_data: bool = False) -> Path:
    """A 'main checkout' cloned from a bare origin that holds the script.

    By default data/ is untracked (the gitignored-snapshot layout the symlink
    is for); tracked_data commits the data/*/.gitkeep skeleton the template
    ships instead."""
    origin = tmp_path / "origin" / "myrepo.git"
    origin.parent.mkdir()
    _git(tmp_path, "init", "--bare", "-q", str(origin))
    main = tmp_path / "work" / "myrepo"
    main.parent.mkdir()
    _git(tmp_path, "clone", "-q", str(origin), str(main))
    (main / "scripts").mkdir()
    shutil.copy(SCRIPT, main / "scripts" / "new_clone.sh")
    (main / "Makefile").write_text(makefile)
    if tracked_data:
        (main / "data" / "raw").mkdir(parents=True)
        (main / "data" / "raw" / ".gitkeep").write_text("")
    _git(main, "add", "-A")
    _git(
        main,
        "-c", "user.name=t", "-c", "user.email=t@example.com",
        "commit", "-q", "-m", "init",
    )  # fmt: skip
    _git(main, "push", "-q", "origin", "HEAD")
    if not tracked_data:
        (main / "data").mkdir()
    return main


def _run(main: Path, tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(main / "scripts" / "new_clone.sh"), *args],
        env=_env(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )


def _registered(tmp_path: Path) -> list[str]:
    f = tmp_path / "tmux-projects"
    return f.read_text().splitlines() if f.exists() else []


def test_clones_links_data_registers_and_makes_venv(tmp_path: Path) -> None:
    main = _make_repo(tmp_path, VENV_OK)
    result = _run(main, tmp_path, "ui")
    assert result.returncode == 0, result.stderr
    clone = tmp_path / "work" / "myrepo-ui"
    assert (clone / ".git").is_dir()
    assert (clone / "data").is_symlink()
    assert (clone / ".venv-made").exists()
    # Default session name is <repo>-<suffix>, taken from the origin URL.
    assert _registered(tmp_path) == ["myrepo-ui ~/work/myrepo-ui"]


def test_tracked_data_skeleton_is_left_as_cloned(tmp_path: Path) -> None:
    # The template tracks data/*/.gitkeep, so the clone brings its own data/;
    # replacing it with a symlink would show the tracked files as deleted.
    main = _make_repo(tmp_path, VENV_OK, tracked_data=True)
    result = _run(main, tmp_path, "ui", "sess")
    assert result.returncode == 0, result.stderr
    clone = tmp_path / "work" / "myrepo-ui"
    assert (clone / "data").is_dir() and not (clone / "data").is_symlink()
    assert (clone / "data" / "raw" / ".gitkeep").exists()
    assert "not linking" in result.stdout
    exclude = clone / ".git" / "info" / "exclude"
    assert not exclude.exists() or "/data" not in exclude.read_text()


def test_second_run_is_idempotent(tmp_path: Path) -> None:
    main = _make_repo(tmp_path, VENV_OK)
    assert _run(main, tmp_path, "ui", "sess").returncode == 0
    again = _run(main, tmp_path, "ui", "sess")
    assert again.returncode == 0, again.stderr
    assert _registered(tmp_path) == ["sess ~/work/myrepo-ui"]


def test_venv_failure_is_not_fatal(tmp_path: Path) -> None:
    main = _make_repo(tmp_path, VENV_FAIL)
    result = _run(main, tmp_path, "ui", "sess")
    assert result.returncode == 0
    assert "boom" in result.stderr
    assert "make venv failed" in result.stderr
    assert _registered(tmp_path) == ["sess ~/work/myrepo-ui"]


def test_missing_venv_target_is_skipped(tmp_path: Path) -> None:
    main = _make_repo(tmp_path, "all:\n\t@true\n")
    result = _run(main, tmp_path, "ui", "sess")
    assert result.returncode == 0
    assert "no venv target" in result.stderr


def test_stale_session_for_another_dir_fails_without_changing_the_file(
    tmp_path: Path,
) -> None:
    main = _make_repo(tmp_path, VENV_OK)
    registry = tmp_path / "tmux-projects"
    registry.write_text("sess ~/gone/old-worktree\n")
    result = _run(main, tmp_path, "ui", "sess")
    assert result.returncode == 1
    assert "already registered" in result.stderr
    assert registry.read_text() == "sess ~/gone/old-worktree\n"


@pytest.mark.parametrize("suffix", [".x", "a b", "a/b", ""])
def test_rejects_bad_suffix(tmp_path: Path, suffix: str) -> None:
    main = _make_repo(tmp_path, VENV_OK)
    assert _run(main, tmp_path, suffix).returncode == 2


@pytest.mark.parametrize("session", ["-x", "a.b"])
def test_rejects_bad_session_name(tmp_path: Path, session: str) -> None:
    main = _make_repo(tmp_path, VENV_OK)
    assert _run(main, tmp_path, "ui", session).returncode == 2
