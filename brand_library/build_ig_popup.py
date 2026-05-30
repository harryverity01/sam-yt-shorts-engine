#!/usr/bin/env python3
"""Sam's Instagram profile popup — pixel-faithful recreation of @sameyeam.secrets header.

Built as a 1080x1920 transparent .mov so it can drop into any Sam Short.
Uses IG's actual dark-mode UI (Helvetica/SF Pro, IG-blue Follow button,
verified blue checkmark) — NOT Sam-brand fonts, because we're recreating
the IG app itself.

Reference: harry's iPhone screenshot of @sameyeam.secrets (2026-05-28).
"""
import math, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path("/Volumes/Seagate/YouTube/Sam Ey Am/brand_library")
OUT = ROOT / "concepts"
TMP = ROOT / "_tmp_concepts"
OUT.mkdir(exist_ok=True)
TMP.mkdir(exist_ok=True)

W, H, FPS = 1080, 1920, 25

# ---- IG dark-mode palette (exact) ----
IG_BG = (0, 0, 0, 255)
IG_TEXT_WHITE = (245, 245, 245, 255)
IG_TEXT_GREY = (170, 170, 170, 255)
IG_BLUE = (0, 149, 246, 255)          # #0095F6 — Follow button + verified
IG_GREY_BTN = (38, 38, 38, 255)       # Message button bg
IG_BORDER = (38, 38, 38, 255)

# IG uses Helvetica Neue / SF Pro Display on iOS. macOS has SF Pro Display.
SF_PRO = "/System/Library/Fonts/SFNS.ttf"
HELV_BOLD = "/System/Library/Fonts/Helvetica.ttc"

def font(path, size, idx=None):
    try:
        if idx is not None:
            return ImageFont.truetype(path, size, index=idx)
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.truetype(HELV_BOLD, size)

# Helvetica.ttc index 1 = Bold on most macOS systems
F_REG = lambda s: font(SF_PRO, s)
F_BOLD = lambda s: font(HELV_BOLD, s, idx=1)


def ease_out_cubic(t): return 1 - (1 - t) ** 3


def render_sam_ig_popup(t, dur=4.0):
    """Recreates Sam's @sameyeam.secrets profile header — dark mode, accurate stats.

    Animation:
      0.0–0.5s : slide down + fade in (springs into frame from top)
      0.5–3.0s : hold steady, Follow button pulses subtly
      3.0–4.0s : hold, fade-out at very end
    """
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas

    # Envelope
    if t < 0.5:
        op = ease_out_cubic(t / 0.5)
        slide = (1 - ease_out_cubic(t / 0.5)) * -200
    elif t > 3.5:
        op = max(0.0, 1.0 - (t - 3.5) / 0.5)
        slide = 0
    else:
        op = 1.0
        slide = 0
    alpha = int(255 * op)

    # ---- Card background: dark rounded panel ----
    # Card sits in upper-middle of frame, ~1000px wide x ~1200px tall
    card_w, card_h = 980, 1200
    cx = W // 2
    card_x = (W - card_w) // 2
    card_y = 300 + int(slide)

    # Drop shadow
    shadow = Image.new("RGBA", (card_w + 60, card_h + 60), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((30, 30, card_w + 30, card_h + 30), radius=40,
                         fill=(0, 0, 0, int(160 * op)))
    canvas.alpha_composite(shadow, (card_x - 30, card_y - 20))

    # Card body (true black IG dark mode)
    card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle((0, 0, card_w, card_h), radius=40,
                         fill=(0, 0, 0, alpha))

    # ---- Header bar: back chevron + handle + verified + ⋯ ----
    # Back arrow
    cd.polygon([(60, 100), (105, 70), (105, 130)], fill=(*IG_TEXT_WHITE[:3], alpha))
    # Handle "sameyeam.secrets" — IG uses a chunky semi-bold
    f_handle = F_BOLD(54)
    handle = "sameyeam.secrets"
    bb = f_handle.getbbox(handle)
    handle_w = bb[2] - bb[0]
    handle_x = (card_w - handle_w - 70) // 2  # leave room for checkmark
    cd.text((handle_x, 65), handle, font=f_handle, fill=(*IG_TEXT_WHITE[:3], alpha))
    # Verified blue checkmark (IG's 8-point star with white tick)
    check_cx = handle_x + handle_w + 50
    check_cy = 95
    cr = 28
    # 8-point star using two overlapping diamonds
    star_pts = []
    for i in range(16):
        ang = (i * 22.5) * math.pi / 180
        r = cr if i % 2 == 0 else cr - 8
        star_pts.append((check_cx + math.cos(ang) * r,
                         check_cy + math.sin(ang) * r))
    cd.polygon(star_pts, fill=(*IG_BLUE[:3], alpha))
    # White checkmark inside
    cd.line([(check_cx - 12, check_cy + 2),
             (check_cx - 3, check_cy + 12),
             (check_cx + 14, check_cy - 8)],
            fill=(255, 255, 255, alpha), width=5)
    # ⋯ menu
    for i in range(3):
        dot_x = card_w - 80 + i * 14
        cd.ellipse((dot_x - 4, 91, dot_x + 4, 99),
                   fill=(*IG_TEXT_WHITE[:3], alpha))

    # ---- Avatar (round, 280px) on the left ----
    avatar_path = ROOT / "people" / "sam_eye_am.png"
    if avatar_path.exists():
        av = Image.open(avatar_path).convert("RGBA")
        av = av.resize((280, 280), Image.LANCZOS)
        # Apply opacity
        if alpha < 255:
            r, g, b, a = av.split()
            a = a.point(lambda v: int(v * op))
            av = Image.merge("RGBA", (r, g, b, a))
        card.alpha_composite(av, (60, 200))

    # ---- "Sam Eye Am | Content Marketing Expert" display name ----
    # IG renders this in bold ~32px next to avatar
    f_name = F_BOLD(46)
    name_x = 380
    # Use thin vertical bar U+2502 ("│") for the pipe — reads clearly as a separator
    cd.text((name_x, 220), "Sam Eye Am │ Content",
            font=f_name, fill=(*IG_TEXT_WHITE[:3], alpha))
    cd.text((name_x, 280), "Marketing Expert",
            font=f_name, fill=(*IG_TEXT_WHITE[:3], alpha))

    # ---- Stats row: 1,053 posts · 143K followers · 2,655 following ----
    # Centers shifted right so numbers clear the avatar circle (right edge ~340).
    stat_y = 380
    stat_xs = [470, 660, 850]
    nums = ["1,053", "143K", "2,655"]
    labels = ["posts", "followers", "following"]
    f_num = F_BOLD(48)
    f_lab = F_REG(34)
    for x, n, l in zip(stat_xs, nums, labels):
        cd.text((x, stat_y), n, font=f_num,
                fill=(*IG_TEXT_WHITE[:3], alpha), anchor="mm")
        cd.text((x, stat_y + 60), l, font=f_lab,
                fill=(*IG_TEXT_WHITE[:3], alpha), anchor="mm")

    # ---- Bio block ----
    bio_y = 540
    f_bio = F_REG(36)
    for i, line in enumerate([
        "Business mentor,",
        "AI systems for personal brands & family",
        "offices",
    ]):
        cd.text((60, bio_y + i * 50), line, font=f_bio,
                fill=(*IG_TEXT_WHITE[:3], alpha))
    # PIL-drawn down chevron (white, simple + readable)
    chev_y = bio_y + 175
    chev_cx = 82
    # Filled triangle pointing down
    cd.polygon([(chev_cx - 22, chev_y - 14),
                (chev_cx + 22, chev_y - 14),
                (chev_cx, chev_y + 14)],
               fill=(*IG_TEXT_WHITE[:3], alpha))
    cd.text((120, chev_y - 22), "Free Courses + coaching",
            font=f_bio, fill=(*IG_TEXT_WHITE[:3], alpha))
    # Link line with PIL-drawn chain link icon
    link_y = bio_y + 230
    # Two interlocking oval rings
    cd.ellipse((60, link_y - 8, 92, link_y + 24),
               outline=(*IG_BLUE[:3], alpha), width=3)
    cd.ellipse((82, link_y - 4, 114, link_y + 28),
               outline=(*IG_BLUE[:3], alpha), width=3)
    cd.text((130, link_y), "www.sameyeam.info",
            font=f_bio, fill=(*IG_BLUE[:3], alpha))

    # ---- Follow + Message buttons (Follow + Message fit card edge cleanly) ----
    btn_y = 1010
    btn_h = 110
    btn_gap = 20
    side_pad = 60
    inner_w = card_w - side_pad * 2 - btn_gap
    fw = inner_w // 2
    mw = inner_w - fw
    # Follow (primary IG blue) with subtle pulse on width
    pulse = 1.0 + 0.015 * math.sin(2 * math.pi * t / 0.9)
    fx = side_pad
    fw_p = int(fw * pulse)
    cd.rounded_rectangle((fx, btn_y, fx + fw_p, btn_y + btn_h),
                         radius=20, fill=(*IG_BLUE[:3], alpha))
    f_btn = F_BOLD(50)
    cd.text((fx + fw_p // 2, btn_y + btn_h // 2), "Follow",
            font=f_btn, fill=(255, 255, 255, alpha), anchor="mm")
    # Message (secondary grey)
    mx = fx + fw + btn_gap
    cd.rounded_rectangle((mx, btn_y, mx + mw, btn_y + btn_h),
                         radius=20, fill=(*IG_GREY_BTN[:3], alpha))
    cd.text((mx + mw // 2, btn_y + btn_h // 2), "Message",
            font=f_btn, fill=(*IG_TEXT_WHITE[:3], alpha), anchor="mm")

    canvas.alpha_composite(card, (card_x, card_y))
    return canvas


def render_clip(name, fn, dur):
    out = OUT / f"{name}.mov"
    if out.exists(): out.unlink()
    fdir = TMP / name
    fdir.mkdir(parents=True, exist_ok=True)
    n = int(dur * FPS)
    print(f"  → {name} ({dur:.1f}s, {n} frames)")
    for i in range(n):
        img = fn(i / FPS, dur)
        img.save(fdir / f"f_{i:05d}.png")
    cmd = ["ffmpeg", "-y", "-framerate", str(FPS),
           "-i", str(fdir / "f_%05d.png"),
           "-c:v", "qtrle", "-pix_fmt", "argb",
           str(out)]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        print(f"    ✗ {r.stderr.decode()[-200:]}")
        return None
    return out


if __name__ == "__main__":
    render_clip("sam_ig_popup", render_sam_ig_popup, 4.0)
    print(f"\n✓ Done → {OUT}/sam_ig_popup.mov")
