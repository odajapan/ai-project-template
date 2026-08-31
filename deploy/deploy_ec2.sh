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
# TODO before this is real: set CONDA_ENV/SERVICE/PORT below and the health
# check path. If this project has more than one long-lived service, split
# this into one script per service rather than looping SERVICE/PORT here.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONDA_ENV="your_project_name"
SERVICE="your_project_name"
PORT=8000

BRANCH=""
if [ "${1:-}" = "--branch" ]; then
  BRANCH="${2:?--branch requires a branch name}"
fi

# shellcheck disable=SC1091
source "${HOME}/miniconda/etc/profile.d/conda.sh"
conda activate "${CONDA_ENV}"

cd "${REPO_ROOT}"

echo "==> Updating git checkout..."
git fetch origin --prune
if [ -n "${TESTED_SHA:-}" ]; then
  git checkout "${TESTED_SHA}"
else
  if [ -n "${BRANCH}" ]; then
    git checkout "${BRANCH}"
  fi
  git pull --ff-only
fi

echo "==> Updating Python dependencies..."
pip install -e . --quiet

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
exit 1
