#!/usr/bin/env python3
"""Sam Clips Engine — orchestrator.

End-to-end pipeline: long-form video → N finished 1080×1920 vertical clips.

Steps (in order):
  1. Ingest (yt-dlp or local file) + verify_sync
  2. Transcribe via video-use (Scribe word-level, cached)
  3. Pack transcript into takes_packed.md
  4. Rank viral moments (pick_moments.py)
  5. For each picked clip (parallel):
     a. Pick b-roll overlays from brand library (pick_broll.py)
     b. Pick caption words (pick_caption_words.py)
     c. Build per-clip EDL + render via video-use render.py (cut + overlay)
     d. Burn captions (burn_captions.py)
     e. Pick + mix music (pick_music.py)
     f. Finalise — NO end card (Sam removed it)
  6. Output: finished/01_<slug>.mp4 … finished/NN_<slug>.mp4

Usage:
    python3 orchestrator.py \\
        --input "<file or YouTube URL>" \\
        --work-dir "<output directory>" \\
        --num-clips 12

Run from anywhere — the helpers all reference brand_assets.json for paths.
"""
import argparse, json, os, re, subprocess, sys, shutil, time
from pathlib import Path

SKILL_DIR = Path(__file__).parent
HELPERS = SKILL_DIR / "helpers"
BRAND_ASSETS = SKILL_DIR / "brand_assets.json"

# video-use helper paths
VIDEO_USE_HELPERS = Path.home() / ".claude/skills/video-use/helpers"

# Our own helpers as importable modules (pure logic: tighten + verify).
sys.path.insert(0, str(HELPERS))
import tighten_cut  # noqa: E402  silence-strip + word-snap + time remap
import verify_cut   # noqa: E402  re-transcribe end protection


def _resolve_relative_paths(cfg, brand_assets_path):
    """Resolve '../x' (relative to brand_assets.json) and '~/x' path values so the
    SAME code runs on any machine — Harry's absolute paths pass through untouched,
    Sam's repo-relative '../brand_library' paths resolve to the repo. No-op otherwise."""
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


def load_cfg():
    return _resolve_relative_paths(json.load(open(BRAND_ASSETS)), BRAND_ASSETS)


def run(cmd, check=True, capture=False):
    """Run a command. If check, exit on failure. If capture, return stdout."""
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    r = subprocess.run([str(c) for c in cmd],
                       capture_output=capture, text=capture)
    if check and r.returncode != 0:
        if capture:
            print(r.stdout, file=sys.stderr)
            print(r.stderr, file=sys.stderr)
        sys.exit(f"❌ command failed: {cmd[0]}")
    return r.stdout if capture else None


def step1_ingest(args, work_dir: Path) -> Path:
    """Download YouTube URL or copy local file to work_dir/source.mp4."""
    src = Path(work_dir) / "source.mp4"
    if src.exists():
        print(f"  source cached at {src}")
        return src

    if args.input.startswith("http"):
        # yt-dlp
        run(["yt-dlp", "-f", "best[height<=1080]/best",
             "-o", str(src), args.input])
    else:
        # Local file — symlink, don't copy (faster, saves disk)
        in_path = Path(args.input).resolve()
        if not in_path.exists():
            sys.exit(f"❌ input file not found: {in_path}")
        if not src.exists():
            src.symlink_to(in_path)

    # Verify sync
    run(["python3", str(VIDEO_USE_HELPERS / "verify_sync.py"), str(src)])
    return src


def step2_transcribe(source: Path, work_dir: Path) -> Path:
    """Scribe transcription via video-use, cached. Returns transcript.json path."""
    transcripts_dir = work_dir / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    expected = transcripts_dir / f"{source.stem}.json"
    if expected.exists():
        print(f"  transcript cached at {expected}")
        return expected
    run(["python3", str(VIDEO_USE_HELPERS / "transcribe.py"), str(source)])
    # video-use writes to <edit>/transcripts/<name>.json by default
    return expected


def step3_pack(work_dir: Path) -> Path:
    """Pack transcripts into takes_packed.md."""
    packed = work_dir / "takes_packed.md"
    if packed.exists():
        return packed
    run(["python3", str(VIDEO_USE_HELPERS / "pack_transcripts.py"),
         "--edit-dir", str(work_dir)])
    return packed


def step4_generate_candidates(packed: Path, work_dir: Path,
                                target_length: float) -> Path:
    """Generate candidate windows (NO ranking — Claude in this session does that).

    The ranking step is a HANDOFF point. The skill does not call any API. Instead,
    Claude (running this skill inside the user's Claude Code subscription) reads
    the candidates + the rubric in references/sam_audience.md, scores each, and
    writes ranked_clips.json. This script just pauses and reminds.
    """
    out = work_dir / "candidates.json"
    run(["python3", str(HELPERS / "pick_moments.py"),
         "--transcript", str(packed),
         "--target-length", str(target_length),
         "-o", str(out)])
    return out


def step4_check_ranked(work_dir: Path, num_clips: int) -> Path:
    """Verify Claude has written ranked_clips.json. If not, exit with the handoff message."""
    ranked = work_dir / "ranked_clips.json"
    if ranked.exists():
        return ranked
    candidates_path = work_dir / "candidates.json"
    n_cands = len(json.load(open(candidates_path))) if candidates_path.exists() else "?"
    print(f"""
╭─────────────────────────────────────────────────────────────────╮
│  ⏸  PAUSED — RANKING HANDOFF                                    │
│                                                                  │
│  {n_cands} candidate clips written to:
│    {candidates_path}
│                                                                  │
│  Claude (you, running this skill): read candidates.json + the   │
│  Sam audience rubric in references/sam_audience.md. Score each  │
│  candidate. Write the top {num_clips:>2} to:                                  │
│    {ranked}
│                                                                  │
│  Schema for ranked_clips.json:                                  │
│    [{{"id": <int from candidates>, "start": <s>, "end": <s>,      │
│      "score": <int>, "beat": "<HOOK|STAT|STORY|HOW-TO|REVEAL>", │
│      "hook_preview": "<first 8 words>",                         │
│      "cuts": [[<s>,<s>]],  // OPTIONAL filler/repeat to excise   │
│      "reason": "<2-sentence why this is viral>"}}]                │
│                                                                  │
│  Rules (references/sam_audience.md): clips must be SAM-DOMINANT │
│  (mostly Sam talking, guest only a short interjection); open on │
│  the hook; every sentence interesting; no filler.              │
│                                                                  │
│  Then re-run orchestrator.py with the same args to continue.    │
╰─────────────────────────────────────────────────────────────────╯
""")
    sys.exit(2)


def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower()).strip("_")
    return s[:40]


def step5_build_clip(idx: int, clip_data: dict, source: Path, transcript: Path,
                      work_dir: Path, args) -> Path | None:
    """Build a single finished clip. Returns output path or None on failure."""
    cfg = load_cfg()
    slug = slugify(clip_data.get("hook_preview", f"clip_{idx}"))
    clip_id = f"{idx:02d}_{slug}"
    clip_dir = work_dir / "clips" / clip_id
    clip_dir.mkdir(parents=True, exist_ok=True)

    start = clip_data["start"]
    end = clip_data["end"]
    duration = end - start

    print(f"\n=== CLIP {clip_id} ===  ({start:.2f}-{end:.2f}s, {duration:.1f}s)")
    print(f"  hook: {clip_data.get('hook_preview', '?')}")

    # 5a. Pick b-roll overlays (skipped with --no-broll — keep the clip clean, just
    # words on the speaker; logos/lower-thirds don't suit a tight talking-head crop)
    overlays_json = clip_dir / "overlays.json"
    if not args.no_broll:
        run(["python3", str(HELPERS / "pick_broll.py"),
             str(transcript), str(start), str(end), "-o", str(overlays_json)])

    # 5b. Pick caption words
    captions_json = clip_dir / "captions.json"
    run(["python3", str(HELPERS / "pick_caption_words.py"),
         str(transcript), str(start), str(end), "-o", str(captions_json)])

    # 5c. Precision cut — silence-stripped, word-snapped, MULTI-range EDL.
    # The fix for "cuts mid-word / elevator-paced": tighten_cut builds an EDL that
    # starts/ends on whole words and removes internal silences (Sam edits the same
    # way — delete the gaps between words). render.py extracts each range with the
    # grade + 30ms fades baked in and losslessly concatenates them.
    # Sam color grade — locked from build_short.py / the 14 shipped shorts.
    SAM_GRADE = ("curves=red='0/0 0.5/0.53 1/1':blue='0/0 0.5/0.45 1/1',"
                 "eq=saturation=0.95:contrast=1.03:brightness=0.01")
    tdata = json.load(open(transcript))
    twords = tdata.get("words") or tdata.get("word_timestamps") or []
    drop_ranges = clip_data.get("cuts")  # optional [[s,e],...] of filler Claude flagged

    def _build_and_render(final_tail_pad: float):
        ranges, meta = tighten_cut.build_tight_ranges(
            twords, start, end,
            max_gap=args.max_gap, final_tail_pad=final_tail_pad,
            drop_ranges=[tuple(d) for d in drop_ranges] if drop_ranges else None,
        )
        edl = {
            "version": 1,
            "sources": {"src": str(source.resolve())},
            "ranges": [{"source": "src", "start": r["start"], "end": r["end"]} for r in ranges],
            "grade": SAM_GRADE,
            "fps": 25,
            "_meta": meta,
        }
        json.dump(edl, open(clip_dir / "edl.json", "w"), indent=2)
        cut_landscape = clip_dir / "cut_landscape.mp4"
        cut_landscape.unlink(missing_ok=True)
        # render.py caches per-segment extracts by index-based name; on a verify
        # retry the range ends change but names don't, so wipe its scratch to force
        # a fresh extract (otherwise the longer tail would be silently ignored).
        shutil.rmtree(clip_dir / "clips_graded", ignore_errors=True)
        (clip_dir / "base.mp4").unlink(missing_ok=True)
        run(["python3", str(VIDEO_USE_HELPERS / "render.py"),
             str(clip_dir / "edl.json"), "-o", str(cut_landscape), "--no-subtitles"])
        # Re-frame to 1080x1920 (9:16). Crop a 9:16 slice horizontally centred on the
        # chosen speaker (args.crop_center as a fraction of width) — NOT a naive centre
        # crop, which on a 2-cam wide shot slices down the middle between both people.
        pr = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", str(cut_landscape)],
            capture_output=True, text=True).stdout.strip()
        lw, lh = (int(x) for x in pr.split("x"))
        cw = (int(lh * 9 / 16) // 2) * 2           # 9:16 crop width for this height
        cx = max(0, min(lw - cw, int(lw * args.crop_center - cw / 2)))
        cut = clip_dir / "cut.mp4"
        run(["ffmpeg", "-y", "-i", str(cut_landscape),
             "-vf", f"crop={cw}:{lh}:{cx}:0,scale=1080:1920,setsar=1",
             "-c:v", "libx264", "-preset", "medium", "-crf", "18",
             "-c:a", "copy", "-movflags", "+faststart", str(cut)])
        return cut, ranges, meta

    cut_mp4, ranges, meta = _build_and_render(0.18)
    print(f"  tightened: {len(ranges)} range(s), {meta['out_duration']:.1f}s out "
          f"(removed {meta['removed_s']:.1f}s of silence/filler)")

    # 5c-verify. Re-listen protection — re-transcribe the cut and confirm the last
    # word isn't clipped (Sam's #1 complaint). ONE conservative retry with a longer
    # end tail, capped at +0.3s so it can never bleed the next sentence in.
    if not args.no_verify:
        v = verify_cut.verify(cut_mp4, expect_first=meta.get("first_word", ""),
                              expect_last=meta.get("last_word", ""), edit_dir=clip_dir)
        json.dump(v, open(clip_dir / "verify.json", "w"), indent=2)
        if v.get("truncated_end") and v.get("suggest_extra_tail", 0) > 0:
            extra = min(v["suggest_extra_tail"], 0.3)
            print(f"  ⚠ end looked clipped (tail={v.get('tail_words')}) — re-cutting +{extra:.2f}s")
            (clip_dir / "transcripts" / f"{cut_mp4.stem}.json").unlink(missing_ok=True)
            cut_mp4, ranges, meta = _build_and_render(0.18 + extra)
            v = verify_cut.verify(cut_mp4, expect_first=meta.get("first_word", ""),
                                  expect_last=meta.get("last_word", ""), edit_dir=clip_dir)
            json.dump(v, open(clip_dir / "verify.json", "w"), indent=2)
            if not v.get("ok"):
                print(f"  ⚠ still flagged after retry — left for manual review: {v.get('tail_words')}")

    out_dur = meta["out_duration"]

    # Removing silence COMPRESSES the timeline — remap b-roll + caption timings
    # from source time onto the new output timeline so they stay in sync.
    if not args.no_broll:
        overlays_remapped = []
        for o in json.load(open(overlays_json)):
            if "End-of-clip handle" in o.get("reason", ""):
                o["start_in_clip"] = round(max(0.0, out_dur - 3.0), 3)
                overlays_remapped.append(o)
                continue
            ro = tighten_cut.map_src_to_out(start + o["start_in_clip"], ranges)
            if ro >= out_dur - 0.2:
                continue  # landed in removed silence past the end — drop it
            o["start_in_clip"] = ro
            overlays_remapped.append(o)
        overlays_remapped.sort(key=lambda o: o["start_in_clip"])
        json.dump(overlays_remapped, open(overlays_json, "w"), indent=2)

    caps_remapped = []
    for c in json.load(open(captions_json)):
        ro = tighten_cut.map_src_to_out(start + c["t"], ranges)
        if ro >= out_dur - 0.1:
            continue
        c["t"] = round(ro, 3)
        caps_remapped.append(c)
    # Enforce ≥1.5s spacing on the OUTPUT timeline so caption windows never overlap
    # (silence removal can collapse two source words onto nearly the same output time).
    caps_remapped.sort(key=lambda x: x["t"])
    spaced_caps, last_ct = [], -99.0
    for c in caps_remapped:
        if c["t"] - last_ct >= 1.5:
            spaced_caps.append(c); last_ct = c["t"]
    json.dump(spaced_caps, open(captions_json, "w"), indent=2)

    # 5d. Overlay b-roll graphics — first, render any runtime templates (ig_comment with keyword)
    overlays = [] if args.no_broll else json.load(open(overlays_json))
    brand_lib = Path(cfg["brand_library"])
    for o in overlays:
        if o.get("runtime_render") == "ig_comment":
            kw = o["runtime_params"]["keyword"]
            target = brand_lib / "concepts" / f"ig_comment_{kw.lower()}.mov"
            if not target.exists():
                print(f"  rendering runtime ig_comment for keyword={kw}...")
                build_script = brand_lib / "build_ig_comments.py"
                run(["python3", str(build_script),
                     "--keyword", kw,
                     "--name", f"ig_comment_{kw.lower()}"])
            o["asset_path"] = str(target)
    overlay_mp4 = clip_dir / "with_overlays.mp4"
    if not overlays:
        shutil.copy(cut_mp4, overlay_mp4)
    else:
        # Build overlay filter chain
        inputs = ["-i", str(cut_mp4)]
        for o in overlays:
            if "asset_path" not in o:  # [MISSING]
                continue
            inputs += ["-i", o["asset_path"]]
        filter_chain = ""
        last = "0:v"
        idx_in = 1
        for o in overlays:
            if "asset_path" not in o: continue
            t0 = o["start_in_clip"]
            dur = o["duration"]
            is_img = o["asset_path"].lower().endswith((".png", ".jpg", ".jpeg"))
            # PTS-shift overlay frame 0 to its window start (Hard Rule 4).
            # Logos/photos (images) are NOT full-frame — scale them to ~36% width and
            # place them as a card near the top. Only full-frame .mov concepts (popup,
            # handle, ig_comment) overlay edge-to-edge at 0:0.
            if is_img:
                filter_chain += (
                    f"[{idx_in}:v]format=yuva444p,scale=390:-2,setpts=PTS-STARTPTS+{t0}/TB[ov{idx_in}];"
                    f"[{last}][ov{idx_in}]overlay=(W-w)/2:170:enable='between(t,{t0},{t0 + dur})'[v{idx_in}];"
                )
            else:
                filter_chain += (
                    f"[{idx_in}:v]format=yuva444p,setpts=PTS-STARTPTS+{t0}/TB[ov{idx_in}];"
                    f"[{last}][ov{idx_in}]overlay=0:0:enable='between(t,{t0},{t0 + dur})'[v{idx_in}];"
                )
            last = f"v{idx_in}"
            idx_in += 1
        filter_chain = filter_chain.rstrip(";")
        filter_chain += f";[{last}]null[vout]" if filter_chain else ""
        if filter_chain:
            cmd = ["ffmpeg", "-y"] + inputs + [
                "-filter_complex", filter_chain,
                "-map", "[vout]", "-map", "0:a?",
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-pix_fmt", "yuv420p", "-r", "25",
                "-c:a", "copy",
                str(overlay_mp4),
            ]
            r = subprocess.run(cmd, capture_output=True)
            if r.returncode != 0:
                print(f"⚠ overlay step failed for {clip_id}: {r.stderr.decode()[-300:]}",
                      file=sys.stderr)
                shutil.copy(cut_mp4, overlay_mp4)
        else:
            shutil.copy(cut_mp4, overlay_mp4)

    # 5d. Burn captions
    captioned_mp4 = clip_dir / "with_captions.mp4"
    run(["python3", str(HELPERS / "burn_captions.py"),
         str(overlay_mp4), str(captions_json), "-o", str(captioned_mp4)])

    # 5e. Music (skippable with --no-music — final = the captioned cut, voice only)
    if args.no_music:
        print("  (--no-music: skipping music gen + mix)")
        music_mixed_mp4 = captioned_mp4
    else:
        music_mp3 = clip_dir / "music.mp3"
        music_args = ["python3", str(HELPERS / "pick_music.py"),
                      "--clip-transcript", str(transcript),
                      "--clip-start", str(start), "--clip-end", str(end),
                      "--duration", str(out_dur),
                      "-o", str(music_mp3)]
        if args.library_only_music:
            music_args.append("--library-only")
        run(music_args)

        # Mix music under voice at -16dB (timeline is the tightened out_dur, not raw)
        music_mixed_mp4 = clip_dir / "with_music.mp4"
        run(["ffmpeg", "-y", "-i", str(captioned_mp4), "-i", str(music_mp3),
             "-filter_complex",
             f"[1:a]volume=-16dB,afade=t=in:st=0:d=0.5,afade=t=out:st={max(0.0, out_dur - 0.5)}:d=0.5[m];"
             f"[0:a][m]amix=inputs=2:duration=first:dropout_transition=0[a]",
             "-map", "0:v", "-map", "[a]",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             "-shortest", str(music_mixed_mp4)])

    # 5f. Finalise — NO end card (Sam's call).
    finished_dir = work_dir / "finished"
    finished_dir.mkdir(parents=True, exist_ok=True)
    final = finished_dir / f"{clip_id}.mp4"
    shutil.copy(music_mixed_mp4, final)

    print(f"  ✓ FINAL: {final}")
    return final


def main():
    ap = argparse.ArgumentParser(description="Sam Clips Engine")
    ap.add_argument("--input", required=True,
                    help="Local video file path OR YouTube URL")
    ap.add_argument("--work-dir", type=Path, required=True,
                    help="Output directory — clips, transcripts, intermediate files")
    ap.add_argument("--num-clips", type=int, default=12,
                    help="Number of clips to ship (default 12)")
    ap.add_argument("--target-length", type=float, default=35.0,
                    help="Target clip length in seconds (28-48 valid)")
    ap.add_argument("--library-only-music", action="store_true",
                    help="Skip Suno/ElevenLabs music gen, use library only")
    ap.add_argument("--no-music", action="store_true",
                    help="No music at all — final clip is voice-only (captioned cut)")
    ap.add_argument("--no-broll", action="store_true",
                    help="No b-roll/logos/lower-thirds — just the cropped speaker + captions")
    ap.add_argument("--crop-center", type=float, default=0.5,
                    help="Horizontal centre of the 9:16 crop as a fraction of source width "
                         "(0=left, 0.5=centre, 1=right). For a 2-cam pod, point it at the "
                         "speaker — e.g. 0.22 if Sam sits on the left.")
    ap.add_argument("--max-gap", type=float, default=0.28,
                    help="Cut internal silences longer than this (s). Lower = tighter cut.")
    ap.add_argument("--no-verify", action="store_true",
                    help="Skip the Scribe re-listen end-protection pass (faster, less safe)")
    ap.add_argument("--start-from", type=int, default=1,
                    help="Resume from clip N (skip 1..N-1, useful for retries)")
    args = ap.parse_args()

    args.work_dir.mkdir(parents=True, exist_ok=True)
    cfg = load_cfg()

    print(f"\n==== SAM CLIPS ENGINE ====")
    print(f"  input:    {args.input}")
    print(f"  work-dir: {args.work_dir}")
    print(f"  num clips: {args.num_clips}")
    print(f"  target len: {args.target_length}s\n")

    t0 = time.time()

    # Step 1: ingest + verify sync
    print("--- Step 1: Ingest ---")
    source = step1_ingest(args, args.work_dir)

    # Step 2: transcribe
    print("\n--- Step 2: Transcribe (Scribe) ---")
    transcript = step2_transcribe(source, args.work_dir)

    # Step 3: pack
    print("\n--- Step 3: Pack transcript ---")
    packed = step3_pack(args.work_dir)

    # Step 4: generate candidates, then pause for Claude (this session) to rank
    print("\n--- Step 4a: Generate candidate windows ---")
    step4_generate_candidates(packed, args.work_dir, args.target_length)

    print("\n--- Step 4b: Wait for Claude ranking handoff ---")
    ranked_json = step4_check_ranked(args.work_dir, args.num_clips)
    ranked = json.load(open(ranked_json))
    if not ranked:
        sys.exit("❌ ranked_clips.json is empty — fill it in with top N picks")

    # Step 5: build each clip
    print(f"\n--- Step 5: Build {len(ranked)} clips ---")
    outputs = []
    for i, clip in enumerate(ranked, start=1):
        if i < args.start_from:
            continue
        try:
            out = step5_build_clip(i, clip, source, transcript, args.work_dir, args)
            if out:
                outputs.append(out)
        except SystemExit as e:
            print(f"⚠ clip {i} failed: {e}", file=sys.stderr)
            continue

    # Summary
    elapsed = int(time.time() - t0)
    print(f"\n==== DONE ====")
    print(f"  {len(outputs)} clips shipped in {elapsed // 60}m {elapsed % 60}s")
    print(f"  → {args.work_dir}/finished/")
    summary = {
        "input": args.input,
        "source_path": str(source),
        "total_clips_picked": len(ranked),
        "total_clips_shipped": len(outputs),
        "elapsed_seconds": elapsed,
        "outputs": [str(o) for o in outputs],
    }
    json.dump(summary, open(args.work_dir / "summary.json", "w"), indent=2)


if __name__ == "__main__":
    main()
