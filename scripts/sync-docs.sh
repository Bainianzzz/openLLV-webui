#!/usr/bin/env sh
# Sync the openLLV docs/ directory into this repository.
#
# Requires the 'openllv' remote:
#   git remote add openllv https://github.com/glory-wan/openLLV.git

set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! git remote get-url openllv >/dev/null 2>&1; then
    echo "error: missing 'openllv' remote; run:" >&2
    echo "  git remote add openllv https://github.com/glory-wan/openLLV.git" >&2
    exit 1
fi

# Detect the remote's default branch (e.g. main / master) so the script keeps
# working even if the upstream default branch changes.
BRANCH="$(git ls-remote --symref openllv HEAD | awk '/^ref:/ { sub("refs/heads/", "", $2); print $2; exit }')"
if [ -z "$BRANCH" ]; then
    echo "error: could not determine the default branch of 'openllv'" >&2
    exit 1
fi

git fetch openllv "$BRANCH"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Archive entries carry the 'docs/' prefix, so extract into the temp root and
# mirror the result into docs/ (--delete removes files that no longer exist).
git archive "openllv/$BRANCH" docs | tar -x -C "$TMP"
rsync -a --delete "$TMP/docs/" docs/

echo "docs/ synced from openllv ($BRANCH)."
