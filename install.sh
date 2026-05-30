#!/bin/bash
# Sam YT Shorts Engine — install
#
# Symlinks sam-clips-engine into ~/.claude/skills/, then runs the skill's own
# install check.

set -e
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$REPO/sam-clips-engine"
SKILL_DEST="$HOME/.claude/skills/sam-clips-engine"

echo "=== Sam YT Shorts Engine — install ==="
echo "  repo:  $REPO"
echo "  skill: $SKILL_DEST"

mkdir -p "$HOME/.claude/skills"

# Replace existing skill link if it exists and points elsewhere
if [ -L "$SKILL_DEST" ] || [ -e "$SKILL_DEST" ]; then
    current="$(readlink "$SKILL_DEST" 2>/dev/null || true)"
    if [ "$current" != "$SKILL_SRC" ]; then
        echo "  → replacing existing $SKILL_DEST"
        rm -rf "$SKILL_DEST"
        ln -s "$SKILL_SRC" "$SKILL_DEST"
    else
        echo "  → symlink already in place"
    fi
else
    ln -s "$SKILL_SRC" "$SKILL_DEST"
    echo "  → symlinked"
fi

echo
echo "=== Running skill's install sanity check ==="
bash "$SKILL_SRC/scripts/install.sh"
