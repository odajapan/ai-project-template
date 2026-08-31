#!/usr/bin/env bash
# Deploy this service (repeatable). Run on the deploy host:
#
#   bash deploy/deploy_ec2.sh                  # pull the current branch and deploy
#   bash deploy/deploy_ec2.sh --branch main    # switch branches first, then deploy
#   TESTED_SHA=<sha> bash deploy/deploy_ec2.sh # check out that exact commit
#
# Normally not run by hand: merging to main (via GitHub Actions,
# .github/workflows/deploy.yml) runs this from a self-hosted runner on the
# deploy host itself, with TESTED_SHA pinned to the commit CI just passed --
# so a push landing on main after CI finishes is never deployed ahead of its
# own CI run. Runner setup: deploy/install_github_runner.sh.
#
# See docs/EC2_DEPLOY.md for the full runbook.
#
# TODO before this is real: set CONDA_ENV/SERVICE/PORT/EXTRAS below and the
# health check path. If this project has more than one long-lived service,
# split this into one script per service rather than looping SERVICE/PORT
# here.

set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
CONDA_ENV="your_project_name"
SERVICE="your_project_name"
PORT=8000
# Extras this service needs at runtime, matching the canonical set in the
# Makefile / CI (e.g. "claude" if it uses ClaudeClient). Empty installs
# the bare package only.
EXTRAS=""

BRANCH=""
if [ "${1:-}" = "--branch" ]; then
  BRANCH="${2:?--branch requires a branch name}"
fi

cd "${REPO_ROOT}"

# About to `git checkout` this repo, which rewrites tracked files in place
# -- including this script. Bash reads a running script incrementally from
# disk, so if this file's own content differs between what's checked out
# now and the target commit, mutating it out from under the still-running
# process can execute a corrupted splice of old and new content. Re-exec
# from a throwaway copy first so the rest of this run reads from a file
# nothing else will touch. DEPLOY_EC2_PINNED (exported) marks that this
# has already happened, so the re-exec'd copy doesn't loop.
if [ -z "${DEPLOY_EC2_PINNED:-}" ]; then
  PINNED_COPY="$(mktemp)"
  cp "${BASH_SOURCE[0]}" "${PINNED_COPY}"
  export REPO_ROOT DEPLOY_EC2_PINNED=1
  # `exec` replaces this process outright, so an EXIT trap set here would
  # never fire -- clean up the copy from inside the re-exec'd process
  # instead (unlinking a file a process is currently executing from is
  # safe; the inode stays around until it exits).
  if [ -n "${BRANCH}" ]; then
    exec bash "${PINNED_COPY}" --branch "${BRANCH}"
  else
    exec bash "${PINNED_COPY}"
  fi
else
  trap 'rm -f "${BASH_SOURCE[0]}"' EXIT
fi

# shellcheck disable=SC1091
source "${HOME}/miniconda/etc/profile.d/conda.sh"
conda activate "${CONDA_ENV}"

echo "==> Updating git checkout..."
PREV_SHA="$(git rev-parse HEAD)"
git fetch origin --prune
if [ -n "${TESTED_SHA:-}" ]; then
  git checkout "${TESTED_SHA}"
else
  if [ -n "${BRANCH}" ]; then
    git checkout "${BRANCH}"
  elif ! git symbolic-ref -q HEAD >/dev/null; then
    # Detached HEAD left over from a prior TESTED_SHA deploy -- `git pull`
    # below requires a branch checked out first.
    git checkout main
  fi
  git pull --ff-only
fi

echo "==> Updating Python dependencies..."
pip install -e ".${EXTRAS:+[$EXTRAS]}" --quiet

# echo "==> Building frontend..."
# ( cd web && pnpm install --frozen-lockfile && pnpm build )

echo "==> Restarting ${SERVICE}..."
sudo systemctl restart "${SERVICE}"

echo "==> Health check..."
for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1; then
    echo "Deployed: http://$(hostname -I | awk '{print $1}'):${PORT}/"
    exit 0
  fi
  sleep 2
done

echo "Health check failed. Recent logs:" >&2
journalctl -u "${SERVICE}" -n 50 --no-pager >&2 || true

if [ "$(git rev-parse HEAD)" != "${PREV_SHA}" ]; then
  echo "==> Rolling back to ${PREV_SHA}..." >&2
  git checkout "${PREV_SHA}"
  pip install -e ".${EXTRAS:+[$EXTRAS]}" --quiet
  sudo systemctl restart "${SERVICE}"
fi

exit 1
