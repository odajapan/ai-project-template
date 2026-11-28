"""The two scripts under .claude/hooks run on every edit and every session
start and exit 0 silently by design, so nothing else notices when they stop
doing their job. Needs bash and git; no network — a fake `git` on PATH
answers `ls-remote` and hands everything else to the real git."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOKS = REPO_ROOT / ".claude" / "hooks"
FORMAT_HOOK = HOOKS / "format-edited-file.sh"
DRIFT_HOOK = HOOKS / "template-drift-check.sh"
BASELINE = "a" * 40
MOVED_HEAD = "b" * 40

pytestmark = pytest.mark.skipif(
    shutil.which("bash") is None or shutil.which("git") is None,
    reason="bash/git missing",
)


def _fake_tool(path: Path, log: Path) -> None:
    # Appends its argv as one line per call; the hook under test is the only
    # thing that ever calls it, so the log is the hook's exact ruff command.
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'#!/bin/sh\necho "$@" >> "{log}"\n')
    path.chmod(0o755)


def _run_format_hook(project: Path, file: Path) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project)}
    return subprocess.run(
        ["bash", str(FORMAT_HOOK)],
        input=json.dumps({"tool_input": {"file_path": str(file)}}),
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _project(tmp_path: Path) -> tuple[Path, Path]:
    project = tmp_path / "project"
    (project / "src").mkdir(parents=True)
    log = project / "ruff.log"
    _fake_tool(project / ".venv" / "bin" / "ruff", log)
    return project, log


def _logged(log: Path) -> list[list[str]]:
    if not log.exists():
        return []
    return [line.split() for line in log.read_text().splitlines()]


def test_format_hook_formats_with_the_project_ruff(tmp_path: Path) -> None:
    project, log = _project(tmp_path)
    target = project / "src" / "a.py"
    target.write_text("x=1\n")
    result = _run_format_hook(project, target)
    assert result.returncode == 0, result.stderr
    assert _logged(log) == [
        ["format", "--quiet", "--force-exclude", str(target.resolve())]
    ]


def test_format_hook_skips_files_outside_the_project(tmp_path: Path) -> None:
    # A session can edit another repo's file or a scratch file; that file's
    # formatter settings are not this project's.
    project, log = _project(tmp_path)
    outside = tmp_path / "elsewhere" / "b.py"
    outside.parent.mkdir()
    outside.write_text("y=2\n")
    assert _run_format_hook(project, outside).returncode == 0
    assert _logged(log) == []


def test_format_hook_compares_physical_paths(tmp_path: Path) -> None:
    # A symlinked checkout (or macOS /tmp -> /private/tmp) must still count as
    # inside the project, whichever spelling the payload or the env uses.
    project, log = _project(tmp_path)
    link = tmp_path / "link"
    link.symlink_to(project, target_is_directory=True)
    target = project / "src" / "c.py"
    target.write_text("z=3\n")
    assert _run_format_hook(link, target).returncode == 0
    assert _run_format_hook(project, link / "src" / "c.py").returncode == 0
    assert (
        _logged(log)
        == [["format", "--quiet", "--force-exclude", str(target.resolve())]] * 2
    )


def test_format_hook_uses_the_worktrees_own_ruff(tmp_path: Path) -> None:
    # .claude/worktrees/<name> is a separate checkout with its own .venv.
    project, main_log = _project(tmp_path)
    worktree = project / ".claude" / "worktrees" / "task"
    (worktree / "src").mkdir(parents=True)
    worktree_log = worktree / "ruff.log"
    _fake_tool(worktree / ".venv" / "bin" / "ruff", worktree_log)
    target = worktree / "src" / "d.py"
    target.write_text("w=4\n")
    assert _run_format_hook(project, target).returncode == 0
    assert _logged(main_log) == []
    assert _logged(worktree_log) == [
        ["format", "--quiet", "--force-exclude", str(target.resolve())]
    ]


def test_format_hook_ignores_non_python_and_missing_files(tmp_path: Path) -> None:
    project, log = _project(tmp_path)
    (project / "notes.md").write_text("# hi\n")
    assert _run_format_hook(project, project / "notes.md").returncode == 0
    assert _run_format_hook(project, project / "src" / "gone.py").returncode == 0
    assert _logged(log) == []


# --- template-drift-check.sh -------------------------------------------------


class _Drift:
    def __init__(self, tmp_path: Path) -> None:
        self.root = tmp_path / "proj"
        self.root.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        ini = self.root / ".claude" / "template-sync.ini"
        ini.parent.mkdir()
        ini.write_text(
            "[template]\n\trepo = org/template\n\tref = main\n"
            f"\tcommit = {BASELINE}\n\tsyncedAt = 2026-01-01\n"
        )
        self.stamp = self.root / ".git" / "template-sync-last-check"
        self.ls_remote_log = tmp_path / "ls-remote.log"
        fake_bin = tmp_path / "bin"
        fake_bin.mkdir()
        real_git = shutil.which("git")
        (fake_bin / "git").write_text(
            "#!/bin/sh\n"
            'if [ "$1" = ls-remote ]; then\n'
            f'  echo "$@" >> "{self.ls_remote_log}"\n'
            '  [ -n "${FAKE_LS_REMOTE_FAIL:-}" ] && exit 128\n'
            '  printf "%s\\trefs/heads/main\\n" "$FAKE_HEAD"\n'
            "  exit 0\n"
            "fi\n"
            f'exec "{real_git}" "$@"\n'
        )
        (fake_bin / "git").chmod(0o755)
        self.env = {
            **os.environ,
            "PATH": f"{fake_bin}:{os.environ['PATH']}",
            "CLAUDE_PROJECT_DIR": str(self.root),
            "FAKE_HEAD": MOVED_HEAD,
        }
        self.env.pop("FAKE_LS_REMOTE_FAIL", None)

    def run(self, *args: str, unreachable: bool = False) -> str:
        env = dict(self.env)
        if unreachable:
            env["FAKE_LS_REMOTE_FAIL"] = "1"
        result = subprocess.run(
            ["bash", str(DRIFT_HOOK), *args],
            cwd=self.root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert result.stderr == ""
        return result.stdout

    def ls_remote_calls(self) -> int:
        log = self.ls_remote_log
        return len(log.read_text().splitlines()) if log.exists() else 0


def test_drift_check_reports_drift_and_stays_quiet_when_current(tmp_path: Path) -> None:
    drift = _Drift(tmp_path)
    assert "Template drift: org/template@main" in drift.run("--force")
    drift.env["FAKE_HEAD"] = BASELINE
    assert drift.run("--force") == ""


def test_drift_check_treats_a_junk_stamp_as_never_checked(tmp_path: Path) -> None:
    # A truncated or hand-edited stamp used to break the `$((now - last))`
    # arithmetic, and the hook then failed on every session start.
    drift = _Drift(tmp_path)
    drift.stamp.write_text("not-a-number\n")
    assert "Template drift" in drift.run()
    assert drift.stamp.read_text().strip().isdigit()


def test_drift_check_stamps_the_attempt_not_the_success(tmp_path: Path) -> None:
    # GitHub unreachable (VPN down, IP allow list): one try per throttle
    # window, not one per session start.
    drift = _Drift(tmp_path)
    assert drift.run(unreachable=True) == ""
    assert drift.stamp.exists()
    assert abs(int(drift.stamp.read_text()) - time.time()) < 60
    assert drift.run(unreachable=True) == ""
    assert drift.run() == ""
    assert drift.ls_remote_calls() == 1


def test_drift_check_force_ignores_and_keeps_the_throttle(tmp_path: Path) -> None:
    drift = _Drift(tmp_path)
    assert "Template drift" in drift.run("--force")
    assert not drift.stamp.exists()
    drift.stamp.write_text(f"{int(time.time())}\n")
    before = drift.stamp.read_text()
    assert "Template drift" in drift.run("--force")
    assert drift.stamp.read_text() == before
    assert drift.run() == ""
    assert drift.ls_remote_calls() == 2
