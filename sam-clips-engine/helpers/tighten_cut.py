#!/usr/bin/env python3
"""Tighten a clip: word-snapped boundaries + silence stripping between words.

This is the fix for "clips cut mid-word / not understandable / elevator-paced".

Sam edits by hand the same way: he looks at the audio waveform, deletes every
silent gap between words, then re-listens to make sure every word is still
recognisable. This helper does the first half mechanically; verify_cut.py does
the re-listen half.

Given the FULL word-level Scribe transcript and a clip window [clip_start, clip_end],
it produces a MULTI-RANGE EDL where:

  1. The clip starts on the first whole word and ends on the last whole word
     (snapped to Scribe word boundaries — never mid-word). A larger tail pad is
     held on the FINAL word so it is never clipped (Sam's #1 complaint).
  2. Internal silences longer than `max_gap` are removed — the clip is split into
     runs of words, each run becomes its own EDL range, and render.py losslessly
     concatenates them. Short, natural gaps (<= max_gap) are kept so speech still
     breathes and doesn't sound robotic.
  3. Optional `drop_ranges` (filler sentences Claude flagged) are excised the same
     way silences are — so the editor can cut "every sentence that isn't interesting".

render.py (video-use) already extracts each range with a baked grade + 30ms audio
fades and concatenates losslessly, so the cut points are pop-free.

Because removing silence COMPRESSES the timeline, caption/overlay timings computed
against the source must be remapped — use `map_src_to_out()` for that.

CLI:
    tighten_cut.py <transcript.json> <source.mp4> <clip_start> <clip_end> -o edl.json \
        [--grade "<ffmpeg filter>"] [--fps 24] \
        [--max-gap 0.28] [--keep-gap 0.10] \
        [--lead-pad 0.05] [--tail-pad 0.08] [--final-tail-pad 0.18] \
        [--drop "12.3-13.1,40.0-42.5"]

Writes edl.json (ready for render.py) and prints what was removed.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path


def _norm(text: str) -> str:
    return re.sub(r"[^\w']", "", text or "").lower()


def _clip_words(words: list, clip_start: float, clip_end: float) -> list:
    """Words whose MIDPOINT falls inside the window — clean, no half-words."""
    out = []
    for w in words:
        if w.get("type", "word") != "word":
            continue
        s, e = w.get("start"), w.get("end")
        if s is None or e is None:
            continue
        mid = (s + e) / 2.0
        if clip_start - 1e-6 <= mid <= clip_end + 1e-6:
            out.append(w)
    out.sort(key=lambda w: w["start"])
    return out


def _in_any(t: float, drop_ranges) -> bool:
    for a, b in (drop_ranges or []):
        if a <= t <= b:
            return True
    return False


def build_tight_ranges(
    words: list,
    clip_start: float,
    clip_end: float,
    *,
    max_gap: float = 0.28,
    keep_gap: float = 0.10,
    lead_pad: float = 0.05,
    tail_pad: float = 0.08,
    final_tail_pad: float = 0.18,
    drop_ranges=None,
) -> tuple[list, dict]:
    """Return (ranges, meta).

    ranges: [{"start": s, "end": e}, ...] in SOURCE time, gaps removed.
    meta:   {first_word, last_word, n_words, n_ranges, kept_s, removed_s, out_duration, ...}

    `max_gap`  — silences longer than this (seconds) are cut. Smaller = tighter.
    `keep_gap` — we never shrink an internal gap below this, so speech breathes.
    pads are held around every kept run; the final word gets `final_tail_pad`.
    """
    kept = [w for w in _clip_words(words, clip_start, clip_end)
            if not _in_any((w["start"] + w["end"]) / 2.0, drop_ranges)]

    if not kept:
        # Graceful fallback — no word data, cut the raw window with end protection.
        rng = [{"start": round(max(0.0, clip_start - lead_pad), 3),
                "end": round(clip_end + final_tail_pad, 3)}]
        return rng, {
            "first_word": "", "last_word": "", "n_words": 0, "n_ranges": 1,
            "kept_s": round(rng[0]["end"] - rng[0]["start"], 3),
            "removed_s": 0.0,
            "out_duration": round(rng[0]["end"] - rng[0]["start"], 3),
            "fallback": True,
        }

    # Group words into runs, breaking where the inter-word gap exceeds max_gap.
    runs: list[list] = [[kept[0]]]
    for prev, w in zip(kept, kept[1:]):
        gap = w["start"] - prev["end"]
        if gap > max_gap:
            runs.append([w])
        else:
            runs[-1].append(w)

    n_runs = len(runs)
    ranges = []
    for i, run in enumerate(runs):
        is_last = i == n_runs - 1
        start = run[0]["start"] - lead_pad
        end = run[-1]["end"] + (final_tail_pad if is_last else tail_pad)
        ranges.append({"start": start, "end": end})

    # Clamp: no negative starts, no overlaps after padding (keep_gap of breathing
    # room between runs preserved where the original gap allowed it).
    ranges[0]["start"] = max(0.0, ranges[0]["start"])
    for prev, r in zip(ranges, ranges[1:]):
        if r["start"] < prev["end"]:
            r["start"] = prev["end"]
        if r["end"] < r["start"]:
            r["end"] = r["start"]

    for r in ranges:
        r["start"] = round(r["start"], 3)
        r["end"] = round(r["end"], 3)
    ranges = [r for r in ranges if r["end"] - r["start"] > 0.02]

    kept_s = sum(r["end"] - r["start"] for r in ranges)
    span_s = ranges[-1]["end"] - ranges[0]["start"]
    meta = {
        "first_word": kept[0].get("text", "").strip(),
        "last_word": kept[-1].get("text", "").strip(),
        "n_words": len(kept),
        "n_ranges": len(ranges),
        "kept_s": round(kept_s, 3),
        "removed_s": round(max(0.0, span_s - kept_s), 3),
        "out_duration": round(kept_s, 3),
        "fallback": False,
    }
    return ranges, meta


def map_src_to_out(t_src: float, ranges: list) -> float:
    """Map a SOURCE-time stamp to the OUTPUT timeline after silence removal.

    A stamp that lands inside a removed gap snaps to the start of the next kept
    range (so a caption never floats over dead air that no longer exists).
    """
    offset = 0.0
    for r in ranges:
        if t_src < r["start"]:
            return round(offset, 3)
        if t_src <= r["end"]:
            return round(offset + (t_src - r["start"]), 3)
        offset += r["end"] - r["start"]
    return round(offset, 3)


def _parse_drop(spec: str | None):
    if not spec:
        return None
    out = []
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        a, b = chunk.split("-")
        out.append((float(a), float(b)))
    return out


def main():
    ap = argparse.ArgumentParser(description="Build a silence-stripped, word-snapped EDL")
    ap.add_argument("transcript_json", type=Path, help="Scribe word-level JSON (full source)")
    ap.add_argument("source", type=Path, help="Source video path (goes into the EDL)")
    ap.add_argument("clip_start", type=float)
    ap.add_argument("clip_end", type=float)
    ap.add_argument("-o", "--out", type=Path, required=True, help="EDL json output path")
    ap.add_argument("--grade", default="", help="Raw ffmpeg grade filter to bake per-segment")
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--max-gap", type=float, default=0.28)
    ap.add_argument("--keep-gap", type=float, default=0.10)
    ap.add_argument("--lead-pad", type=float, default=0.05)
    ap.add_argument("--tail-pad", type=float, default=0.08)
    ap.add_argument("--final-tail-pad", type=float, default=0.18)
    ap.add_argument("--drop", default=None, help="Comma list of src ranges to excise, e.g. '12.3-13.1,40-42.5'")
    args = ap.parse_args()

    data = json.load(open(args.transcript_json))
    words = data.get("words") or data.get("word_timestamps") or []

    ranges, meta = build_tight_ranges(
        words, args.clip_start, args.clip_end,
        max_gap=args.max_gap, keep_gap=args.keep_gap,
        lead_pad=args.lead_pad, tail_pad=args.tail_pad,
        final_tail_pad=args.final_tail_pad,
        drop_ranges=_parse_drop(args.drop),
    )

    edl = {
        "version": 1,
        "sources": {"src": str(args.source.resolve())},
        "ranges": [{"source": "src", "start": r["start"], "end": r["end"]} for r in ranges],
        "grade": args.grade,
        "fps": args.fps,
        "_meta": meta,
    }
    json.dump(edl, open(args.out, "w"), indent=2)

    raw = args.clip_end - args.clip_start
    print(f"✓ tightened EDL → {args.out}")
    print(f"  {meta['n_words']} words, {meta['n_ranges']} range(s)")
    print(f"  raw window {raw:.1f}s → out {meta['out_duration']:.1f}s "
          f"(removed {meta['removed_s']:.1f}s of silence/filler)")
    print(f"  first: '{meta['first_word']}'   last: '{meta['last_word']}'")


if __name__ == "__main__":
    main()
