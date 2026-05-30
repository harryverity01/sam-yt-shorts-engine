#!/usr/bin/env python3
"""Build concept Remotion graphics for Sam's brand library.

Each concept is a 2.5-3s transparent .mov at 1080×1920, with pop-in / hold / pop-out
and continuous subtle motion during hold. Style: HV-influenced (Anton italic red shadow
for big text, clean geometric for diagrams), but adapted for Sam's orange+navy brand.
"""
import os, math, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path("/Volumes/Seagate/YouTube/Sam Ey Am/brand_library")
OUT = ROOT / "concepts"
TMP = ROOT / "_tmp_concepts"
OUT.mkdir(exist_ok=True)
TMP.mkdir(exist_ok=True)

W, H, FPS = 1080, 1920, 25
ORANGE = (255, 140, 60, 255)
ORANGE_DARK = (220, 100, 30, 255)
NAVY = (12, 14, 22, 255)
NAVY_LIGHT = (24, 28, 42, 255)
CREAM = (245, 240, 230, 255)
INK = (17, 17, 17, 255)
RED = (214, 40, 40, 255)
WHITE = (255, 255, 255, 255)
DIM = (150, 150, 160, 255)

ANTON_PATH = "/Users/harrycunningham/Library/Fonts/Anton-Regular.ttf"
MONT_BLACK = "/Volumes/Seagate/YouTube/Sam Ey Am/Shorts/_assets/fonts/Montserrat-Black.ttf"
MONT_REG = "/Volumes/Seagate/YouTube/Sam Ey Am/Shorts/_assets/fonts/Montserrat-Regular.ttf"
BELLEFAIR_PATH = "/Volumes/Seagate/YouTube/Sam Ey Am/Shorts/_assets/fonts/Bellefair-Regular.ttf"

def font(path, size):
    try: return ImageFont.truetype(path, size)
    except: return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)

ANTON = lambda s: font(ANTON_PATH, s)
MONT_B = lambda s: font(MONT_BLACK, s)
MONT_R = lambda s: font(MONT_REG, s)
BELLEFAIR = lambda s: font(BELLEFAIR_PATH, s)


def draw_bellefair_with_shadow(canvas, text, x, y, size, color=WHITE, shadow=ORANGE,
                                sx=6, sy=8, opacity=1.0):
    """Bellefair (high-contrast Didone serif) with offset shadow for legibility.
    No italic skew — Bellefair's character set is upright editorial."""
    f = BELLEFAIR(size)
    bbox = f.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = 60
    layer = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text((pad - bbox[0] + sx, pad - bbox[1] + sy), text, font=f,
           fill=(*shadow[:3], int(255 * opacity)))
    d.text((pad - bbox[0], pad - bbox[1]), text, font=f,
           fill=(*color[:3], int(255 * opacity)))
    canvas.alpha_composite(layer, (x - layer.width // 2, y - layer.height // 2))

def ease_out_cubic(t): return 1 - (1 - t) ** 3

def envelope(t, dur, pop_in=0.20, pop_out=0.20):
    if t < pop_in: p = ease_out_cubic(t / pop_in); return p, 0.88 + 0.12 * p
    if t < dur - pop_out: return 1.0, 1.0
    if t < dur: p = (t - (dur - pop_out)) / pop_out; return 1.0 - p ** 2, 1.0 - 0.04 * p
    return 0.0, 1.0

def draw_bellefair_with_shadow(canvas, text, x, y, size, color=WHITE, shadow=ORANGE,
                            sx=10, sy=12, skew=-0.14, opacity=1.0):
    f = ANTON(size)
    bbox = f.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = 80
    layer = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text((pad - bbox[0] + sx, pad - bbox[1] + sy), text, font=f,
           fill=(*shadow[:3], int(255 * opacity)))
    d.text((pad - bbox[0], pad - bbox[1]), text, font=f,
           fill=(*color[:3], int(255 * opacity)))
    if abs(skew) > 0.001:
        layer = layer.transform(layer.size, Image.AFFINE, (1, skew, 0, 0, 1, 0), Image.BICUBIC)
    canvas.alpha_composite(layer, (x - layer.width // 2, y - layer.height // 2))

# ============================================================
# CONCEPT TEMPLATES
# ============================================================

def render_closer_to_money(t, dur=3.0):
    """Concentric rings with $ at centre — 'Closer to money = more money'."""
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Three concentric circles, fading from orange to dim
    drift = math.sin(2 * math.pi * t / 2.0) * 8
    for ri, (radius, opacity_mult, w) in enumerate([(420, 0.3, 8), (300, 0.5, 10), (180, 0.7, 12)]):
        r = int(radius * sc)
        color_op = int(255 * op * opacity_mult)
        for offset in range(w):
            d.ellipse((cx - r - offset, cy - r - offset, cx + r + offset, cy + r + offset),
                      outline=(*ORANGE[:3], color_op // (1 + offset)))
    # Big $ in centre
    draw_bellefair_with_shadow(canvas, "$", cx, cy + int(drift), int(280 * sc),
                           color=ORANGE, shadow=ORANGE_DARK, opacity=op)
    # Tagline below
    f = MONT_B(int(54 * sc))
    text = "CLOSER TO MONEY"
    bbox = f.getbbox(text)
    tw = bbox[2] - bbox[0]
    d.text((cx - tw // 2, cy + int(450 * sc)), text, font=f,
           fill=(*WHITE[:3], int(255 * op)))
    text2 = "= MORE MONEY"
    bbox = f.getbbox(text2)
    tw = bbox[2] - bbox[0]
    d.text((cx - tw // 2, cy + int(520 * sc)), text2, font=f,
           fill=(*ORANGE[:3], int(255 * op)))
    return canvas

def render_400_to_4000(t, dur=3.5):
    """Money counter $400 → $4,000."""
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    # Phase 1 (0-1.2s): $400 grows in
    # Phase 2 (1.2-2.0s): arrow + transition
    # Phase 3 (2.0-): $4,000 lands big
    if t < 1.2:
        phase_op = ease_out_cubic(min(t / 0.4, 1.0)) * op
        draw_bellefair_with_shadow(canvas, "$400", cx, cy - 150, int(280 * sc),
                               color=WHITE, shadow=ORANGE, opacity=phase_op)
    elif t < 2.0:
        # $400 dims, arrow appears
        p = (t - 1.2) / 0.8
        draw_bellefair_with_shadow(canvas, "$400", cx, cy - 200, int(180 * sc),
                               color=DIM, shadow=DIM, opacity=(1 - p * 0.6) * op)
        f_arrow = ANTON(int(180 * sc))
        d = ImageDraw.Draw(canvas)
        d.text((cx, cy + 20), "↓", font=f_arrow, anchor="mm",
               fill=(*ORANGE[:3], int(255 * op * p)))
    else:
        # Final state
        draw_bellefair_with_shadow(canvas, "$400", cx, cy - 220, int(140 * sc),
                               color=DIM, shadow=DIM, opacity=0.4 * op)
        f_arrow = ANTON(int(160 * sc))
        ImageDraw.Draw(canvas).text((cx, cy - 50), "↓", font=f_arrow, anchor="mm",
                                     fill=(*ORANGE[:3], int(255 * op)))
        phase3_t = min((t - 2.0) / 0.5, 1.0)
        big_op = ease_out_cubic(phase3_t) * op
        big_sc = (0.85 + 0.15 * phase3_t) * sc
        draw_bellefair_with_shadow(canvas, "$4,000", cx, cy + 200, int(360 * big_sc),
                               color=ORANGE, shadow=ORANGE_DARK, opacity=big_op)
        # 10x stamp in corner
        if phase3_t > 0.6:
            stamp_op = (phase3_t - 0.6) / 0.4 * op
            draw_bellefair_with_shadow(canvas, "10×", cx + 380, cy + 380, int(180 * sc),
                                   color=RED, shadow=ORANGE_DARK, opacity=stamp_op, skew=0.10)
    return canvas

def render_victim_vs_creator(t, dur=3.0):
    """Split-screen VICTIM (red, left) vs CREATOR (orange, right)."""
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    # Left half: red zone with VICTIM
    left = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(left)
    ld.rectangle((0, cy - 400, W // 2 - 20, cy + 400),
                 fill=(80, 30, 30, int(220 * op)))
    canvas.alpha_composite(left)
    draw_bellefair_with_shadow(canvas, "VICTIM", cx - 280, cy - 60, int(120 * sc),
                           color=WHITE, shadow=RED, opacity=op)
    # Subtitle
    f = MONT_B(int(34 * sc))
    d = ImageDraw.Draw(canvas)
    d.text((cx - 280, cy + 80), '"why me?"', font=f, anchor="mm",
           fill=(*CREAM[:3], int(180 * op)))
    # Right half: orange zone with CREATOR
    right = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(right)
    rd.rectangle((W // 2 + 20, cy - 400, W, cy + 400),
                 fill=(40, 30, 15, int(220 * op)))
    canvas.alpha_composite(right)
    draw_bellefair_with_shadow(canvas, "CREATOR", cx + 280, cy - 60, int(120 * sc),
                           color=WHITE, shadow=ORANGE, opacity=op)
    d.text((cx + 280, cy + 80), '"watch this."', font=f, anchor="mm",
           fill=(*ORANGE[:3], int(255 * op)))
    # VS in middle
    draw_bellefair_with_shadow(canvas, "vs", cx, cy + int(8 * math.sin(2 * math.pi * t / 1.5)),
                           int(80 * sc), color=ORANGE, shadow=ORANGE_DARK, opacity=op)
    return canvas

def render_money_while_sleep(t, dur=3.5):
    """HERO quote: 'IF YOU CAN'T MAKE MONEY WHILE YOU SLEEP / YOU WILL WORK UNTIL YOU DIE'."""
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    # 5am clock icon (top)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Phase 1 (0-1.5s): top half — "MAKE MONEY WHILE YOU SLEEP"
    if t < 0.5:
        line_op = ease_out_cubic(t / 0.5) * op
    else:
        line_op = op
    draw_bellefair_with_shadow(canvas, "MAKE MONEY", cx, cy - 350, int(140 * sc),
                           color=WHITE, shadow=ORANGE, opacity=line_op)
    draw_bellefair_with_shadow(canvas, "WHILE YOU SLEEP", cx, cy - 180, int(110 * sc),
                           color=ORANGE, shadow=ORANGE_DARK, opacity=line_op)
    # OR (small, between)
    if t > 1.0:
        or_op = ease_out_cubic(min((t - 1.0) / 0.4, 1.0)) * op
        f_or = MONT_B(int(60 * sc))
        d.text((cx, cy), "OR", font=f_or, anchor="mm",
               fill=(*DIM[:3], int(255 * or_op)))
    # Phase 2 (1.5-): bottom half — "WORK UNTIL YOU DIE"
    if t > 1.5:
        bot_op = ease_out_cubic(min((t - 1.5) / 0.5, 1.0)) * op
        draw_bellefair_with_shadow(canvas, "WORK", cx, cy + 180, int(140 * sc),
                               color=WHITE, shadow=RED, opacity=bot_op)
        draw_bellefair_with_shadow(canvas, "UNTIL YOU DIE", cx, cy + 350, int(110 * sc),
                               color=RED, shadow=(80, 0, 0, 255), opacity=bot_op)
    return canvas

def render_show_dont_tell(t, dur=2.5):
    """SHOW > TELL type card."""
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    draw_bellefair_with_shadow(canvas, "SHOW.", cx, cy - 200, int(280 * sc),
                           color=ORANGE, shadow=ORANGE_DARK, opacity=op)
    f = MONT_B(int(80 * sc))
    d = ImageDraw.Draw(canvas)
    d.text((cx, cy), "DON'T", font=f, anchor="mm",
           fill=(*DIM[:3], int(255 * op)))
    # Crossed out tell
    draw_bellefair_with_shadow(canvas, "TELL.", cx, cy + 200, int(280 * sc),
                           color=DIM, shadow=DIM, opacity=op * 0.6)
    # Strike line
    line_op = int(255 * op)
    line_w = int(440 * sc)
    d.line([(cx - line_w // 2, cy + 200), (cx + line_w // 2, cy + 200)],
           fill=(*RED[:3], line_op), width=int(14 * sc))
    return canvas

def render_responsibility_results(t, dur=3.0):
    """Stairs climbing — More responsibility = more results."""
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # 5 ascending bars
    bar_w = int(120 * sc)
    bar_gap = int(20 * sc)
    base_x = cx - (5 * bar_w + 4 * bar_gap) // 2
    bar_y_base = cy + 200
    for i in range(5):
        rise = (i + 1) * 70 * sc
        x = base_x + i * (bar_w + bar_gap)
        h = int(rise)
        bar_op_phase = ease_out_cubic(min(max((t - i * 0.1) / 0.3, 0), 1.0))
        color = (*ORANGE[:3], int(255 * op * bar_op_phase))
        d.rectangle((x, bar_y_base - h, x + bar_w, bar_y_base), fill=color)
    # Up arrow at top
    draw_bellefair_with_shadow(canvas, "↑", cx + int(280 * sc), cy - 200,
                           int(180 * sc), color=ORANGE, shadow=ORANGE_DARK, opacity=op)
    # Tagline
    draw_bellefair_with_shadow(canvas, "MORE", cx, cy - 350, int(120 * sc),
                           color=WHITE, shadow=ORANGE, opacity=op)
    draw_bellefair_with_shadow(canvas, "RESPONSIBILITY", cx, cy - 220, int(80 * sc),
                           color=ORANGE, shadow=ORANGE_DARK, opacity=op)
    f = MONT_B(int(48 * sc))
    d.text((cx, cy + 450), "= MORE RESULTS", font=f, anchor="mm",
           fill=(*WHITE[:3], int(255 * op)))
    return canvas

def render_lean_into_fear(t, dur=3.0):
    """Door / threshold graphic — Lean into fear."""
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Dark doorway with orange glow behind
    door_w, door_h = int(380 * sc), int(620 * sc)
    door_x = cx - door_w // 2
    door_y = cy - door_h // 2
    # Glow behind door
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.rectangle((door_x - 80, door_y - 80, door_x + door_w + 80, door_y + door_h + 80),
                 fill=(*ORANGE[:3], int(120 * op)))
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    canvas.alpha_composite(glow)
    # Door frame
    d.rectangle((door_x, door_y, door_x + door_w, door_y + door_h),
                fill=(0, 0, 0, int(180 * op)),
                outline=(*ORANGE[:3], int(255 * op)), width=int(10 * sc))
    # Caption above
    draw_bellefair_with_shadow(canvas, "LEAN INTO", cx, cy - 500, int(110 * sc),
                           color=WHITE, shadow=ORANGE, opacity=op)
    draw_bellefair_with_shadow(canvas, "FEAR", cx, cy + 480, int(220 * sc),
                           color=ORANGE, shadow=ORANGE_DARK, opacity=op)
    return canvas

def render_share_secrets(t, dur=3.0):
    """Open vault / unlocked padlock graphic — Share your secrets."""
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Unlock symbol (big)
    f = ANTON(int(380 * sc))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.text((cx, cy), "🔓", font=f, anchor="mm", fill=(*ORANGE[:3], int(255 * op)))
    canvas.alpha_composite(layer)
    # Caption
    draw_bellefair_with_shadow(canvas, "SHARE", cx, cy - 380, int(160 * sc),
                           color=WHITE, shadow=ORANGE, opacity=op)
    draw_bellefair_with_shadow(canvas, "EVERY SECRET", cx, cy + 380, int(140 * sc),
                           color=ORANGE, shadow=ORANGE_DARK, opacity=op)
    return canvas

def render_fafo(t, dur=2.5):
    """FUCK AROUND AND FIND OUT — block-letter slate."""
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Phase: each line slams in
    if t > 0.0:
        op1 = ease_out_cubic(min(t / 0.3, 1.0)) * op
        draw_bellefair_with_shadow(canvas, "FUCK", cx, cy - 350, int(220 * sc),
                               color=WHITE, shadow=RED, opacity=op1)
    if t > 0.3:
        op2 = ease_out_cubic(min((t - 0.3) / 0.3, 1.0)) * op
        draw_bellefair_with_shadow(canvas, "AROUND", cx, cy - 150, int(200 * sc),
                               color=ORANGE, shadow=ORANGE_DARK, opacity=op2)
    if t > 0.6:
        op3 = ease_out_cubic(min((t - 0.6) / 0.3, 1.0)) * op
        draw_bellefair_with_shadow(canvas, "FIND", cx, cy + 100, int(220 * sc),
                               color=WHITE, shadow=RED, opacity=op3)
    if t > 0.9:
        op4 = ease_out_cubic(min((t - 0.9) / 0.3, 1.0)) * op
        draw_bellefair_with_shadow(canvas, "OUT.", cx, cy + 320, int(280 * sc),
                               color=ORANGE, shadow=ORANGE_DARK, opacity=op4)
    return canvas

def render_problems_solutions(t, dur=3.0):
    """Find problems → give solutions. Magnifier → lightbulb."""
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Magnifying glass emoji (left/top)
    if t < 1.5:
        mag_op = op
        f = ANTON(int(280 * sc))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((cx - 200, cy), "🔍", font=f, anchor="mm",
                                     fill=(*WHITE[:3], int(255 * mag_op)))
        canvas.alpha_composite(layer)
        draw_bellefair_with_shadow(canvas, "FIND", cx - 200, cy - 300, int(120 * sc),
                               color=WHITE, shadow=ORANGE, opacity=mag_op)
        draw_bellefair_with_shadow(canvas, "PROBLEMS", cx - 200, cy + 280, int(80 * sc),
                               color=ORANGE, shadow=ORANGE_DARK, opacity=mag_op)
    if t > 1.0:
        # arrow appearing
        arr_op = ease_out_cubic(min((t - 1.0) / 0.5, 1.0)) * op
        f_arr = ANTON(int(140 * sc))
        ImageDraw.Draw(canvas).text((cx, cy), "→", font=f_arr, anchor="mm",
                                      fill=(*ORANGE[:3], int(255 * arr_op)))
    if t > 1.5:
        bulb_op = ease_out_cubic(min((t - 1.5) / 0.5, 1.0)) * op
        f = ANTON(int(280 * sc))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((cx + 200, cy), "💡", font=f, anchor="mm",
                                     fill=(*WHITE[:3], int(255 * bulb_op)))
        canvas.alpha_composite(layer)
        draw_bellefair_with_shadow(canvas, "GIVE", cx + 200, cy - 300, int(120 * sc),
                               color=WHITE, shadow=ORANGE, opacity=bulb_op)
        draw_bellefair_with_shadow(canvas, "SOLUTIONS", cx + 200, cy + 280, int(80 * sc),
                               color=ORANGE, shadow=ORANGE_DARK, opacity=bulb_op)
    return canvas

# ============================================================
# REGISTRY
# ============================================================
CONCEPTS = {
    "closer_to_money":      (render_closer_to_money, 3.0),
    "400_to_4000":          (render_400_to_4000, 3.5),
    "victim_vs_creator":    (render_victim_vs_creator, 3.0),
    "money_while_sleep":    (render_money_while_sleep, 3.5),
    "show_dont_tell":       (render_show_dont_tell, 2.5),
    "responsibility":       (render_responsibility_results, 3.0),
    "lean_into_fear":       (render_lean_into_fear, 3.0),
    "share_secrets":        (render_share_secrets, 3.0),
    "problems_solutions":   (render_problems_solutions, 3.0),
}

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
    print(f"Building {len(CONCEPTS)} concept Remotion graphics...")
    for name, (fn, dur) in CONCEPTS.items():
        render_clip(name, fn, dur)
    print(f"\n✓ Done → {OUT}")
