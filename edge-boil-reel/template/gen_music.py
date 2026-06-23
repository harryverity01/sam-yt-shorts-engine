#!/usr/bin/env python3
"""Generate the music bed for an edge-boil reel — or fall back to a bundled track.

Cloud-only, no external account *required*:
  - If ELEVENLABS_API_KEY is set (env or the repo .env), POST to ElevenLabs /v1/music
    for a bespoke documentary bed.
  - Otherwise (or on any API failure), copy a track from the repo ../music/ library so
    the pipeline always produces something.

Usage (run from your work dir):
  python3 ../template/gen_music.py --seconds 35 --out soundtrack.mp3
  python3 ../template/gen_music.py --seconds 35 --out soundtrack.mp3 --prompt "..."   # full override
  python3 ../template/gen_music.py --seconds 35 --out soundtrack.mp3 --fallback "Varation 1 strings.mp3"

The key is YOUR OWN (bills your ElevenLabs account). Nothing here is committed.
"""
import argparse, os, shutil, sys, urllib.request, urllib.error
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]   # edge-boil-reel/template -> edge-boil-reel -> repo root
MUSIC_DIR = REPO_ROOT / "music"


def load_key() -> str:
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if key:
        return key
    env = REPO_ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line.startswith("ELEVENLABS_API_KEY=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def default_prompt(seconds: int) -> str:
    # The documentary-tension recipe from SKILL.md. Tune per reel via --prompt.
    return (
        "Investigative documentary tension instrumental. Subtle typewriter clicks as the "
        "percussion gimmick. Steady driving rhythm around 100 BPM with a clear beat to cut "
        "visuals to. Building intensity in clear 5-second sections, rising into a final punchy "
        "resolving hit. Instrumental only, no vocals, mixed to sit under a male voiceover. "
        f"About {seconds} seconds long."
    )


def fallback(out: str, name: str | None) -> int:
    if not MUSIC_DIR.exists():
        print(f"no ../music/ library at {MUSIC_DIR} and no API key — cannot produce music", file=sys.stderr)
        return 1
    tracks = sorted(MUSIC_DIR.glob("*.mp3"))
    if not tracks:
        print(f"../music/ has no .mp3 tracks — cannot produce music", file=sys.stderr)
        return 1
    pick = MUSIC_DIR / name if name else tracks[0]
    if not pick.exists():
        print(f"fallback '{name}' not found; using {tracks[0].name}", file=sys.stderr)
        pick = tracks[0]
    shutil.copyfile(pick, out)
    print(f"fallback: copied library track '{pick.name}' -> {out}")
    print("  (note: bundled tracks are general-purpose; a bespoke ElevenLabs bed suits this format better)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=int, default=35, help="bed length target (reel duration + ~3s)")
    ap.add_argument("--out", default="soundtrack.mp3")
    ap.add_argument("--prompt", default=None, help="full prompt override")
    ap.add_argument("--fallback", default=None, help="specific ../music/ filename to use if no API key")
    args = ap.parse_args()

    key = load_key()
    if not key:
        print("ELEVENLABS_API_KEY not set (env or repo .env) — using the bundled library.")
        return fallback(args.out, args.fallback)

    prompt = args.prompt or default_prompt(args.seconds)
    body = ('{"prompt": %s, "music_length_ms": %d}' % (
        _json_str(prompt), max(10000, args.seconds * 1000))).encode()
    url = "https://api.elevenlabs.io/v1/music?output_format=mp3_44100_192"
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"xi-api-key": key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = r.read()
        Path(args.out).write_bytes(data)
        print(f"ElevenLabs music -> {args.out} ({len(data)//1024} KB)")
        return 0
    except urllib.error.HTTPError as e:
        print(f"ElevenLabs /v1/music failed: HTTP {e.code} {e.read()[:200]!r}", file=sys.stderr)
    except Exception as e:
        print(f"ElevenLabs /v1/music failed: {e}", file=sys.stderr)
    print("falling back to the bundled library.", file=sys.stderr)
    return fallback(args.out, args.fallback)


def _json_str(s: str) -> str:
    import json
    return json.dumps(s)


if __name__ == "__main__":
    raise SystemExit(main())
