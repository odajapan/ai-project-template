#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 new_project_name" >&2
  exit 1
fi

NEW_NAME="$1"
OLD_NAME="your_project_name"

# Choose sed -i syntax depending on platform (GNU vs BSD)
if sed --version >/dev/null 2>&1; then
  # GNU sed
  SED_INPLACE=(-i)
else
  # BSD / macOS sed
  SED_INPLACE=(-i "")
fi

# Replace in text files
# You can extend the find path/patterns as needed.
find . -type f \
  \( -name "*.py" -o -name "*.rst" -o -name "*.md" -o -name "*.yml" -o -name "*.yaml" -o -name "*.txt" -o -name "Makefile" -o -name "*.cfg" -o -name "*.ini" \) \
  ! -path "*/.git/*" \
	  ! -path "*/*.egg-info/*" \
  -print0 | xargs -0 sed "${SED_INPLACE[@]}" "s/${OLD_NAME}/${NEW_NAME}/g"

# Rename package directory under src/
if [ -d "src/${OLD_NAME}" ] && [ ! -d "src/${NEW_NAME}" ]; then
  mv "src/${OLD_NAME}" "src/${NEW_NAME}"
fi

echo "Renamed project from '${OLD_NAME}' to '${NEW_NAME}'."

