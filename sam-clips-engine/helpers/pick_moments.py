#!/usr/bin/env python3
"""Viral moment candidate generator.

This script DOES NOT rank clips — it generates candidate windows for Claude (running
this skill inside the Claude Code session) to score using the rubric in
`references/sam_audience.md`. No API keys, no SDK calls.

The orchestrator pauses after this step and hands the candidates over to Claude
(this session) to rank them. Claude writes the ranked output back to ranked_clips.json
and the orchestrator continues.

Input: takes_packed.md from video-use pack_transcripts.py (phrase-level transcript with
       [start-end] times).
Output: candidates.json — every valid 28–48s window, ready for ranking.

Usage:
    python3 pick_moments.py --transcript <takes_packed.md> [--target-length 35] -o candidates.json
"""
import argparse, json, re, sys
from pathlib import Path


def load_packed_transcript(packed_md_path: Path) -> list:
    """Parse takes_packed.md (phrase-level) into a list of phrases with [start-end] times."""
    text = packed_md_path.read_text()
    phrases = []
    for line in text.splitlines():
        # Match `  [001.23-005.67] S0 actual text here`
        m = re.match(r"\s*\[(\d+\.\d+)-(\d+\.\d+)\]\s+S\d+\s+(.+)", line)
        if m:
            phrases.append({
                "start": float(m.group(1)),
                "end": float(m.group(2)),
                "text": m.group(3).strip(),
            })
    return phrases


def generate_candidate_windows(phrases: list, target_len_s: float = 35.0,
                                 min_len_s: float = 28.0, max_len_s: float = 48.0,
                                 stride_phrases: int = 2) -> list:
    """Slide a window over phrases, grouping consecutive ones into ~target_len_s candidates.

    Drop candidates that start mid-thought (lowercase first letter or starts with
    'and/but/so/because/which/that/to').
    """
    drop_starts = {"and", "but", "so", "because", "which", "that", "to"}
    candidates = []
    n = len(phrases)
    for i in range(0, n, stride_phrases):
        start = phrases[i]["start"]
        first_text = phrases[i]["text"]
        first_word = first_text.split()[0] if first_text else ""
        if first_word and first_word[0].islower():
            continue
        if first_word.lower().rstrip(",.") in drop_starts:
            continue
        # Extend until target length
        end = start
        chunks = []
        for j in range(i, n):
            chunks.append(phrases[j])
            end = phrases[j]["end"]
            if end - start >= target_len_s:
                break
        dur = end - start
        if dur < min_len_s or dur > max_len_s:
            continue
        candidates.append({
            "id": len(candidates),
            "start": round(start, 2),
            "end": round(end, 2),
            "duration": round(dur, 2),
            "text": " ".join(c["text"] for c in chunks),
        })
    return candidates


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript", type=Path, required=True,
                    help="takes_packed.md from video-use pack_transcripts.py")
    ap.add_argument("--target-length", type=float, default=35.0)
    ap.add_argument("--min-length", type=float, default=28.0)
    ap.add_argument("--max-length", type=float, default=48.0)
    ap.add_argument("-o", "--out", type=Path, required=True)
    args = ap.parse_args()

    if not args.transcript.exists():
        sys.exit(f"❌ transcript not found: {args.transcript}")

    phrases = load_packed_transcript(args.transcript)
    print(f"  {len(phrases)} phrases loaded")

    candidates = generate_candidate_windows(
        phrases,
        target_len_s=args.target_length,
        min_len_s=args.min_length,
        max_len_s=args.max_length,
    )
    print(f"  {len(candidates)} candidate windows generated "
          f"({args.min_length:.0f}–{args.max_length:.0f}s, target {args.target_length:.0f}s)")

    if not candidates:
        sys.exit("❌ no valid candidate windows — check transcript / length params")

    json.dump(candidates, open(args.out, "w"), indent=2)
    print(f"✓ candidates → {args.out}")
    print(f"\n  ⏸  HANDOFF: Claude (this session) ranks these candidates using the rubric")
    print(f"     in references/sam_audience.md and writes the top N to ranked_clips.json.")
    print(f"     See orchestrator.py:rank_handoff() for the exact protocol.")


if __name__ == "__main__":
    main()
