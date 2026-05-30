#!/usr/bin/env python3
"""Sam Hormozi-style word-by-word caption overlays.

Replicates the exact style used in the 14 viral shorts shipped from build_short.py:
  - Montserrat Black 140pt
  - White fill + 8px black stroke
  - Centered horizontally, y = 0.62 * H
  - One word per beat (NOT every word — emphasised words only)
  - 1.5s overlay window with 0.15s pop-in + 0.15s pop-out alpha fade

Usage:
    burn_captions.py <body.mp4> <captions.json> [-o <out.mp4>]

captions.json schema:
    [{"t": 1.234, "word": "STRIPE"}, {"t": 3.456, "word": "$30,000"}, ...]

The `t` is relative to the clip start (seconds). Pick which words to emphasise
via helpers/pick_caption_words.py — don't burn every word, that breaks the rhythm.
"""
import argparse, json, subprocess, sys, tempfile, shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


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
W, H = 1080, 1920


def render_word_png(word: str, font_path: str, size: int, stroke_px: int,
                     y_ratio: float, out_png: Path) -> None:
    """Render a single word as a 1080×1920 transparent PNG with Hormozi-style stroke + fill."""
    font = ImageFont.truetype(font_path, size)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    tw = d.textlength(word, font=font)
    x = int((W - tw) // 2)
    y = int(H * y_ratio)
    # Black stroke (8px radius — matches build_short.py exactly)
    for dx in range(-stroke_px, stroke_px + 1, 2):
        for dy in range(-stroke_px, stroke_px + 1, 2):
            if dx * dx + dy * dy <= stroke_px * stroke_px:
                d.text((x + dx, y + dy), word, font=font, fill=(0, 0, 0, 255))
    # White fill on top
    d.text((x, y), word, font=font, fill=(255, 255, 255, 255))
    img.save(out_png, "PNG")


def burn(body_path: Path, captions: list, out_path: Path, cfg: dict) -> None:
    """Burn N caption overlays onto body_path via ffmpeg overlay filter chain.

    Each caption: 0.15s alpha fade-in, hold ~1.2s, 0.15s alpha fade-out (total 1.5s).
    """
    if not captions:
        # No captions — just copy body to out
        shutil.copy(body_path, out_path)
        return

    specs = cfg["render_specs"]
    font_path = cfg["fonts"]["caption_black"]
    size = specs["caption_size_pt"]
    stroke = specs["caption_stroke_px"]
    y_ratio = specs["caption_y_ratio"]
    win = specs["caption_window_s"]
    fade = specs["caption_fade_s"]

    tmpdir = Path(tempfile.mkdtemp(prefix="sam_caps_"))
    pngs = []
    for i, cap in enumerate(captions):
        png = tmpdir / f"cap_{i:03d}.png"
        render_word_png(cap["word"], font_path, size, stroke, y_ratio, png)
        pngs.append((png, cap["t"]))

    # Build ffmpeg input list + filter chain
    inputs = ["-i", str(body_path)]
    for png, _ in pngs:
        inputs += ["-loop", "1", "-t", str(win), "-i", str(png)]

    filter_chain = ""
    last = "0:v"
    fade_in_end = fade
    fade_out_start = win - fade
    for i, (_, rel_t) in enumerate(pngs):
        idx = i + 1
        out_lbl = f"v{i+1}" if i < len(pngs) - 1 else "vout"
        filter_chain += (
            f"[{idx}:v]format=rgba,"
            f"fade=t=in:st=0:d={fade}:alpha=1,"
            f"fade=t=out:st={fade_out_start}:d={fade}:alpha=1[ov{i}];"
            f"[{last}][ov{i}]overlay=0:0:enable='between(t,{rel_t},{rel_t + win})'[{out_lbl}];"
        )
        last = out_lbl
    filter_chain = filter_chain.rstrip(";")

    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_chain,
        "-map", "[vout]",
        "-map", "0:a?",   # passthrough audio if present
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", str(specs["fps"]),
        "-c:a", "copy",
        str(out_path),
    ]
    r = subprocess.run(cmd, capture_output=True)
    shutil.rmtree(tmpdir, ignore_errors=True)
    if r.returncode != 0:
        sys.exit(f"❌ caption burn failed: {r.stderr.decode()[-600:]}")
    print(f"✓ burned {len(pngs)} caption overlays → {out_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("body", type=Path)
    ap.add_argument("captions_json", type=Path)
    ap.add_argument("-o", "--out", type=Path)
    ap.add_argument("--brand-assets", type=Path, default=DEFAULT_BRAND_ASSETS)
    args = ap.parse_args()

    captions = json.load(open(args.captions_json))
    cfg = _resolve_relative_paths(_resolve_relative_paths(json.load(open(args.brand_assets)), Path(args.brand_assets).resolve()), Path(args.brand_assets).resolve() if not str(args.brand_assets).startswith("Path") else args.brand_assets)
    out = args.out or args.body.with_name(f"{args.body.stem}_captioned.mp4")
    burn(args.body, captions, out, cfg)


if __name__ == "__main__":
    main()
