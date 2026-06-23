#!/bin/bash
# Edge-Boil Reel — install + sanity check.
#
# Run once per fresh cloud container before building a reel. Everything it installs is
# cloud-friendly: no system packages, no local machine needed.
set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$SKILL_DIR/.." && pwd)"

echo "=== Edge-Boil Reel — install check ==="
echo "  skill: $SKILL_DIR"

PIP="pip3 install --break-system-packages -q"

# 1. Python render deps
echo -n "  python playwright ... "
python3 -c "import playwright" 2>/dev/null && echo "ok" || { echo "installing"; $PIP playwright; }

echo -n "  python Pillow ... "
python3 -c "from PIL import Image" 2>/dev/null && echo "ok" || { echo "installing"; $PIP Pillow; }

echo -n "  python imageio-ffmpeg (bundled ffmpeg) ... "
python3 -c "import imageio_ffmpeg" 2>/dev/null && echo "ok" || { echo "installing"; $PIP imageio-ffmpeg; }

# 2. Chromium for Playwright (the renderer). ~150MB download, once per container.
echo -n "  chromium for Playwright ... "
if python3 -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(); b.close(); p.stop()" 2>/dev/null; then
    echo "ok"
else
    echo "installing"
    python3 -m playwright install chromium
fi

# 3. Verify the bundled ffmpeg binary actually runs
echo -n "  ffmpeg (via imageio-ffmpeg) ... "
FFMPEG="$(python3 -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())' 2>/dev/null || true)"
if [ -n "$FFMPEG" ] && "$FFMPEG" -version >/dev/null 2>&1; then
    echo "ok ($FFMPEG)"
else
    echo "FAILED — check imageio-ffmpeg install"; exit 1
fi

# 4. ElevenLabs key (OPTIONAL — only for the music bed). Falls back to ../music/ if unset.
echo -n "  ELEVENLABS_API_KEY (optional, music) ... "
if [ -n "$ELEVENLABS_API_KEY" ]; then
    echo "ok (env var)"
elif [ -f "$REPO_ROOT/.env" ] && grep -q "^ELEVENLABS_API_KEY=..*" "$REPO_ROOT/.env" && ! grep -q "your_elevenlabs_key_here" "$REPO_ROOT/.env"; then
    echo "ok (repo .env)"
else
    echo "not set — music will fall back to the bundled ../music/ library (fine)"
fi

echo
echo "=== Install check done ==="
echo "Next:"
echo "  mkdir -p $SKILL_DIR/work/<project> && cd \$_"
echo "  cp $SKILL_DIR/template/stage.html ."
echo "  python3 $SKILL_DIR/template/fetch_fonts.py"
echo "  # source assets, edit stage.html, then:"
echo "  python3 $SKILL_DIR/template/render.py preview 2 6 12 20"
echo "  python3 $SKILL_DIR/template/render.py full 30 32"
echo "  python3 $SKILL_DIR/template/gen_music.py --seconds 35 --out soundtrack.mp3"
echo "  $SKILL_DIR/template/finish.sh --music soundtrack.mp3 --duration 32 --name <project>"
