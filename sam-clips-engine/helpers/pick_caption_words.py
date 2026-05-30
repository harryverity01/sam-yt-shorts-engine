#!/usr/bin/env python3
"""Pick which words in a clip transcript to emphasise with caption overlays.

Default heuristic (no LLM call — fast + deterministic):
  - Numbers ($30K, 150, 4K, 500K) — currency / quantities
  - Brand/person names from a small allow-list
  - Imperative verbs at the start of a clause (STOP, DON'T, LEARN)
  - The first 3 words of the clip (hook reinforcement)
  - The last word of the clip (payoff punch)

Target: 8-14 emphasised words per 30-45s clip (sparse = lands harder).

Input: Scribe word-level JSON for the clip range
Output: captions JSON for burn_captions.py — [{"t": <s>, "word": "WORD"}, ...]

Usage:
    pick_caption_words.py <clip_transcript.json> <clip_start_s> <clip_end_s> [-o captions.json]
"""
import argparse, json, re, sys
from pathlib import Path

# Recognisable allow-list — uppercase forms read better
BRANDS = {"stripe", "instagram", "ig", "youtube", "tiktok", "manychat", "chatgpt",
          "claude", "openai", "anthropic", "calendly", "hilton", "tommy", "hugo",
          "soho", "william", "brown", "naval", "hormozi", "rockefeller", "tony",
          "robbins", "elon", "musk", "rogan", "lukins", "danielle", "buffett", "greene"}

IMPERATIVES = {"stop", "don't", "dont", "never", "always", "imagine", "remember",
               "learn", "watch", "listen", "look", "think", "do", "stop"}

# Filler words to NEVER emphasise even if they fit a rule
SKIP = {"i", "a", "the", "and", "or", "but", "so", "is", "was", "to", "of", "in",
        "on", "at", "for", "with", "from", "by", "as", "if", "it", "that", "this",
        "you", "your", "we", "they", "be", "are", "have", "had", "has"}



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

def is_number(word: str) -> bool:
    """Money, percentages, or any token with a digit."""
    clean = word.strip("$£€%,.")
    return bool(re.search(r"\d", word)) or clean.lower().endswith(("k", "m", "b"))


def normalise(word: str) -> str:
    """Normalise word for matching (lowercase, strip punctuation)."""
    return re.sub(r"[^\w']", "", word).lower()


def pick(transcript_words: list, clip_start: float, clip_end: float,
         max_caps: int = 12) -> list:
    """Walk the transcript and return [{"t": rel_s, "word": "WORD"}, ...].

    Times are RELATIVE to clip_start so they're ready for burn_captions.py.
    """
    # Filter words inside the clip range
    in_clip = [w for w in transcript_words
               if w.get("start", 0) >= clip_start - 0.01
               and w.get("end", w.get("start", 0)) <= clip_end + 0.01]
    if not in_clip:
        return []

    picks = []
    n = len(in_clip)
    seen_words = set()

    for i, w in enumerate(in_clip):
        text = w.get("text", w.get("word", "")).strip()
        if not text: continue
        norm = normalise(text)
        if norm in SKIP: continue

        reason = None
        if i < 3:
            reason = "hook"
        elif i == n - 1:
            reason = "payoff"
        elif is_number(text):
            reason = "number"
        elif norm in BRANDS:
            reason = "brand"
        elif norm in IMPERATIVES and i > 0 and normalise(in_clip[i - 1].get("text", "")) in {".", "?", "!", ""}:
            reason = "imperative"

        if reason and norm not in seen_words:
            seen_words.add(norm)
            picks.append({
                "t": round(w["start"] - clip_start, 3),
                "word": text.upper().strip(".,!?;:"),
                "reason": reason,
            })

    # Cap at max — keep the most "important" (hook + payoff are mandatory, then numbers, brands, imperatives)
    if len(picks) > max_caps:
        priority = {"hook": 0, "payoff": 1, "number": 2, "brand": 3, "imperative": 4}
        picks.sort(key=lambda p: (priority.get(p["reason"], 9), p["t"]))
        picks = picks[:max_caps]
        picks.sort(key=lambda p: p["t"])

    return picks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript_json", type=Path,
                    help="Scribe word-level JSON (full source transcript)")
    ap.add_argument("clip_start", type=float)
    ap.add_argument("clip_end", type=float)
    ap.add_argument("--max-caps", type=int, default=12)
    ap.add_argument("-o", "--out", type=Path)
    args = ap.parse_args()

    data = json.load(open(args.transcript_json))
    # Scribe transcript shape: data["words"] = [{"text": "...", "start": s, "end": s, "type": "word"}]
    words = data.get("words") or data.get("word_timestamps") or []
    words = [w for w in words if w.get("type", "word") == "word"]

    picks = pick(words, args.clip_start, args.clip_end, args.max_caps)
    out = args.out or Path(f"captions_{args.clip_start:.0f}_{args.clip_end:.0f}.json")
    json.dump(picks, open(out, "w"), indent=2)
    print(f"✓ {len(picks)} caption words → {out}")
    for p in picks:
        print(f"  [{p['t']:>5.2f}s]  {p['word']:<20} ({p['reason']})")


if __name__ == "__main__":
    main()
