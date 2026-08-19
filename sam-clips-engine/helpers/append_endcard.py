#!/usr/bin/env python3
"""Append Sam's endcard_v3.mp4 to a finished clip — lossless concat.

The end card has matching codec (libx264 yuv420p), matching sample rate (48000 stereo AAC),
and silent audio baked in. So we can concat with -c copy (no re-encoding the body).

Usage:
    append_endcard.py <body.mp4> [-o <out.mp4>] [--endcard <path>]
"""
import argparse, json, subprocess, sys, tempfile, os
from pathlib import Path

DEFAULT_BRAND_ASSETS = Path(__file__).parent.parent / "brand_assets.json"


def append_endcard(body_path: Path, out_path: Path, endcard_path: Path) -> None:
    if not body_path.exists():
        sys.exit(f"❌ body not found: {body_path}")
    if not endcard_path.exists():
        sys.exit(f"❌ endcard not found: {endcard_path}")

    # Write a concat-file list
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(f"file '{body_path.absolute()}'\n")
        f.write(f"file '{endcard_path.absolute()}'\n")
        list_path = f.name

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", list_path,
        "-c", "copy",
        str(out_path),
    ]
    r = subprocess.run(cmd, capture_output=True)
    os.unlink(list_path)
    if r.returncode != 0:
        # Fallback: re-encode body to match endcard exactly (codec mismatch)
        # This is rare but happens when body went through ProRes intermediate.
        print(f"⚠ lossless concat failed, re-encoding body to match endcard...", file=sys.stderr)
        cmd2 = [
            "ffmpeg", "-y",
            "-i", str(body_path), "-i", str(endcard_path),
            "-filter_complex",
            "[0:v]scale=1080:1920,setsar=1,fps=25[v0];"
            "[1:v]scale=1080:1920,setsar=1,fps=25[v1];"
            "[0:a]aresample=48000,aformat=channel_layouts=stereo[a0];"
            "[1:a]aresample=48000,aformat=channel_layouts=stereo[a1];"
            "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]",
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            str(out_path),
        ]
        r2 = subprocess.run(cmd2, capture_output=True)
        if r2.returncode != 0:
            sys.exit(f"❌ both concat attempts failed:\n{r2.stderr.decode()[-500:]}")
    print(f"✓ {out_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("body", type=Path)
    ap.add_argument("-o", "--out", type=Path)
    ap.add_argument("--endcard", type=Path)
    ap.add_argument("--brand-assets", type=Path, default=DEFAULT_BRAND_ASSETS)
    args = ap.parse_args()

    if not args.endcard:
        cfg = json.load(open(args.brand_assets))
        args.endcard = Path(cfg["endcard"])

    out = args.out or args.body.with_name(f"{args.body.stem}_final.mp4")
    append_endcard(args.body, out, args.endcard)


if __name__ == "__main__":
    main()
