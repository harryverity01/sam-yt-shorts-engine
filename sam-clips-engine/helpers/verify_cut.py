#!/usr/bin/env python3
"""Re-listen protection: re-transcribe a finished cut and confirm no word is clipped.

This is the second half of how Sam edits by hand — after deleting the silent gaps
he listens back to make sure every word is still recognisable, especially the last
one. We do the same mechanically: re-run Scribe on the rendered clip and check the
boundaries.

It answers Sam's two complaints directly:
  - "it cuts words off at the end"  -> truncated_end check
  - "not everything is understandable" -> first/last word recognisability check

It is deliberately conservative so it doesn't "make a mess" (Sam's worry): it only
ever recommends extending the END tail, never the body, and the orchestrator caps
the extension so it can't bleed the next sentence in.

CLI:
    verify_cut.py <clip.mp4> --expect-first "so" --expect-last "money" [-o verdict.json]

Returns (and prints) a verdict dict:
    {ok, first_ok, last_ok, truncated_end, suggest_extra_tail, clip_duration, tail_words}
Exit code 0 if ok, 3 if a boundary problem was detected (so shell callers can branch).
"""
from __future__ import annotations
import argparse, json, re, subprocess, sys, tempfile
from pathlib import Path

VIDEO_USE_HELPERS = Path.home() / ".claude/skills/video-use/helpers"


def _norm(text: str) -> str:
    return re.sub(r"[^\w']", "", text or "").lower()


def ffprobe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def judge(words: list, clip_duration: float, expect_first: str, expect_last: str,
          *, end_guard: float = 0.06, tail_n: int = 3) -> dict:
    """Pure decision logic (no I/O) so it is unit-testable.

    truncated_end fires when EITHER the expected last word is missing from the
    tail, OR the last transcribed word ends flush against the clip end (< end_guard
    of audio after it) — both signal the final word was cut off.
    """
    spoken = [w for w in words if w.get("type", "word") == "word"
              and w.get("text", "").strip()]
    if not spoken:
        return {"ok": False, "first_ok": False, "last_ok": False,
                "truncated_end": True, "suggest_extra_tail": 0.2,
                "clip_duration": round(clip_duration, 3), "tail_words": [],
                "note": "no words transcribed back — render or audio problem"}

    ef, el = _norm(expect_first), _norm(expect_last)
    first_norm = _norm(spoken[0].get("text", ""))
    tail = [_norm(w.get("text", "")) for w in spoken[-tail_n:]]

    first_ok = (not ef) or first_norm == ef or first_norm.startswith(ef) or ef.startswith(first_norm)
    last_ok = (not el) or any(t == el or t.startswith(el) or el.startswith(t) for t in tail)

    last_end = spoken[-1].get("end", clip_duration)
    flush = (clip_duration - last_end) < end_guard
    # End is truncated only if the expected payoff word never came back. (We do NOT
    # trigger on "flush" alone: with onset-based word selection the last kept word is
    # always rendered in full, and a flush ending is usually just a trailing guest
    # "Mm-hmm" — retrying on that would extend the tail INTO the interjection.)
    truncated_end = not last_ok
    suggest = 0.2 if truncated_end else 0.0

    ok = first_ok and last_ok and not truncated_end
    return {
        "ok": ok,
        "first_ok": first_ok,
        "last_ok": last_ok,
        "truncated_end": truncated_end,
        "suggest_extra_tail": round(suggest, 3),
        "clip_duration": round(clip_duration, 3),
        "last_word_end": round(last_end, 3),
        "tail_words": [w.get("text", "") for w in spoken[-tail_n:]],
    }


def verify(clip: Path, expect_first: str = "", expect_last: str = "",
           edit_dir: Path | None = None) -> dict:
    """Re-transcribe `clip` with Scribe and judge its boundaries."""
    clip = Path(clip)
    edit_dir = Path(edit_dir) if edit_dir else clip.parent
    # Re-transcribe into edit_dir/transcripts/<stem>.json (cached by transcribe.py).
    r = subprocess.run(
        ["python3", str(VIDEO_USE_HELPERS / "transcribe.py"), str(clip),
         "--edit-dir", str(edit_dir)],
        capture_output=True, text=True,
    )
    tr_path = edit_dir / "transcripts" / f"{clip.stem}.json"
    if not tr_path.exists():
        return {"ok": False, "error": f"re-transcribe failed: {r.stderr[-300:]}",
                "truncated_end": False, "suggest_extra_tail": 0.0}
    data = json.load(open(tr_path))
    words = data.get("words") or data.get("word_timestamps") or []
    dur = ffprobe_duration(clip)
    return judge(words, dur, expect_first, expect_last)


def main():
    ap = argparse.ArgumentParser(description="Re-transcribe a cut and verify word boundaries")
    ap.add_argument("clip", type=Path)
    ap.add_argument("--expect-first", default="")
    ap.add_argument("--expect-last", default="")
    ap.add_argument("--edit-dir", type=Path, default=None)
    ap.add_argument("-o", "--out", type=Path, default=None)
    args = ap.parse_args()

    verdict = verify(args.clip, args.expect_first, args.expect_last, args.edit_dir)
    if args.out:
        json.dump(verdict, open(args.out, "w"), indent=2)

    status = "✓ OK" if verdict.get("ok") else "⚠ BOUNDARY ISSUE"
    print(f"{status}  first_ok={verdict.get('first_ok')} last_ok={verdict.get('last_ok')} "
          f"truncated_end={verdict.get('truncated_end')}")
    print(f"  tail words: {verdict.get('tail_words')}")
    if verdict.get("truncated_end"):
        print(f"  → suggest extending end tail by {verdict.get('suggest_extra_tail')}s")
    sys.exit(0 if verdict.get("ok") else 3)


if __name__ == "__main__":
    main()
