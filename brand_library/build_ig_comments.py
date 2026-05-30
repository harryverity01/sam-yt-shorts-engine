#!/usr/bin/env python3
"""Sam's IG comments highlight — pixel-faithful recreation + animated keyword highlight.

Built from Sam's actual IG desktop comments view (Screenshot 2026-05-28 at 21.16.54.png).
1080x1920 transparent .mov. Parameterised so the trigger keyword swaps per reel.

Animation arc (~5s):
  0.0–0.6s : card slides up + fades in
  0.6–2.0s : existing comments visible (3 rows)
  2.0–2.6s : highlighted comment slides up + lands at bottom (someone commenting the keyword)
  2.6–3.0s : keyword glow flashes + heart icon pops
  3.0–4.5s : hold steady
  4.5–5.0s : fade out
"""
import argparse, math, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path("/Volumes/Seagate/YouTube/Sam Ey Am/brand_library")
OUT = ROOT / "concepts"
TMP = ROOT / "_tmp_concepts"
OUT.mkdir(exist_ok=True)
TMP.mkdir(exist_ok=True)

W, H, FPS = 1080, 1920, 25

# IG LIGHT MODE palette (sampled from real screenshot)
WHITE = (255, 255, 255, 255)
INK = (38, 38, 38, 255)           # primary text
MID = (115, 115, 115, 255)        # time / secondary text
LIGHT_GREY = (219, 219, 219, 255) # borders
IG_BLUE = (0, 149, 246, 255)      # #0095F6 verified + post link
IG_RED = (237, 73, 86, 255)       # heart filled
HIGHLIGHT_BG = (255, 247, 220, 255)  # soft yellow glow
ORANGE_KEYWORD = (255, 140, 60, 255)  # Sam orange — the keyword pop

HELV = "/System/Library/Fonts/Helvetica.ttc"
SF_PRO = "/System/Library/Fonts/SFNS.ttf"


def font(path, size, idx=None):
    try:
        if idx is not None:
            return ImageFont.truetype(path, size, index=idx)
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.truetype(HELV, size)


F_REG = lambda s: font(SF_PRO, s)
F_BOLD = lambda s: font(HELV, s, idx=1)


def ease_out_cubic(t): return 1 - (1 - t) ** 3
def ease_out_back(t):
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def draw_pill_avatar(cd, cx, cy, r, color, alpha=255):
    """Solid coloured circle as a generic avatar."""
    cd.ellipse((cx - r, cy - r, cx + r, cy + r),
               fill=(*color[:3], alpha))


def draw_heart(cd, cx, cy, r, color, alpha=255, filled=False):
    """Heart drawn as one continuous polygon — looks like an actual heart, not warped ovals."""
    col = (*color[:3], alpha)
    # Heart polygon: starts at bottom point, sweeps up + around through two lobes, back down
    s = r / 14.0
    pts = [
        (cx,              cy + 12 * s),    # bottom tip
        (cx - 13 * s,     cy + 1 * s),     # bottom left curve
        (cx - 14 * s,     cy - 6 * s),     # left lobe outer
        (cx - 9 * s,      cy - 12 * s),    # left lobe top
        (cx - 4 * s,      cy - 10 * s),    # left lobe inner
        (cx,              cy - 5 * s),     # centre dip
        (cx + 4 * s,      cy - 10 * s),    # right lobe inner
        (cx + 9 * s,      cy - 12 * s),    # right lobe top
        (cx + 14 * s,     cy - 6 * s),     # right lobe outer
        (cx + 13 * s,     cy + 1 * s),     # bottom right curve
    ]
    if filled:
        cd.polygon(pts, fill=col)
    else:
        cd.polygon(pts, outline=col)
        # Thicker outline — draw twice with slight offset
        cd.line(pts + [pts[0]], fill=col, width=3)


def render_sam_ig_comment_highlight(t, dur=5.0, keyword="TRAINING",
                                      username="alex_creator_",
                                      comment_text=None,
                                      avatar_color=(180, 120, 240)):
    """Recreate Sam's IG comments section with a highlighted trigger keyword.

    Defaults parameterised — call with different keyword/username per use.
    """
    if comment_text is None:
        comment_text = keyword  # bare keyword by default

    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas

    # ---- Slide-in envelope ----
    if t < 0.6:
        op = ease_out_cubic(t / 0.6)
        slide = (1 - ease_out_cubic(t / 0.6)) * 300
    elif t > 4.5:
        op = max(0.0, 1.0 - (t - 4.5) / 0.5)
        slide = 0
    else:
        op = 1.0
        slide = 0
    alpha = int(255 * op)

    # ---- Card: IG light mode white panel with rounded corners ----
    card_w = 980
    card_h = 1280
    card_x = (W - card_w) // 2
    card_y = 320 + int(slide)

    # Drop shadow
    shadow = Image.new("RGBA", (card_w + 80, card_h + 80), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((40, 40, card_w + 40, card_h + 40), radius=36,
                         fill=(0, 0, 0, int(70 * op)))
    canvas.alpha_composite(shadow, (card_x - 40, card_y - 20))

    card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle((0, 0, card_w, card_h), radius=36,
                         fill=(*WHITE[:3], alpha))

    # ---- Top: handle bar (sameyeam.secrets + verified + ...) ----
    avatar_path = ROOT / "people" / "sam_eye_am.png"
    if avatar_path.exists():
        sam_av = Image.open(avatar_path).convert("RGBA").resize((90, 90), Image.LANCZOS)
        if alpha < 255:
            r, g, b, a = sam_av.split()
            a = a.point(lambda v: int(v * op))
            sam_av = Image.merge("RGBA", (r, g, b, a))
        card.alpha_composite(sam_av, (40, 40))

    # Handle text + verified
    handle = "sameyeam.secrets"
    f_handle = F_BOLD(38)
    cd.text((160, 56), handle, font=f_handle, fill=(*INK[:3], alpha))
    bb = f_handle.getbbox(handle)
    handle_w = bb[2] - bb[0]
    # Verified blue 8-pt star
    vx, vy = 170 + handle_w, 76
    star_pts = []
    for i in range(16):
        ang = (i * 22.5) * math.pi / 180
        r = 16 if i % 2 == 0 else 11
        star_pts.append((vx + math.cos(ang) * r, vy + math.sin(ang) * r))
    cd.polygon(star_pts, fill=(*IG_BLUE[:3], alpha))
    cd.line([(vx - 7, vy + 1), (vx - 2, vy + 6), (vx + 8, vy - 4)],
            fill=(255, 255, 255, alpha), width=3)
    # "Original audio" subtitle
    cd.text((160, 100), "Original audio", font=F_REG(26),
            fill=(*MID[:3], alpha))
    # ⋯ menu top-right
    for i in range(3):
        cd.ellipse((card_w - 90 + i * 18 - 4, 76, card_w - 90 + i * 18 + 4, 84),
                   fill=(*INK[:3], alpha))

    # Divider
    cd.line([(40, 170), (card_w - 40, 170)],
            fill=(*LIGHT_GREY[:3], alpha), width=2)

    # ---- "Comments" section header ----
    cd.text((40, 200), "Comments", font=F_BOLD(34),
            fill=(*INK[:3], alpha))

    # ---- 3 existing comments (always visible) ----
    # Plain-text comments — no emojis (PIL renders them as black squares without a colour-emoji font)
    existing = [
        {"handle": "itmahfijur", "text": "Love this so much!", "time": "13w", "color": (240, 100, 100)},
        {"handle": "itsbahador", "text": "What is your camera?", "time": "13w", "color": (100, 150, 240)},
        {"handle": "maria.fitness", "text": "This changed everything for me", "time": "12w", "color": (240, 180, 100)},
    ]
    row_y = 280
    row_h = 130
    for i, c in enumerate(existing):
        y = row_y + i * row_h
        # Generic colour avatar (no real photos for commenters)
        draw_pill_avatar(cd, 70, y + 40, 38, c["color"], alpha=alpha)
        # Handle (bold)
        cd.text((130, y + 14), c["handle"], font=F_BOLD(30),
                fill=(*INK[:3], alpha))
        # Comment text (reg, wrap on next line)
        cd.text((130, y + 58), c["text"], font=F_REG(28),
                fill=(*INK[:3], alpha))
        # Time + Reply (small grey)
        cd.text((130, y + 95), f"{c['time']}  ·  Reply",
                font=F_REG(22), fill=(*MID[:3], alpha))
        # Heart icon on right
        draw_heart(cd, card_w - 60, y + 50, 14, MID, alpha=alpha)

    # ---- HIGHLIGHTED COMMENT (the new one with the keyword) ----
    # Slides up from bottom starting at t=2.0s, lands at t=2.6s
    hl_y_target = row_y + 3 * row_h + 20
    if t < 2.0:
        hl_alpha = 0
    else:
        slide_progress = ease_out_back(min((t - 2.0) / 0.6, 1.0))
        hl_y = int(hl_y_target + (1 - slide_progress) * 200)
        hl_alpha = int(255 * min((t - 2.0) / 0.3, 1.0) * op)

        # Yellow glow pulse on the highlighted row (peaks at t=2.8s)
        pulse_t = t - 2.6
        glow_intensity = 1.0
        if 0 < pulse_t < 0.8:
            glow_intensity = 1.0 + 0.5 * math.sin(pulse_t * math.pi / 0.4)

        # Background highlight panel
        cd.rounded_rectangle((30, hl_y - 15, card_w - 30, hl_y + 110),
                             radius=16,
                             fill=(*HIGHLIGHT_BG[:3], int(180 * op * glow_intensity)))
        # Orange left border bar (sam brand accent)
        cd.rounded_rectangle((30, hl_y - 15, 42, hl_y + 110), radius=4,
                             fill=(*ORANGE_KEYWORD[:3], int(255 * op)))

        # Avatar
        draw_pill_avatar(cd, 70, hl_y + 40, 38, avatar_color, alpha=hl_alpha)
        # Handle
        cd.text((130, hl_y + 14), username, font=F_BOLD(30),
                fill=(*INK[:3], hl_alpha))

        # Comment text WITH highlighted keyword
        # Render text-up-to-keyword | keyword-pill | text-after
        full = comment_text
        kw_upper = keyword
        # Find keyword position (case-insensitive)
        idx = full.upper().find(kw_upper.upper())
        if idx == -1:
            # Keyword not in comment — render plain
            cd.text((130, hl_y + 58), full, font=F_REG(28),
                    fill=(*INK[:3], hl_alpha))
        else:
            before = full[:idx]
            actual_kw = full[idx:idx + len(kw_upper)]
            after = full[idx + len(kw_upper):]
            f_body = F_REG(28)
            f_kw = F_BOLD(32)
            x_cur = 130
            # Before
            if before:
                cd.text((x_cur, hl_y + 58), before, font=f_body,
                        fill=(*INK[:3], hl_alpha))
                x_cur += int(cd.textlength(before, font=f_body))
            # Keyword highlight pill — orange BG, white text
            kw_w = int(cd.textlength(actual_kw, font=f_kw)) + 24
            cd.rounded_rectangle((x_cur, hl_y + 50,
                                  x_cur + kw_w, hl_y + 96),
                                 radius=10,
                                 fill=(*ORANGE_KEYWORD[:3], hl_alpha))
            cd.text((x_cur + 12, hl_y + 55), actual_kw, font=f_kw,
                    fill=(255, 255, 255, hl_alpha))
            x_cur += kw_w
            # After
            if after:
                cd.text((x_cur + 4, hl_y + 58), after, font=f_body,
                        fill=(*INK[:3], hl_alpha))

        # Time + Reply
        cd.text((130, hl_y + 95), "Just now  ·  Reply",
                font=F_REG(22), fill=(*MID[:3], hl_alpha))

        # Heart pops red at t=2.8s
        heart_filled = (t > 2.8)
        heart_color = IG_RED if heart_filled else MID
        heart_scale = 1.0
        if 2.8 < t < 3.0:
            heart_scale = 1.0 + 0.5 * (1 - (t - 2.8) / 0.2)
        hr = int(14 * heart_scale)
        draw_heart(cd, card_w - 60, hl_y + 50, hr, heart_color,
                   alpha=hl_alpha, filled=heart_filled)

    canvas.alpha_composite(card, (card_x, card_y))
    return canvas


def render_clip(name, fn, dur, **kwargs):
    out = OUT / f"{name}.mov"
    if out.exists(): out.unlink()
    fdir = TMP / name
    fdir.mkdir(parents=True, exist_ok=True)
    n = int(dur * FPS)
    print(f"  → {name} ({dur:.1f}s, {n} frames)")
    for i in range(n):
        img = fn(i / FPS, dur, **kwargs)
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keyword", default="TRAINING",
                    help="The trigger word Sam asked viewers to comment (e.g. TRAINING, CLIENTS, AI)")
    ap.add_argument("--username", default="alex_creator_",
                    help="Handle of the commenter")
    ap.add_argument("--comment-text",
                    help="Full comment body. If omitted, uses just the keyword.")
    ap.add_argument("--avatar-color", nargs=3, type=int, default=[180, 120, 240],
                    help="RGB tuple for the generic commenter avatar")
    ap.add_argument("--duration", type=float, default=5.0)
    ap.add_argument("--name", default=None,
                    help="Output basename (default: ig_comment_<keyword_lower>)")
    args = ap.parse_args()

    name = args.name or f"ig_comment_{args.keyword.lower()}"
    render_clip(name, render_sam_ig_comment_highlight, args.duration,
                keyword=args.keyword,
                username=args.username,
                comment_text=args.comment_text,
                avatar_color=tuple(args.avatar_color))
    print(f"\n✓ {OUT}/{name}.mov")


if __name__ == "__main__":
    main()
