#!/usr/bin/env python3
"""B-roll picker — scans a clip transcript and picks overlays from the Sam brand library.

Strategy:
  1. Load brand_library/manifest.json — has 3 active concepts + 48 logos + 11 people
  2. Walk the clip transcript, looking for trigger words/phrases
  3. Match triggers to assets via a Sam-specific rules table
  4. Spread overlays across the clip — target 1 every 8–15s (matches viral cadence)
  5. ALWAYS end with handle_sameyeam_secrets lower-third in the last 2s

Input: clip_transcript.json (Scribe word-level, already clipped to the range)
       OR full transcript + clip_start + clip_end

Output: overlays.json — [{"file": "/abs/path/x.mov", "start_in_clip": 4.2, "duration": 3.0, "reason": "..."}, ...]

If a trigger fires but no matching asset exists, the reason field starts with "[MISSING]" —
flag to user, never invent assets.
"""
import argparse, json, re, sys
from pathlib import Path
from collections import defaultdict


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


# Trigger phrase → asset rules. Order matters — earlier rules win.
RULES = [
    # WILLIAM BROWN — intelligent pick (animated card vs villa wide)
    {"pattern": r"\bwilliam\s+brown\b|\bwill\s+brown\b",
     "asset": "william_brown_choice",   # special: pick based on context
     "reason": "William Brown mentioned"},

    # PEOPLE references → person photo from people/
    {"pattern": r"\bhormozi\b|\balex\s+hormozi\b",
     "asset": "people/hormozi.jpg", "reason": "Hormozi name-drop"},
    {"pattern": r"\bnaval\b|\bravikant\b",
     "asset": "people/naval_ravikant.jpg", "reason": "Naval name-drop"},
    {"pattern": r"\bbuffett\b|\bwarren\s+buffett\b",
     "asset": "people/warren_buffett.jpg", "reason": "Buffett name-drop"},
    {"pattern": r"\btony\s+robbins\b",
     "asset": "people/tony_robbins.jpg", "reason": "Tony Robbins name-drop"},
    {"pattern": r"\brockefeller\b",
     "asset": "people/rockefeller.jpg", "reason": "Rockefeller name-drop"},
    {"pattern": r"\bjoe\s+rogan\b|\brogan\b",
     "asset": "people/joe_rogan.jpg", "reason": "Rogan name-drop"},
    {"pattern": r"\belon\b|\bmusk\b",
     "asset": "people/elon_musk.jpg", "reason": "Elon name-drop"},
    {"pattern": r"\balan\s+watts\b",
     "asset": "people/alan_watts.png", "reason": "Alan Watts quote"},
    {"pattern": r"\brobert\s+greene\b",
     "asset": "people/robert_greene.jpg", "reason": "Robert Greene name-drop"},
    {"pattern": r"\bdanielle\b|\blukins\b",
     "asset": "people/danielle_lukins.png", "reason": "Danielle Lukins (podcast guest)"},
    {"pattern": r"\bpiers\s+morgan\b",
     "asset": "people/piers_morgan.jpg", "reason": "Piers Morgan name-drop"},

    # BRANDS → logos
    {"pattern": r"\bstripe\b",
     "asset": "logos/stripe_com_logo.png", "reason": "Stripe mentioned"},
    {"pattern": r"\binstagram\b|\big\b(?!\.)",
     "asset": "logos/instagram_com_logo.png", "reason": "Instagram mentioned"},
    {"pattern": r"\byoutube\b|\byt\b",
     "asset": "logos/youtube_com_logo.png", "reason": "YouTube mentioned"},
    {"pattern": r"\btiktok\b",
     "asset": "logos/tiktok_com_logo.png", "reason": "TikTok mentioned"},
    {"pattern": r"\bmanychat\b",
     "asset": "logos/manychat_com_logo.png", "reason": "ManyChat mentioned"},
    {"pattern": r"\bchatgpt\b|\bgpt\b|\bopenai\b",
     "asset": "logos/chatgpt_com_logo.png", "reason": "ChatGPT/OpenAI mentioned"},
    {"pattern": r"\bclaude\b|\banthropic\b",
     "asset": "logos/claude_ai_logo.png", "reason": "Claude/Anthropic mentioned"},
    {"pattern": r"\bcapcut\b",
     "asset": "logos/capcut_com_logo.png", "reason": "CapCut mentioned"},
    {"pattern": r"\blightroom\b",
     "asset": "logos/lightroom_adobe_com_logo.png", "reason": "Lightroom mentioned"},
    {"pattern": r"\bhilton\b",
     "asset": "logos/hilton_com_logo.png", "reason": "Hilton client name-drop"},
    {"pattern": r"\btommy\s+hilfiger\b|\btommy\b",
     "asset": "logos/tommy_com_logo.png", "reason": "Tommy Hilfiger client name-drop"},
    {"pattern": r"\bhugo\s+boss\b",
     "asset": "logos/fourseasons_com_logo.png", "reason": "Hugo Boss client (using FS placeholder)"},
    {"pattern": r"\bgohighlevel\b|\bhigh\s*level\b",
     "asset": "logos/gohighlevel_com_logo.png", "reason": "GHL mentioned"},
    {"pattern": r"\bcalendly\b",
     "asset": "concepts/sam_calendly_fully_booked.mov", "reason": "Calendly mentioned — fully booked card"},
    {"pattern": r"\bsoho\s+house\b|\bsoho\b",
     "asset": "logos/sohohouse_com_logo.png", "reason": "Soho House mentioned"},
    {"pattern": r"\bkajabi\b",
     "asset": "logos/kajabi_com_logo.png", "reason": "Kajabi mentioned"},
    {"pattern": r"\belevenlabs\b|\beleven\s+labs\b",
     "asset": "logos/elevenlabs_io_logo.png", "reason": "ElevenLabs mentioned"},

    # SAM-SPECIFIC NARRATIVE TRIGGERS
    {"pattern": r"\bfully\s+booked\b|\bbooked\s+out\b|\b150\s+calls?\b",
     "asset": "concepts/sam_calendly_fully_booked.mov",
     "reason": "Booking-flood narrative"},

    # COMMENT/DM CTA → IG comment highlight (parameterised — renders at runtime)
    # The picker captures the keyword (group 1) and writes a build instruction
    # rather than a static asset path. The orchestrator handles runtime rendering.
    {"pattern": r"\bcomment\s+['\"]?(\w{3,15})['\"]?",
     "asset": "RUNTIME:ig_comment",   # special marker — orchestrator handles
     "reason": "DM-trigger CTA — comment a word",
     "extract_keyword": True},

    # @sameyeam.secrets / IG profile reference → popup
    {"pattern": r"\bsameyeam\.secrets\b|\bmy\s+(instagram|ig|profile)\b",
     "asset": "concepts/sam_ig_popup.mov", "reason": "Sam IG profile reference"},
]


def text_of_window(words: list, start: float, end: float) -> str:
    """Concat text of all words in [start, end]."""
    return " ".join(w.get("text", "") for w in words
                    if start - 0.01 <= w.get("start", 0) <= end + 0.01).lower()


def first_match_time(words: list, pattern: re.Pattern, start: float, end: float) -> float | None:
    """Return the start time of the first word matching pattern, or None."""
    txt_running = ""
    for w in words:
        if w.get("start", 0) < start - 0.01: continue
        if w.get("start", 0) > end + 0.01: break
        token = w.get("text", "")
        # Check if appending this word completes the pattern
        candidate = (txt_running + " " + token).strip().lower()
        if pattern.search(candidate):
            return w.get("start")
        txt_running = candidate[-200:]  # rolling window
    return None


def pick(transcript_words: list, clip_start: float, clip_end: float,
         brand_lib_dir: Path, asset_paths: dict) -> list:
    """Return a list of overlay specs for this clip."""
    overlays = []
    used_times = []   # to enforce 8-15s spread

    # Walk rules in order
    for rule in RULES:
        pattern = re.compile(rule["pattern"], re.IGNORECASE)
        # Find first match in transcript
        full_text = text_of_window(transcript_words, clip_start, clip_end)
        if not pattern.search(full_text):
            continue

        # Get the timing of the match
        match_t = first_match_time(transcript_words, pattern, clip_start, clip_end)
        if match_t is None:
            continue
        rel_t = match_t - clip_start

        # Enforce 8s minimum spread between overlays
        if any(abs(rel_t - prev) < 8.0 for prev in used_times):
            continue

        # Resolve asset path
        asset_rel = rule["asset"]
        # Runtime-rendered templates (e.g. ig_comment with parameterised keyword)
        if asset_rel.startswith("RUNTIME:"):
            template_name = asset_rel.split(":", 1)[1]
            if template_name == "ig_comment" and rule.get("extract_keyword"):
                # Pull the keyword from the regex match
                full_text = text_of_window(transcript_words, clip_start, clip_end)
                m = re.search(rule["pattern"], full_text, re.IGNORECASE)
                if m and m.group(1):
                    keyword = m.group(1).upper()
                    overlays.append({
                        "start_in_clip": round(rel_t, 3),
                        "duration": 5.0,
                        "runtime_render": "ig_comment",
                        "runtime_params": {"keyword": keyword},
                        "asset_rel": f"concepts/ig_comment_{keyword.lower()}.mov",
                        "reason": f"DM-trigger CTA — comment '{keyword}'",
                    })
                    used_times.append(rel_t)
                    continue
            # Unknown runtime template — flag missing
            overlays.append({
                "start_in_clip": round(rel_t, 3),
                "duration": 3.0,
                "reason": f"[MISSING] runtime template {template_name} not wired up",
            })
            continue
        if asset_rel == "william_brown_choice":
            # Pick: stat-heavy clip → IG popup; relaxed clip → villa shot
            # Heuristic: count numbers in the clip
            num_count = sum(1 for w in transcript_words
                            if clip_start - 0.01 <= w.get("start", 0) <= clip_end + 0.01
                            and re.search(r"\d", w.get("text", "")))
            if num_count >= 2:
                # Stat-heavy → IG popup (more visual punch)
                asset_rel = "concepts/sam_ig_popup.mov"
                reason = "William Brown — stat-heavy clip, IG popup"
            else:
                # Note: villa shot would need to be added to brand_library/broll/
                asset_rel = "broll/william_brown_villa.mp4"
                reason = "William Brown — relaxed clip, villa wide"
        else:
            reason = rule["reason"]

        asset_path = brand_lib_dir / asset_rel
        if not asset_path.exists():
            overlays.append({
                "start_in_clip": round(rel_t, 3),
                "duration": 3.0,
                "asset_rel": asset_rel,
                "reason": f"[MISSING] {reason} (no asset at {asset_path})",
            })
            continue

        # Get asset duration (default 3.0 for .mov, 2.5 for .png)
        dur = 3.0
        if asset_rel.endswith((".png", ".jpg")):
            dur = 2.5

        overlays.append({
            "start_in_clip": round(rel_t, 3),
            "duration": dur,
            "asset_path": str(asset_path),
            "asset_rel": asset_rel,
            "reason": reason,
        })
        used_times.append(rel_t)

    # ALWAYS end with handle_sameyeam_secrets lower-third in last 2s
    handle_path = brand_lib_dir / "concepts/handle_sameyeam_secrets.mov"
    if handle_path.exists():
        clip_dur = clip_end - clip_start
        overlays.append({
            "start_in_clip": round(max(0, clip_dur - 3.0), 3),
            "duration": 3.0,
            "asset_path": str(handle_path),
            "asset_rel": "concepts/handle_sameyeam_secrets.mov",
            "reason": "End-of-clip handle plug",
        })

    overlays.sort(key=lambda o: o["start_in_clip"])
    return overlays


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript_json", type=Path,
                    help="Scribe word-level JSON (full source)")
    ap.add_argument("clip_start", type=float)
    ap.add_argument("clip_end", type=float)
    ap.add_argument("-o", "--out", type=Path)
    ap.add_argument("--brand-assets", type=Path, default=DEFAULT_BRAND_ASSETS)
    args = ap.parse_args()

    cfg = _resolve_relative_paths(_resolve_relative_paths(json.load(open(args.brand_assets)), Path(args.brand_assets).resolve()), Path(args.brand_assets).resolve() if not str(args.brand_assets).startswith("Path") else args.brand_assets)
    brand_lib = Path(cfg["brand_library"])

    data = json.load(open(args.transcript_json))
    words = data.get("words") or data.get("word_timestamps") or []
    words = [w for w in words if w.get("type", "word") == "word"]

    overlays = pick(words, args.clip_start, args.clip_end, brand_lib, cfg)
    out = args.out or Path(f"overlays_{args.clip_start:.0f}_{args.clip_end:.0f}.json")
    json.dump(overlays, open(out, "w"), indent=2)
    print(f"✓ {len(overlays)} overlays picked → {out}")
    for o in overlays:
        flag = "❌" if o.get("reason", "").startswith("[MISSING]") else "✓"
        print(f"  {flag} [{o['start_in_clip']:>5.2f}s +{o['duration']:.1f}s]  "
              f"{o.get('asset_rel', '?'):<50}  {o['reason']}")


if __name__ == "__main__":
    main()
