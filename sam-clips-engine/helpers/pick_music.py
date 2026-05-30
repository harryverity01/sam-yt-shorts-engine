#!/usr/bin/env python3
"""Music picker for Sam clips.

Strategy:
  1. Classify clip mood from transcript (proof/origin/contrarian/how-to/case-study)
  2. Try ElevenLabs music generation — per-clip bespoke track
  3. Fallback: pick from Sam's 4-track library based on mood

Usage:
    pick_music.py --clip-transcript <words.json> --duration 35 [-o track.mp3]
"""
import argparse, json, os, random, subprocess, sys, urllib.request
from pathlib import Path


def _resolve_relative_paths(cfg: dict, brand_assets_path: Path) -> dict:
    """Resolve any '../path' values in cfg as relative to brand_assets.json's parent."""
    base = brand_assets_path.parent
    def walk(o):
        if isinstance(o, dict):
            return {k: walk(v) for k, v in o.items()}
        if isinstance(o, list):
            return [walk(x) for x in o]
        if isinstance(o, str) and o.startswith("../"):
            return str((base / o).resolve())
        if isinstance(o, str) and o.startswith("~/"):
            return str(Path(o).expanduser())
        return o
    return walk(cfg)

DEFAULT_BRAND_ASSETS = Path(__file__).parent.parent / "brand_assets.json"


MOOD_KEYWORDS = {
    "proof":      ["i made", "i closed", "$", "k in", "made $", "closed", "client", "results"],
    "origin":     ["i started", "back when", "used to", "years ago", "remember when", "i was"],
    "contrarian": ["everyone tells", "most people", "they say", "wrong", "lie", "myth", "actually"],
    "how-to":     ["here's how", "step by step", "first you", "the way", "system", "process"],
    "case-study": ["my client", "this client", "worked with", "helped him", "we built"],
}

MOOD_PROMPTS = {
    "proof":      "warm electric piano + soft sub bass, optimistic build, confident cinematic tech, no vocals, no prominent drums, designed to sit under a YouTube voiceover, lofi production polish",
    "origin":     "soft pad swell, single piano motif, nostalgic warmth, hopeful, no vocals, no prominent drums, designed to sit under a YouTube voiceover, lofi production polish",
    "contrarian": "low pulse + ticking, slight tension, intelligent restrained, cinematic tech, no vocals, no prominent drums, designed to sit under a YouTube voiceover, lofi production polish",
    "how-to":     "thoughtful boardroom, strings pad + light pulse, restrained intelligent, no vocals, no prominent drums, designed to sit under a YouTube voiceover, lofi production polish",
    "case-study": "rising arpeggio + sub-bass drop, social-media-positive, hopeful build to subtle drop, no vocals, no prominent drums, designed to sit under a YouTube voiceover, lofi production polish",
}


def classify_mood(transcript_words: list, clip_start: float, clip_end: float) -> str:
    """Score each mood by keyword count; return highest. Default 'how-to'."""
    text = " ".join(w.get("text", "") for w in transcript_words
                    if clip_start - 0.01 <= w.get("start", 0) <= clip_end + 0.01).lower()
    scores = {mood: sum(text.count(k) for k in kws)
              for mood, kws in MOOD_KEYWORDS.items()}
    if max(scores.values(), default=0) == 0:
        return "how-to"
    return max(scores, key=scores.get)


def try_elevenlabs_music(prompt: str, duration_s: float, out_path: Path) -> bool:
    """Call ElevenLabs Music API. Returns True on success.

    Reads API key from ELEVENLABS_API_KEY env or .env at video-use repo root.
    """
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        env_path = Path.home() / ".claude/skills/video-use/.env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("ELEVENLABS_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"\'')
                    break
    if not api_key:
        print("⚠ no ELEVENLABS_API_KEY — falling back to library", file=sys.stderr)
        return False

    # Pad the duration slightly so end card doesn't sit on a sudden cut
    duration_ms = int((duration_s + 2.0) * 1000)
    body = json.dumps({
        "prompt": prompt,
        "music_length_ms": duration_ms,
    }).encode()
    req = urllib.request.Request(
        "https://api.elevenlabs.io/v1/music",
        data=body,
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            audio = resp.read()
        out_path.write_bytes(audio)
        print(f"✓ ElevenLabs music generated ({len(audio) // 1024}KB) → {out_path}")
        return True
    except Exception as e:
        print(f"⚠ ElevenLabs failed: {e} — falling back to library", file=sys.stderr)
        return False


def pick_library_track(mood: str, cfg: dict) -> Path:
    """Pick from Sam's 4-track library, preferring mood-matched tracks."""
    library = Path(cfg["music_library"])
    matched = [t for t in cfg["music_tracks"] if mood in t.get("moods", [])]
    pool = matched if matched else cfg["music_tracks"]
    pick = random.choice(pool)
    return library / pick["file"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clip-transcript", type=Path, required=True,
                    help="Word-level Scribe JSON")
    ap.add_argument("--clip-start", type=float, default=0.0)
    ap.add_argument("--clip-end", type=float, required=True)
    ap.add_argument("--duration", type=float,
                    help="Override duration (default: clip_end - clip_start)")
    ap.add_argument("--mood", choices=list(MOOD_PROMPTS.keys()),
                    help="Force a mood instead of auto-classifying")
    ap.add_argument("--library-only", action="store_true",
                    help="Skip ElevenLabs, pick from library only")
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("--brand-assets", type=Path, default=DEFAULT_BRAND_ASSETS)
    args = ap.parse_args()

    cfg = _resolve_relative_paths(_resolve_relative_paths(json.load(open(args.brand_assets)), Path(args.brand_assets).resolve()), Path(args.brand_assets).resolve() if not str(args.brand_assets).startswith("Path") else args.brand_assets)
    dur = args.duration or (args.clip_end - args.clip_start)

    data = json.load(open(args.clip_transcript))
    words = data.get("words") or data.get("word_timestamps") or []
    words = [w for w in words if w.get("type", "word") == "word"]
    mood = args.mood or classify_mood(words, args.clip_start, args.clip_end)
    print(f"  mood: {mood}")

    if not args.library_only:
        prompt = MOOD_PROMPTS[mood]
        if try_elevenlabs_music(prompt, dur, args.out):
            return

    # Fallback
    track = pick_library_track(mood, cfg)
    # Copy/trim the library track to out at exact duration
    cmd = [
        "ffmpeg", "-y", "-i", str(track),
        "-t", str(dur + 2.0),
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(args.out),
    ]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        sys.exit(f"❌ library track trim failed: {r.stderr.decode()[-300:]}")
    print(f"✓ library fallback ({track.name}) → {args.out}")


if __name__ == "__main__":
    main()
