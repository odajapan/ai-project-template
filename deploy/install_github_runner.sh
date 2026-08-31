#!/usr/bin/env bash
# Install a GitHub Actions self-hosted runner on this deploy host for this
# repo (one-time, per host). .github/workflows/deploy.yml runs
# deploy_ec2.sh on this runner whenever main is merged.
#
# Usage (from your machine):
#   TOKEN=$(gh api -X POST \
#     /repos/<org>/<repo>/actions/runners/registration-token --jq .token)
#   ssh <deploy-host> \
#     'bash ~/path/to/<repo>/deploy/install_github_runner.sh' "$TOKEN"
#
# To deregister:
#   TOKEN=$(gh api -X POST .../actions/runners/remove-token --jq .token)
#   cd ~/actions-runner/your_project_name && sudo ./svc.sh uninstall && ./config.sh remove --token "$TOKEN"
#
# See docs/EC2_DEPLOY.md -- in particular, this step is manual and easy to
# skip: adding deploy.yml alone does nothing until a runner is actually
# registered and online.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNNER_VERSION="2.336.0"
# SHA-256 from the actions/runner release notes for actions-runner-linux-x64
# (bump this together with RUNNER_VERSION).
TARBALL_SHA256="04cf0be1aff4c3ec3554466c39124ca250e3effd8873bb7e8d68535aa9505d5d"
REPO_URL="$(git -C "${REPO_ROOT}" remote get-url origin | sed -E 's#\.git$##; s#^git@github\.com:#https://github.com/#')"
RUNNER_DIR="${HOME}/actions-runner/your_project_name"
RUNNER_NAME="your_project_name"
TOKEN="${1:?registration token required (see header comment)}"

# Running as root would put the runner (and its service) under /root
# instead of the intended user's home.
if [ "$(id -u)" -eq 0 ]; then
  echo "Do not run as root -- run as the user the runner should run as (e.g. ubuntu)." >&2
  exit 1
fi

if [ -f "${RUNNER_DIR}/.runner" ]; then
  echo "Runner already configured: ${RUNNER_DIR}" >&2
  exit 1
fi

mkdir -p "${RUNNER_DIR}"
cd "${RUNNER_DIR}"

echo "[1/3] Downloading runner v${RUNNER_VERSION}..."
TARBALL="actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
curl -fsSL -o "${TARBALL}" \
  "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${TARBALL}"
echo "${TARBALL_SHA256}  ${TARBALL}" | sha256sum --check --quiet
tar xzf "${TARBALL}"
rm "${TARBALL}"

echo "[2/3] Registering runner..."
./config.sh --unattended \
  --url "${REPO_URL}" \
  --token "${TOKEN}" \
  --name "${RUNNER_NAME}" \
  --replace

echo "[3/3] Installing as a systemd service..."
sudo ./svc.sh install "$(whoami)"
sudo ./svc.sh start
sudo ./svc.sh status

API_PATH="$(echo "${REPO_URL}" | sed -E 's#https://github.com/##')"
echo "Done. Verify from your machine: gh api /repos/${API_PATH}/actions/runners"
