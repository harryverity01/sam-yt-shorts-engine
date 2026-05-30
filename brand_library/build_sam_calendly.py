#!/usr/bin/env python3
"""Sam's Calendly booking page — pixel-faithful recreation + 'fully booked' animation.

Built from his real mobile Calendly view at calendly.com/sameyeam/call.
1080x1920 transparent .mov for overlay use.

Animation arc (~6s):
  0.0–0.7s : card slides up into frame
  0.7–3.0s : dates progressively light up blue (demand surge — bookings flooding in)
  3.0–4.8s : dates progressively turn back grey (booked out, no slots left)
  4.8–5.5s : "FULLY BOOKED" red stamp slams in + holds
  5.5–6.0s : fade out
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

# ---- Calendly's actual palette (sampled from real screenshot) ----
PAGE_BG = (250, 250, 250, 255)              # #FAFAFA
CARD_BG = (255, 255, 255, 255)              # #FFFFFF
NAVY = (10, 37, 64, 255)                    # #0A2540 header text
SLATE = (71, 85, 105, 255)                  # body text
GREY = (197, 197, 197, 255)                 # unavailable date text
LIGHT_GREY = (229, 229, 229, 255)           # borders
BLUE = (0, 107, 255, 255)                   # #006BFF Calendly primary
PALE_BLUE = (238, 245, 255, 255)            # #EEF5FF available circle BG
RED_STAMP = (220, 38, 38, 255)              # "FULLY BOOKED" stamp

SF_PRO = "/System/Library/Fonts/SFNS.ttf"
HELV = "/System/Library/Fonts/Helvetica.ttc"


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
def ease_in_cubic(t):  return t ** 3


# May 2026 calendar layout — days indexed by (row, col)
# Mon=col 0, Sun=col 6. May 2026 starts Fri 1.
# Rows: 0=labels, 1=week1 (start Fri), 2=week2, 3=week3, 4=week4, 5=week5
CALENDAR_2026_MAY = [
    [None, None, None, None,    1,    2,    3],  # row 1
    [   4,    5,    6,    7,    8,    9,   10],  # row 2
    [  11,   12,   13,   14,   15,   16,   17],  # row 3
    [  18,   19,   20,   21,   22,   23,   24],  # row 4
    [  25,   26,   27,   28,   29,   30,   31],  # row 5
]
DAY_LABELS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


def render_sam_calendly_fully_booked(t, dur=6.0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas

    # ---- Slide-in envelope ----
    if t < 0.7:
        slide = (1 - ease_out_cubic(t / 0.7)) * 400
        op = ease_out_cubic(t / 0.7)
    elif t > 5.5:
        slide = 0
        op = max(0.0, 1.0 - (t - 5.5) / 0.5)
    else:
        slide = 0
        op = 1.0
    alpha = int(255 * op)

    # ---- Card (full-width Calendly page on phone) ----
    card_w = 1000
    card_h = 1720
    cx = W // 2
    card_x = (W - card_w) // 2
    card_y = 120 + int(slide)

    # Drop shadow
    shadow = Image.new("RGBA", (card_w + 60, card_h + 60), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((30, 30, card_w + 30, card_h + 30), radius=40,
                         fill=(0, 0, 0, int(80 * op)))
    canvas.alpha_composite(shadow, (card_x - 30, card_y - 20))

    # Card body
    card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle((0, 0, card_w, card_h), radius=40,
                         fill=(*CARD_BG[:3], alpha))

    # ---- Top header bar (back arrow + Calendly ribbon corner) ----
    # Back arrow blue circle
    cd.ellipse((50, 50, 130, 130),
               outline=(*BLUE[:3], alpha), width=4)
    # Arrow inside
    cd.polygon([(100, 70), (75, 90), (100, 110), (100, 100), (115, 100),
                (115, 80), (100, 80)], fill=(*BLUE[:3], alpha))
    # Calendly ribbon (top-right corner)
    ribbon_pts = [(card_w, 0), (card_w - 200, 0), (card_w, 200)]
    cd.polygon(ribbon_pts, fill=(60, 60, 60, alpha))
    f_ribbon = F_BOLD(22)
    # POWERED BY (small) + Calendly (large) — rotate text along ribbon diagonal
    ribbon_layer = Image.new("RGBA", (260, 80), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ribbon_layer)
    rd.text((130, 18), "POWERED BY", font=F_BOLD(14),
            anchor="mm", fill=(255, 255, 255, alpha))
    rd.text((130, 50), "Calendly", font=F_BOLD(30),
            anchor="mm", fill=(255, 255, 255, alpha))
    ribbon_layer = ribbon_layer.rotate(-45, expand=True, resample=Image.BICUBIC)
    card.alpha_composite(ribbon_layer, (card_w - 240, -20))

    # ---- Sam's Calendly avatar (camera in dark suit — his actual Calendly photo) ----
    avatar_path = ROOT / "people" / "sam_calendly_avatar.png"
    if avatar_path.exists():
        av = Image.open(avatar_path).convert("RGBA")
        av = av.resize((220, 220), Image.LANCZOS)
        if alpha < 255:
            r, g, b, a = av.split()
            a = a.point(lambda v: int(v * op))
            av = Image.merge("RGBA", (r, g, b, a))
        card.alpha_composite(av, ((card_w - 220) // 2, 200))

    # ---- Name + Title ----
    cd.text((cx - card_x, 460), "Sam Eye Am", font=F_REG(40),
            anchor="mm", fill=(*SLATE[:3], alpha))
    cd.text((cx - card_x, 530), "Call", font=F_BOLD(72),
            anchor="mm", fill=(*NAVY[:3], alpha))

    # ---- "1 hr" with clock icon ----
    row_y = 640
    # Clock circle
    cd.ellipse((100, row_y - 24, 148, row_y + 24),
               outline=(*NAVY[:3], alpha), width=3)
    # Clock hands
    cd.line([(124, row_y), (124, row_y - 16)],
            fill=(*NAVY[:3], alpha), width=3)
    cd.line([(124, row_y), (136, row_y + 4)],
            fill=(*NAVY[:3], alpha), width=3)
    cd.text((180, row_y), "1 hr", font=F_BOLD(42),
            anchor="lm", fill=(*NAVY[:3], alpha))

    # ---- Web conferencing line with camera icon ----
    row_y = 720
    # Camera body
    cd.rounded_rectangle((100, row_y - 22, 148, row_y + 22),
                         radius=6, fill=(*NAVY[:3], alpha))
    # Camera lens (the triangle bit on the right)
    cd.polygon([(148, row_y - 12), (170, row_y - 20),
                (170, row_y + 20), (148, row_y + 12)],
               fill=(*NAVY[:3], alpha))
    cd.text((200, row_y - 16), "Web conferencing details", font=F_BOLD(32),
            anchor="lm", fill=(*NAVY[:3], alpha))
    cd.text((200, row_y + 18), "provided upon confirmation.", font=F_BOLD(32),
            anchor="lm", fill=(*NAVY[:3], alpha))

    # ---- Divider ----
    cd.line([(50, 820), (card_w - 50, 820)],
            fill=(*LIGHT_GREY[:3], alpha), width=2)

    # ---- "Select a Day" header ----
    cd.text((cx - card_x, 900), "Select a Day", font=F_BOLD(56),
            anchor="mm", fill=(*NAVY[:3], alpha))

    # ---- Month navigator ← May 2026 → ----
    nav_y = 1000
    cd.text((cx - card_x, nav_y), "May 2026", font=F_BOLD(40),
            anchor="mm", fill=(*NAVY[:3], alpha))
    # Left chevron (greyed)
    cd.line([(360, nav_y - 12), (340, nav_y), (360, nav_y + 12)],
            fill=(*GREY[:3], alpha), width=4)
    # Right chevron (blue circle bg)
    cd.ellipse((640, nav_y - 30, 700, nav_y + 30),
               fill=(*PALE_BLUE[:3], alpha))
    cd.line([(660, nav_y - 12), (680, nav_y), (660, nav_y + 12)],
            fill=(*BLUE[:3], alpha), width=4)

    # ---- Day labels ----
    label_y = 1090
    cal_left = 70
    cal_right = card_w - 70
    col_w = (cal_right - cal_left) // 7
    for c, lab in enumerate(DAY_LABELS):
        x = cal_left + c * col_w + col_w // 2
        cd.text((x, label_y), lab, font=F_BOLD(24),
                anchor="mm", fill=(*SLATE[:3], int(180 * op)))

    # ---- Calendar grid with animated availability ----
    # Animation logic:
    # Phase 1 (0.7 → 3.0s): dates light up blue progressively (1 → 31)
    # Phase 2 (3.0 → 4.8s): dates go back to grey progressively (1 → 31, faster)
    cal_phase = "filling" if t < 3.0 else "booking"
    # How many dates lit blue so far?
    if t < 0.7:
        lit_count = 0
        booked_count = 0
    elif t < 3.0:
        progress = (t - 0.7) / 2.3
        lit_count = int(progress * 31)
        booked_count = 0
    elif t < 4.8:
        progress = (t - 3.0) / 1.8
        lit_count = 31
        booked_count = int(progress * 31)
    else:
        lit_count = 31
        booked_count = 31

    grid_top = 1160
    row_h = 80
    for row_idx, week in enumerate(CALENDAR_2026_MAY):
        y = grid_top + row_idx * row_h
        for col_idx, day in enumerate(week):
            if day is None: continue
            x = cal_left + col_idx * col_w + col_w // 2
            # State: empty / available (blue) / booked (grey)
            if day <= lit_count and day > booked_count:
                # Available (blue circle)
                cd.ellipse((x - 32, y - 32, x + 32, y + 32),
                           fill=(*PALE_BLUE[:3], alpha))
                cd.text((x, y), str(day), font=F_BOLD(32),
                        anchor="mm", fill=(*BLUE[:3], alpha))
            elif day <= booked_count:
                # Booked = greyed out with strikethrough-style line
                cd.text((x, y), str(day), font=F_BOLD(30),
                        anchor="mm", fill=(*GREY[:3], alpha))
                # Subtle strikethrough red to convey "booked"
                cd.line([(x - 24, y), (x + 24, y)],
                        fill=(*RED_STAMP[:3], int(120 * op)), width=2)
            else:
                # Not yet revealed = pure grey
                cd.text((x, y), str(day), font=F_BOLD(30),
                        anchor="mm", fill=(*GREY[:3], int(180 * op)))

    # ---- "Time zone" footer ----
    cd.text((cx - card_x, 1620), "🌐  Central Indonesia Time (20:36)",
            font=F_BOLD(28), anchor="mm", fill=(*SLATE[:3], alpha))

    # Composite card to canvas
    canvas.alpha_composite(card, (card_x, card_y))

    # ---- "FULLY BOOKED" stamp (lands at t=4.8s) — sized to fit canvas ----
    if t > 4.8:
        s_progress = min((t - 4.8) / 0.3, 1.0)
        # Slam in with overshoot
        scale = 1.0 + (1.0 - s_progress) * 0.4   # starts 1.4x, settles to 1.0
        rotation = (1.0 - s_progress) * 12        # tilts in
        stamp_op = min((t - 4.8) / 0.2, 1.0)
        # Stamp sized to fit
        base_w, base_h = 760, 200
        sw, sh = int(base_w * scale), int(base_h * scale)
        # Build with padding for rotation
        pad = 80
        stamp = Image.new("RGBA", (sw + pad * 2, sh + pad * 2), (0, 0, 0, 0))
        st = ImageDraw.Draw(stamp)
        # Red double border
        st.rectangle((pad, pad, sw + pad, sh + pad),
                     outline=(*RED_STAMP[:3], int(255 * stamp_op)),
                     width=int(8 * scale))
        st.rectangle((pad + 14, pad + 14, sw + pad - 14, sh + pad - 14),
                     outline=(*RED_STAMP[:3], int(180 * stamp_op)),
                     width=int(3 * scale))
        f_st = F_BOLD(int(82 * scale))
        st.text((pad + sw // 2, pad + sh // 2), "FULLY BOOKED",
                font=f_st, anchor="mm",
                fill=(*RED_STAMP[:3], int(255 * stamp_op)))
        if rotation > 0.1:
            stamp = stamp.rotate(-rotation, resample=Image.BICUBIC, expand=True)
        canvas.alpha_composite(stamp,
                               (W // 2 - stamp.width // 2,
                                H // 2 + 80 - stamp.height // 2))

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
    render_clip("sam_calendly_fully_booked", render_sam_calendly_fully_booked, 6.0)
    print(f"\n✓ Done → {OUT}/sam_calendly_fully_booked.mov")
