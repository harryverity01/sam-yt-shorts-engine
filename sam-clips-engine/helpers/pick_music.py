#!/usr/bin/env python3
"""Music picker for Sam clips.

Provider order (best → fallback):
  1. Suno  — modern, produced beds (fixes the "elevator music" complaint). Used
     when a SUNO_API_KEY is available. Async generate + poll + download.
  2. ElevenLabs — bespoke per-clip generation if Suno isn't configured/fails.
  3. Library — Sam's cleared tracks, trimmed to length, if both gen paths fail.

Mood is classified from the transcript and mapped to a prompt seed. The seeds are
deliberately NOT "corporate boardroom" — Sam's shorts are Hormozi-style and need
forward motion (subtle modern beat, warm, motivational), just no vocals so they
sit under his voice.

Keys are read from (in order): env var → a secrets dir configured in
brand_assets.json (music.suno_secret / EL via video-use .env) → video-use .env.
On Sam's standalone machine, set SUNO_API_KEY / ELEVENLABS_API_KEY in env or .env.

Usage:
    pick_music.py --clip-transcript <words.json> --clip-end 35 --duration 35 [-o track.mp3]
    pick_music.py ... --library-only        # skip all generation
    pick_music.py ... --provider suno|elevenlabs|library
"""
import argparse, json, os, random, subprocess, sys, time, urllib.request, urllib.error
from pathlib import Path

DEFAULT_BRAND_ASSETS = Path(__file__).parent.parent / "brand_assets.json"


def _resolve_relative_paths(cfg, brand_assets_path):
    """Resolve '../x' (relative to brand_assets.json) and '~/x' path values so the
    same code runs on any machine. Absolute paths pass through untouched."""
    base = Path(brand_assets_path).resolve().parent
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


MOOD_KEYWORDS = {
    "proof":      ["i made", "i closed", "$", "k in", "made $", "closed", "client", "results"],
    "origin":     ["i started", "back when", "used to", "years ago", "remember when", "i was"],
    "contrarian": ["everyone tells", "most people", "they say", "wrong", "lie", "myth", "actually"],
    "how-to":     ["here's how", "step by step", "first you", "the way", "system", "process"],
    "case-study": ["my client", "this client", "worked with", "helped him", "we built"],
}

# De-"elevator"-ed seeds: modern, motivational, subtle beat, NO vocals, sits under VO.
MOOD_PROMPTS = {
    "proof":      "modern motivational lo-fi hip-hop, warm Rhodes keys, crisp subtle boom-bap beat, confident forward momentum, instrumental, no vocals, mixed to sit under a spoken voiceover",
    "origin":     "cinematic lo-fi with soft piano motif and warm sub bass, hopeful and nostalgic but moving forward, light tasteful drums, instrumental, no vocals, sits under a voiceover",
    "contrarian": "tense modern trap-lite instrumental, muted plucks and ticking hats, intelligent and a little edgy, restrained, no vocals, designed to sit under a spoken voiceover",
    "how-to":     "clean modern lo-fi beat, bright plucks over warm pads, focused and motivational, light percussion, instrumental, no vocals, sits under a voiceover",
    "case-study": "uplifting lo-fi hip-hop, rising arpeggio and warm sub-bass, social-media-positive build, tasteful beat, instrumental, no vocals, sits under a voiceover",
}


def classify_mood(transcript_words: list, clip_start: float, clip_end: float) -> str:
    text = " ".join(w.get("text", "") for w in transcript_words
                    if clip_start - 0.01 <= w.get("start", 0) <= clip_end + 0.01).lower()
    scores = {mood: sum(text.count(k) for k in kws)
              for mood, kws in MOOD_KEYWORDS.items()}
    if max(scores.values(), default=0) == 0:
        return "how-to"
    return max(scores, key=scores.get)


# -------- key loading --------------------------------------------------------

def _read_first_file(dir_path: Path) -> str | None:
    if not dir_path or not dir_path.exists():
        return None
    for f in sorted(dir_path.iterdir()):
        if f.is_file():
            v = f.read_text().strip()
            if v:
                return v.strip().strip('"\'')
    return None


def load_key(env_name: str, cfg: dict, cfg_secret_key: str) -> str | None:
    """env var → secrets dir from brand_assets.json → video-use .env."""
    v = os.environ.get(env_name)
    if v:
        return v.strip()
    # secrets dir configured per-machine in brand_assets.json (music.<cfg_secret_key>)
    sd = (cfg.get("music") or {}).get(cfg_secret_key)
    if sd:
        v = _read_first_file(Path(sd).expanduser())
        if v:
            return v
    # video-use .env (where ELEVENLABS_API_KEY usually lives)
    env_path = Path.home() / ".claude/skills/video-use/.env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith(f"{env_name}="):
                return line.split("=", 1)[1].strip().strip('"\'')
    return None


# -------- Suno ---------------------------------------------------------------

def try_suno_music(prompt: str, duration_s: float, out_path: Path, cfg: dict) -> bool:
    """Generate an instrumental bed via a Suno API provider, poll, download, trim.

    Defaults target the sunoapi.org v1 shape (generate → poll record-info). Override
    base/endpoints/model via env (SUNO_API_BASE, SUNO_MODEL) or brand_assets.json
    `music.suno_*` if you use a different provider. Falls back gracefully on any error.
    """
    api_key = load_key("SUNO_API_KEY", cfg, "suno_secret")
    if not api_key:
        return False
    mcfg = cfg.get("music") or {}
    base = (os.environ.get("SUNO_API_BASE") or mcfg.get("suno_base")
            or "https://api.sunoapi.org").rstrip("/")
    model = os.environ.get("SUNO_MODEL") or mcfg.get("suno_model") or "V4"
    gen_url = base + (mcfg.get("suno_generate_path") or "/api/v1/generate")
    poll_url = base + (mcfg.get("suno_poll_path") or "/api/v1/generate/record-info")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def _post(url, payload):
        req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                     headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())

    def _get(url):
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())

    def _find_audio_url(obj):
        """Walk arbitrary JSON for the first http(s) audio url."""
        found = []
        def walk(o):
            if isinstance(o, dict):
                for k, val in o.items():
                    if isinstance(val, str) and val.startswith("http") and \
                       (val.endswith((".mp3", ".m4a", ".wav")) or "audio" in k.lower()):
                        found.append(val)
                    else:
                        walk(val)
            elif isinstance(o, list):
                for it in o:
                    walk(it)
        walk(obj)
        return found[0] if found else None

    try:
        payload = {
            "prompt": prompt,
            "instrumental": True,
            "customMode": False,
            "model": model,
            "callBackUrl": mcfg.get("suno_callback", ""),
        }
        resp = _post(gen_url, payload)
        # task id lives under data.taskId / taskId / id depending on provider
        data = resp.get("data") if isinstance(resp, dict) else None
        task_id = None
        for cand in (data, resp):
            if isinstance(cand, dict):
                task_id = cand.get("taskId") or cand.get("task_id") or cand.get("id")
                if task_id:
                    break
        if not task_id:
            print(f"⚠ Suno: no task id in response — falling back ({str(resp)[:160]})", file=sys.stderr)
            return False

        audio_url = None
        for _ in range(40):  # up to ~4 min
            time.sleep(6)
            rec = _get(f"{poll_url}?taskId={task_id}")
            audio_url = _find_audio_url(rec)
            if audio_url:
                break
        if not audio_url:
            print("⚠ Suno: timed out waiting for audio — falling back", file=sys.stderr)
            return False

        raw = out_path.with_suffix(".suno_raw")
        urllib.request.urlretrieve(audio_url, raw)
        # Trim to clip length + 2s safety tail (the mix is -shortest, so any extra is dropped)
        cmd = ["ffmpeg", "-y", "-i", str(raw), "-t", str(duration_s + 2.0),
               "-c:a", "libmp3lame", "-b:a", "192k", str(out_path)]
        subprocess.run(cmd, capture_output=True, check=True)
        raw.unlink(missing_ok=True)
        print(f"✓ Suno music generated → {out_path}")
        return True
    except Exception as e:
        print(f"⚠ Suno failed: {e} — falling back", file=sys.stderr)
        return False


# -------- ElevenLabs ---------------------------------------------------------

def try_elevenlabs_music(prompt: str, duration_s: float, out_path: Path, cfg: dict) -> bool:
    api_key = load_key("ELEVENLABS_API_KEY", cfg, "elevenlabs_secret")
    if not api_key:
        print("⚠ no ELEVENLABS_API_KEY — falling back to library", file=sys.stderr)
        return False
    duration_ms = int((duration_s + 2.0) * 1000)
    body = json.dumps({"prompt": prompt, "music_length_ms": duration_ms}).encode()
    req = urllib.request.Request(
        "https://api.elevenlabs.io/v1/music", data=body,
        headers={"xi-api-key": api_key, "Content-Type": "application/json",
                 "Accept": "audio/mpeg"})
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            audio = resp.read()
        out_path.write_bytes(audio)
        print(f"✓ ElevenLabs music generated ({len(audio) // 1024}KB) → {out_path}")
        return True
    except Exception as e:
        print(f"⚠ ElevenLabs failed: {e} — falling back to library", file=sys.stderr)
        return False


# -------- Library fallback ---------------------------------------------------

def pick_library_track(mood: str, cfg: dict) -> Path:
    library = Path(cfg["music_library"])
    matched = [t for t in cfg["music_tracks"] if mood in t.get("moods", [])]
    pool = matched if matched else cfg["music_tracks"]
    pick = random.choice(pool)
    return library / pick["file"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clip-transcript", type=Path, required=True)
    ap.add_argument("--clip-start", type=float, default=0.0)
    ap.add_argument("--clip-end", type=float, required=True)
    ap.add_argument("--duration", type=float)
    ap.add_argument("--mood", choices=list(MOOD_PROMPTS.keys()))
    ap.add_argument("--provider", choices=["auto", "suno", "elevenlabs", "library"],
                    default="auto", help="Force a provider (default auto: suno→EL→library)")
    ap.add_argument("--library-only", action="store_true")
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("--brand-assets", type=Path, default=DEFAULT_BRAND_ASSETS)
    args = ap.parse_args()

    cfg = _resolve_relative_paths(json.load(open(args.brand_assets)), args.brand_assets)
    dur = args.duration or (args.clip_end - args.clip_start)

    data = json.load(open(args.clip_transcript))
    words = [w for w in (data.get("words") or data.get("word_timestamps") or [])
             if w.get("type", "word") == "word"]
    mood = args.mood or classify_mood(words, args.clip_start, args.clip_end)
    prompt = MOOD_PROMPTS[mood]
    print(f"  mood: {mood}")

    provider = "library" if args.library_only else args.provider
    if provider in ("auto", "suno") and try_suno_music(prompt, dur, args.out, cfg):
        return
    if provider in ("auto", "elevenlabs") and try_elevenlabs_music(prompt, dur, args.out, cfg):
        return

    # Library fallback
    track = pick_library_track(mood, cfg)
    cmd = ["ffmpeg", "-y", "-i", str(track), "-t", str(dur + 2.0),
           "-c:a", "libmp3lame", "-b:a", "192k", str(args.out)]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        sys.exit(f"❌ library track trim failed: {r.stderr.decode()[-300:]}")
    print(f"✓ library fallback ({track.name}) → {args.out}")


if __name__ == "__main__":
    main()
