#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 [--dry-run] new_project_name [old_project_name]" >&2
  exit 1
}

DRY_RUN=false
if [ "${1:-}" = "--dry-run" ]; then
  DRY_RUN=true
  shift
fi

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
  usage
fi

NEW_NAME="$1"
OLD_NAME="${2:-your_project_name}"

if ! [[ "${NEW_NAME}" =~ ^[a-z][a-z0-9_]*$ ]]; then
  echo "error: '${NEW_NAME}' is not a valid Python identifier (must match ^[a-z][a-z0-9_]*\$)" >&2
  exit 1
fi

# Choose sed -i syntax depending on platform (GNU vs BSD)
if sed --version >/dev/null 2>&1; then
  SED_INPLACE=(-i)
else
  SED_INPLACE=(-i "")
fi

# Files to rewrite in place. Excludes this script itself (so OLD_NAME below
# stays literal across repeated runs — see the idempotence check at the
# bottom), common lockfiles/build artifacts that should never be touched,
# and tests/test_repo_consistency.py: its
# test_env_example_reviewed_after_template_rename sentinel must stay
# "your_project_name" regardless of the new project name, or the blind sed
# below would rewrite the sentinel and the pyproject.toml name to the same
# string, making the check's skip guard trivially true forever.
FIND_FILES=(find . -type f
  \( -name "*.py" -o -name "*.rst" -o -name "*.md"
     -o -name "*.yml" -o -name "*.yaml" -o -name "*.txt"
     -o -name "Makefile" -o -name "Dockerfile"
     -o -name "*.cfg" -o -name "*.ini" -o -name "*.toml"
     -o -name "*.json" -o -name "*.sh" \)
  ! -path "*/.git/*"
  ! -path "*/*.egg-info/*"
  ! -path "*/node_modules/*"
  ! -path "*/.venv/*"
  ! -path "*/venv/*"
  ! -path "*/.mypy_cache/*"
  ! -path "*/.ruff_cache/*"
  ! -path "*/.pytest_cache/*"
  ! -path "*/dist/*"
  ! -path "*/build/*"
  ! -path "*/htmlcov/*"
  ! -name "rename_project.sh"
  ! -path "*/tests/test_repo_consistency.py"
  ! -name "package-lock.json"
  ! -name "pnpm-lock.yaml"
  ! -name "uv.lock"
  ! -name "poetry.lock"
  ! -name "requirements.lock"
)

if [ "${DRY_RUN}" = true ]; then
  echo "Would rewrite '${OLD_NAME}' -> '${NEW_NAME}' in:"
  "${FIND_FILES[@]}" -print0 | xargs -0 grep -l "${OLD_NAME}" 2>/dev/null || true
  if [ -d "src/${OLD_NAME}" ] && [ ! -d "src/${NEW_NAME}" ]; then
    echo "Would move: src/${OLD_NAME} -> src/${NEW_NAME}"
  fi
  exit 0
fi

"${FIND_FILES[@]}" -print0 | xargs -0 sed "${SED_INPLACE[@]}" "s/${OLD_NAME}/${NEW_NAME}/g"

# Rename package directory under src/
if [ -d "src/${OLD_NAME}" ] && [ ! -d "src/${NEW_NAME}" ]; then
  mv "src/${OLD_NAME}" "src/${NEW_NAME}"
fi

echo "Renamed project from '${OLD_NAME}' to '${NEW_NAME}'."
echo
echo "Not renamed (do these by hand if needed):"
echo "  - env.example / .env contents"
echo "  - an already-created conda environment name"
echo "  - the GitHub remote / repository name"
