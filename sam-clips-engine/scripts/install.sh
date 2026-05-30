#!/bin/bash
# Sam Clips Engine — install + sanity check
#
# Run this once on a new machine before invoking orchestrator.py
set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRAND_ASSETS="$SKILL_DIR/brand_assets.json"

echo "=== Sam Clips Engine — install check ==="

# 1. Python deps
echo -n "  python anthropic ... "
python3 -c "import anthropic" 2>/dev/null && echo "ok" || {
    echo "missing — installing"
    pip3 install --break-system-packages -q anthropic
}

echo -n "  python PIL ... "
python3 -c "from PIL import Image" 2>/dev/null && echo "ok" || {
    echo "missing — installing"
    pip3 install --break-system-packages -q Pillow
}

# 2. System tools
for cmd in ffmpeg ffprobe yt-dlp; do
    echo -n "  $cmd ... "
    command -v $cmd >/dev/null && echo "ok ($(which $cmd))" || echo "MISSING — install via brew install $cmd"
done

# 3. video-use dependency
VIDEO_USE="$HOME/.claude/skills/video-use/SKILL.md"
echo -n "  video-use skill ... "
[ -f "$VIDEO_USE" ] && echo "ok ($VIDEO_USE)" || {
    echo "MISSING — install video-use first (see https://github.com/...)"
    exit 1
}

# 4. API keys
echo -n "  ELEVENLABS_API_KEY ... "
if [ -n "$ELEVENLABS_API_KEY" ]; then
    echo "ok (env)"
elif [ -f "$HOME/.claude/skills/video-use/.env" ] && grep -q ELEVENLABS_API_KEY "$HOME/.claude/skills/video-use/.env"; then
    echo "ok (.env)"
else
    echo "MISSING — set ELEVENLABS_API_KEY env var or add to ~/.claude/skills/video-use/.env"
fi

echo "  ANTHROPIC_API_KEY ... not needed (skill runs inside Claude Code session, not via SDK)"

# 5. Sam asset paths from brand_assets.json (resolve ../ relative to the json file)
echo "  Sam asset paths:"
python3 -c "
import json, os
from pathlib import Path
ba = Path('$BRAND_ASSETS').resolve()
cfg = json.load(open(ba))
def resolve(p):
    if p.startswith('../'): return str((ba.parent / p).resolve())
    if p.startswith('~/'): return str(Path(p).expanduser())
    return p
for key in ['brand_library', 'music_library']:
    p = resolve(cfg[key])
    ok = os.path.exists(p)
    print(f'    {key}: {\"✓\" if ok else \"❌ MISSING\"}  {p}')
"

echo
echo "=== Install check done ==="
echo "Next: python3 $SKILL_DIR/orchestrator.py --input <video> --work-dir <out>"
