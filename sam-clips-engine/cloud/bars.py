#!/usr/bin/env python3
"""Prison-bar transition for the Melvin prison clip (Harry, 2026-08-27).

Bars drop down over the shot, hold, then lift back out. The bars are a transition
device drawn with alpha, not a fake asset - what sits behind them is the real
Breda Koepel footage. A real metal impact from the R2 SFX library lands on the
frame the bars hit, and a lighter one on the lift. No whoosh, ever.
"""
import os, subprocess, math
from PIL import Image, ImageDraw, ImageFilter
import imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
FF = imageio_ffmpeg.get_ffmpeg_exe()
SFX = os.path.join(HERE, "broll_src", "sfx")
W, H = 1080, 1920


def make_png(out):
    """Vertical bars with a top rail, drawn with alpha so the shot reads through."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rail = 120
    d.rectangle([0, 0, W, rail], fill=(22, 22, 24, 255))
    d.rectangle([0, rail - 14, W, rail], fill=(58, 58, 62, 255))
    n = 7
    bw = 46
    gap = (W - n * bw) / (n + 1)
    for i in range(n):
        x = gap + i * (bw + gap)
        d.rectangle([x, rail, x + bw, H], fill=(26, 26, 28, 255))
        d.rectangle([x + 4, rail, x + 11, H], fill=(74, 74, 80, 255))      # highlight
        d.rectangle([x + bw - 9, rail, x + bw - 4, H], fill=(8, 8, 9, 255))  # shadow
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    img.save(out)
    return out


def apply(beat_mp4, out, dur, drop=0.34, hold=1.6):
    """Overlay the bars on an existing 1080x1920 beat and mix the impacts in."""
    png = os.path.join(HERE, "broll_src", "_bars.png")
    if not os.path.exists(png):
        make_png(png)
    lift_at = drop + hold
    y = (f"'if(lt(t,{drop}), -{H}+t/{drop}*{H},"
         f" if(lt(t,{lift_at}), 0, -( (t-{lift_at})/{drop} )*{H} ))'")
    fc = f"[0:v][1:v]overlay=0:{y}:eof_action=pass[v]"
    cmd = [FF, "-y", "-nostdin", "-i", beat_mp4, "-loop", "1", "-i", png,
           "-filter_complex", fc, "-map", "[v]", "-an", "-t", f"{dur:.2f}",
           "-r", "30", "-c:v", "libx264", "-crf", "19", "-preset", "veryfast",
           "-pix_fmt", "yuv420p", out]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        print("bars FAIL", p.stderr[-600:])
        return None
    if not (os.path.exists(out) and os.path.getsize(out) > 20000):
        return None
    # SFX events, relative to the beat start. Real recordings from the R2 library.
    return [{"file": os.path.join(SFX, "impact_metal-hammer-hit.mp3"),
             "at": round(drop, 3), "gain": 0.85},
            {"file": os.path.join(SFX, "impact_fast-impact-blow.mp3"),
             "at": round(lift_at, 3), "gain": 0.5}]


if __name__ == "__main__":
    import sys
    make_png(os.path.join(HERE, "broll_src", "_bars.png"))
    print("bars png written")
