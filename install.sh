#!/bin/bash
# Sam YT Shorts Engine — install
#
# Symlinks the repo's skills into ~/.claude/skills/, then runs each skill's own
# install/sanity check.

set -e
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS=(sam-clips-engine edge-boil-reel)

echo "=== Sam YT Shorts Engine — install ==="
echo "  repo: $REPO"
mkdir -p "$HOME/.claude/skills"

for skill in "${SKILLS[@]}"; do
    SKILL_SRC="$REPO/$skill"
    SKILL_DEST="$HOME/.claude/skills/$skill"
    echo "  skill: $SKILL_DEST"

    # Replace existing skill link if it exists and points elsewhere
    if [ -L "$SKILL_DEST" ] || [ -e "$SKILL_DEST" ]; then
        current="$(readlink "$SKILL_DEST" 2>/dev/null || true)"
        if [ "$current" != "$SKILL_SRC" ]; then
            echo "    → replacing existing $SKILL_DEST"
            rm -rf "$SKILL_DEST"
            ln -s "$SKILL_SRC" "$SKILL_DEST"
        else
            echo "    → symlink already in place"
        fi
    else
        ln -s "$SKILL_SRC" "$SKILL_DEST"
        echo "    → symlinked"
    fi
done

for skill in "${SKILLS[@]}"; do
    echo
    echo "=== $skill — install sanity check ==="
    bash "$REPO/$skill/scripts/install.sh"
done
