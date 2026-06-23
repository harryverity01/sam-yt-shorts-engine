#!/bin/bash
# Encode rendered frames -> finished reel(s). Runs in the cloud off this repo only.
#
# Usage (run from your work dir, after `render.py full`):
#   ./template/finish.sh [--frames frames_out] [--music soundtrack.mp3] \
#                        [--duration 32] [--fps 30] [--name reel] [--out finished]
#
# Produces:
#   <out>/<name>-master-silent.mp4   (always)
#   <out>/<name>-with-music.mp4      (only if --music given and the file exists)
#
# ffmpeg comes from the imageio-ffmpeg wheel (no system install) — scripts/install.sh
# adds it. The agent running the session hands the finished .mp4 back to you in chat;
# nothing is uploaded anywhere.
set -e

FRAMES="frames_out"
MUSIC=""
DURATION="32"
FPS="30"
NAME="reel"
OUT="finished"

while [ $# -gt 0 ]; do
  case "$1" in
    --frames)   FRAMES="$2"; shift 2;;
    --music)    MUSIC="$2"; shift 2;;
    --duration) DURATION="$2"; shift 2;;
    --fps)      FPS="$2"; shift 2;;
    --name)     NAME="$2"; shift 2;;
    --out)      OUT="$2"; shift 2;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

FFMPEG="$(python3 -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')"
mkdir -p "$OUT"

if [ -z "$(ls -A "$FRAMES"/*.jpg 2>/dev/null)" ]; then
  echo "no frames found in $FRAMES/ — run: python3 template/render.py full $FPS $DURATION" >&2
  exit 1
fi

echo "=== silent master ==="
"$FFMPEG" -y -framerate "$FPS" -i "$FRAMES/%05d.jpg" \
  -c:v libx264 -preset slow -crf 19 -pix_fmt yuv420p -movflags +faststart \
  "$OUT/$NAME-master-silent.mp4"

if [ -n "$MUSIC" ] && [ -f "$MUSIC" ]; then
  # fade the bed out over the last 1.6s; hold music under the VO at 0.85
  FADE_ST="$(python3 -c "print(max(0, float($DURATION) - 1.6))")"
  echo "=== with music ($MUSIC) ==="
  "$FFMPEG" -y -framerate "$FPS" -i "$FRAMES/%05d.jpg" -i "$MUSIC" \
    -filter_complex "[1:a]atrim=0:$DURATION,afade=t=out:st=$FADE_ST:d=1.6,volume=0.85[a]" \
    -map 0:v -map "[a]" \
    -c:v libx264 -preset slow -crf 19 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart \
    "$OUT/$NAME-with-music.mp4"
else
  [ -n "$MUSIC" ] && echo "music file '$MUSIC' not found — skipping music version" >&2
fi

echo
ls -la "$OUT"/$NAME-*.mp4
