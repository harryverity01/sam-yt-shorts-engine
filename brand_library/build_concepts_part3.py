#!/usr/bin/env python3
"""PART 3 — 14 additional Sam-brand graphics from his full YouTube catalog.

8 concept clips (current hooks not in 87-min interview):
  thirty_k_in_2_days, five_hundred_to_5000, yacht_week_badge, nike_ping_pong,
  one_fifty_calls, five_hundred_k_followers, replaced_three_vas, dj_to_photographer

5 DM trigger cards (Sam's standard CTA mechanic):
  comment_clients, comment_grow, comment_audit, comment_system, comment_ai

1 reusable handle lower-third:
  handle_sameyeam_secrets
"""
import os, math, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from build_concepts import (
    W, H, FPS, OUT, TMP,
    ORANGE, ORANGE_DARK, NAVY, NAVY_LIGHT, CREAM, INK, RED, WHITE, DIM,
    ANTON, MONT_B, MONT_R, BELLEFAIR,
    ease_out_cubic, envelope, draw_bellefair_with_shadow, draw_bellefair_with_shadow,
    render_clip,
)

GREEN = (60, 200, 120, 255)
IG_PINK = (228, 64, 95, 255)
IG_GREY = (240, 240, 242, 255)
IG_TEXT = (38, 38, 38, 255)


# ---- PIL-drawn glyphs (avoid emoji font fallback to hollow X) ----
def draw_phone_glyph(d, cx, cy, size, color, opacity=1.0):
    """Simple handset shape — earpiece, mouthpiece, curved cord."""
    a = int(255 * opacity)
    col = (*color[:3], a)
    s = size / 100.0
    # Handset rotated ~ -30deg drawn as two ellipses + connector
    ear = (cx - int(60 * s), cy - int(40 * s),
           cx - int(20 * s), cy + int(0 * s))
    mouth = (cx + int(20 * s), cy + int(20 * s),
             cx + int(60 * s), cy + int(60 * s))
    d.ellipse(ear, fill=col)
    d.ellipse(mouth, fill=col)
    # Connector bar
    d.line([(cx - int(30 * s), cy - int(20 * s)),
            (cx + int(40 * s), cy + int(40 * s))],
           fill=col, width=max(3, int(14 * s)))
    # Sound waves above ear
    for r in [int(75 * s), int(105 * s)]:
        d.arc((cx - int(60 * s) - r, cy - int(60 * s) - r,
               cx - int(60 * s) + r, cy - int(60 * s) + r),
              start=200, end=320,
              fill=col, width=max(2, int(6 * s)))


def draw_person_glyph(d, cx, cy, size, color, opacity=1.0):
    """Round head + shoulders silhouette."""
    a = int(255 * opacity)
    col = (*color[:3], a)
    s = size / 100.0
    # Head
    head_r = int(35 * s)
    d.ellipse((cx - head_r, cy - int(50 * s) - head_r,
               cx + head_r, cy - int(50 * s) + head_r),
              fill=col)
    # Shoulders (rounded trapezoid via pieslice + rectangle)
    sh_w = int(110 * s)
    sh_h = int(70 * s)
    sh_top = cy + int(0 * s)
    d.pieslice((cx - sh_w // 2, sh_top, cx + sh_w // 2, sh_top + sh_h * 2),
               start=180, end=360, fill=col)


# ============================================================
# 1. $30,000 IN 2 DAYS — current hero stat
# ============================================================
def render_thirty_k_in_2_days(t, dur=3.2):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Burst rays
    rays = 14
    for i in range(rays):
        ang = (i / rays) * 2 * math.pi + t * 0.4
        x2 = cx + math.cos(ang) * 720
        y2 = cy + math.sin(ang) * 720
        d.line([(cx, cy), (x2, y2)], fill=(*ORANGE[:3], int(50 * op)), width=8)
    # Main number — counter from 0 to 30k
    if t > 0.1:
        n_op = ease_out_cubic(min((t - 0.1) / 0.45, 1.0)) * op
        progress = min((t - 0.1) / 1.0, 1.0)
        val = int(ease_out_cubic(progress) * 30000)
        pulse = 1.0 + 0.04 * math.sin(2 * math.pi * t / 1.2)
        draw_bellefair_with_shadow(canvas, f"${val:,}", cx, cy - 80,
                               int(240 * sc * pulse),
                               color=ORANGE, shadow=ORANGE_DARK, opacity=n_op)
    if t > 1.0:
        s_op = ease_out_cubic(min((t - 1.0) / 0.4, 1.0)) * op
        draw_bellefair_with_shadow(canvas, "IN 2 DAYS", cx, cy + 180, int(180 * sc),
                               color=WHITE, shadow=ORANGE_DARK, opacity=s_op)
    # Sub: 14 leads / 10 closed
    if t > 1.6:
        l_op = ease_out_cubic(min((t - 1.6) / 0.4, 1.0)) * op
        f = MONT_B(int(52 * sc))
        d.text((cx, cy + 480), "14 LEADS · 10 CLOSED", font=f, anchor="mm",
               fill=(*CREAM[:3], int(255 * l_op)))
    return canvas


# ============================================================
# 2. $500 → $5,000 (parallel of $400→$4000)
# ============================================================
def render_five_hundred_to_5000(t, dur=3.5):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    if t < 1.2:
        p_op = ease_out_cubic(min(t / 0.4, 1.0)) * op
        draw_bellefair_with_shadow(canvas, "$500", cx, cy - 150, int(280 * sc),
                               color=WHITE, shadow=ORANGE, opacity=p_op)
    elif t < 2.0:
        p = (t - 1.2) / 0.8
        draw_bellefair_with_shadow(canvas, "$500", cx, cy - 220, int(180 * sc),
                               color=DIM, shadow=DIM, opacity=(1 - p * 0.6) * op)
        f_arrow = ANTON(int(180 * sc))
        d.text((cx, cy - 20), "→", font=f_arrow, anchor="mm",
               fill=(*ORANGE[:3], int(255 * op)))
    else:
        big_op = ease_out_cubic(min((t - 2.0) / 0.4, 1.0)) * op
        pulse = 1.0 + 0.04 * math.sin(2 * math.pi * (t - 2.0) / 0.8)
        draw_bellefair_with_shadow(canvas, "$500", cx, cy - 360, int(140 * sc),
                               color=DIM, shadow=DIM, opacity=0.5 * op)
        f_arrow = ANTON(int(140 * sc))
        d.text((cx, cy - 220), "→", font=f_arrow, anchor="mm",
               fill=(*ORANGE[:3], int(200 * op)))
        draw_bellefair_with_shadow(canvas, "$5,000", cx, cy + 60,
                               int(340 * sc * pulse),
                               color=ORANGE, shadow=ORANGE_DARK, opacity=big_op)
        f_sub = MONT_B(int(60 * sc))
        d.text((cx, cy + 380), "10X PROJECT", font=f_sub, anchor="mm",
               fill=(*WHITE[:3], int(255 * big_op)))
    return canvas


# ============================================================
# 3. YACHT WEEK BADGE
# ============================================================
def render_yacht_week_badge(t, dur=3.0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Navy badge
    bw, bh = int(820 * sc), int(560 * sc)
    bx, by = cx - bw // 2, cy - bh // 2
    d.rounded_rectangle((bx, by, bx + bw, by + bh), radius=int(40 * sc),
                        fill=(*NAVY[:3], int(245 * op)),
                        outline=(*ORANGE[:3], int(255 * op)), width=int(8 * sc))
    # Sail triangle (simple)
    sail_top = (cx, by + 90)
    sail_bl = (cx - 70, by + 230)
    sail_br = (cx + 70, by + 230)
    d.polygon([sail_top, sail_bl, sail_br], fill=(*ORANGE[:3], int(255 * op)))
    # Mast
    d.line([(cx, by + 90), (cx, by + 280)], fill=(*WHITE[:3], int(255 * op)), width=int(6 * sc))
    # Boat hull
    d.polygon([(cx - 110, by + 280), (cx + 110, by + 280), (cx + 80, by + 320), (cx - 80, by + 320)],
              fill=(*WHITE[:3], int(255 * op)))
    if t > 0.2:
        t_op = ease_out_cubic(min((t - 0.2) / 0.4, 1.0)) * op
        draw_bellefair_with_shadow(canvas, "YACHT", cx, by + int(390 * sc), int(120 * sc),
                               color=WHITE, shadow=ORANGE, opacity=t_op)
        draw_bellefair_with_shadow(canvas, "WEEK", cx, by + int(500 * sc), int(120 * sc),
                               color=ORANGE, shadow=ORANGE_DARK, opacity=t_op)
    return canvas


# ============================================================
# 4. NIKE + PING PONG — origin moment
# ============================================================
def render_nike_ping_pong(t, dur=3.0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Nike swoosh — simplified curve
    swoosh_w = int(420 * sc)
    sx, sy = cx - swoosh_w // 2, cy - 480
    # Approximate swoosh with two arcs
    d.polygon([
        (sx, sy + 60), (sx + 50, sy + 80),
        (sx + swoosh_w - 60, sy), (sx + swoosh_w, sy + 10),
        (sx + 80, sy + 120), (sx, sy + 100),
    ], fill=(*WHITE[:3], int(255 * op)))
    # Ping pong paddle (orange circle + black handle)
    if t > 0.3:
        p_op = ease_out_cubic(min((t - 0.3) / 0.4, 1.0)) * op
        wobble = math.sin(2 * math.pi * t * 1.5) * 10
        pad_cx, pad_cy = cx, cy - 80 + int(wobble)
        r = int(180 * sc)
        d.ellipse((pad_cx - r, pad_cy - r, pad_cx + r, pad_cy + r),
                  fill=(*ORANGE[:3], int(255 * p_op)),
                  outline=(*ORANGE_DARK[:3], int(255 * p_op)), width=int(8 * sc))
        # Handle
        hw = int(50 * sc)
        d.rectangle((pad_cx - hw // 2, pad_cy + r, pad_cx + hw // 2, pad_cy + r + int(180 * sc)),
                    fill=(20, 20, 20, int(255 * p_op)))
        # White ball
        ball_cx = pad_cx + int(120 * sc + wobble * 2)
        d.ellipse((ball_cx - 30, pad_cy - 130, ball_cx + 30, pad_cy - 70),
                  fill=(*WHITE[:3], int(255 * p_op)))
    if t > 1.0:
        tx_op = ease_out_cubic(min((t - 1.0) / 0.4, 1.0)) * op
        draw_bellefair_with_shadow(canvas, "MADE 3X MORE", cx, cy + 480, int(110 * sc),
                               color=WHITE, shadow=ORANGE, opacity=tx_op)
        draw_bellefair_with_shadow(canvas, "THAN ME", cx, cy + 620, int(140 * sc),
                               color=ORANGE, shadow=ORANGE_DARK, opacity=tx_op)
    return canvas


# ============================================================
# 5. 150 CALLS FROM 1 POST
# ============================================================
def render_one_fifty_calls(t, dur=3.0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Big counter
    if t < 1.4:
        progress = ease_out_cubic(min(t / 1.2, 1.0))
        val = int(progress * 150)
        n_op = ease_out_cubic(min(t / 0.4, 1.0)) * op
        pulse = 1.0 + 0.04 * math.sin(2 * math.pi * t / 0.9)
        draw_bellefair_with_shadow(canvas, str(val), cx, cy - 80,
                               int(420 * sc * pulse),
                               color=ORANGE, shadow=ORANGE_DARK, opacity=n_op)
    else:
        pulse = 1.0 + 0.03 * math.sin(2 * math.pi * t / 0.9)
        draw_bellefair_with_shadow(canvas, "150", cx, cy - 80,
                               int(420 * sc * pulse),
                               color=ORANGE, shadow=ORANGE_DARK, opacity=op)
    if t > 0.6:
        c_op = ease_out_cubic(min((t - 0.6) / 0.4, 1.0)) * op
        draw_bellefair_with_shadow(canvas, "CALLS", cx, cy + 240, int(180 * sc),
                               color=WHITE, shadow=ORANGE_DARK, opacity=c_op)
    if t > 1.2:
        s_op = ease_out_cubic(min((t - 1.2) / 0.4, 1.0)) * op
        f = MONT_B(int(56 * sc))
        d.text((cx, cy + 440), "FROM 1 POST", font=f, anchor="mm",
               fill=(*CREAM[:3], int(255 * s_op)))
    # Phone ringing icons in corners (PIL-drawn, not emoji)
    for i, (px, py) in enumerate([(cx - 380, cy - 480), (cx + 380, cy - 480)]):
        wig = math.sin(2 * math.pi * (t + i * 0.5)) * 15
        draw_phone_glyph(d, px + int(wig), py, int(140 * sc), ORANGE, opacity=0.85 * op)
    return canvas


# ============================================================
# 6. 500K FOLLOWERS FROM 1 POST
# ============================================================
def render_five_hundred_k_followers(t, dur=3.0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    if t < 1.4:
        progress = ease_out_cubic(min(t / 1.2, 1.0))
        val = int(progress * 500)
        n_op = ease_out_cubic(min(t / 0.4, 1.0)) * op
        pulse = 1.0 + 0.04 * math.sin(2 * math.pi * t / 0.9)
        draw_bellefair_with_shadow(canvas, f"{val}K", cx, cy - 80,
                               int(380 * sc * pulse),
                               color=ORANGE, shadow=ORANGE_DARK, opacity=n_op)
    else:
        pulse = 1.0 + 0.03 * math.sin(2 * math.pi * t / 0.9)
        draw_bellefair_with_shadow(canvas, "500K", cx, cy - 80,
                               int(380 * sc * pulse),
                               color=ORANGE, shadow=ORANGE_DARK, opacity=op)
    if t > 0.7:
        f_op = ease_out_cubic(min((t - 0.7) / 0.4, 1.0)) * op
        draw_bellefair_with_shadow(canvas, "FOLLOWERS", cx, cy + 220, int(140 * sc),
                               color=WHITE, shadow=ORANGE_DARK, opacity=f_op)
    if t > 1.3:
        s_op = ease_out_cubic(min((t - 1.3) / 0.4, 1.0)) * op
        f = MONT_B(int(56 * sc))
        d.text((cx, cy + 420), "FROM 1 POST", font=f, anchor="mm",
               fill=(*CREAM[:3], int(255 * s_op)))
    # Person icons rising (PIL-drawn)
    for i in range(5):
        seed = i * 0.31
        t_local = (t + seed) % 1.5
        py = cy - 540 + int((1 - t_local / 1.5) * 250)
        px = cx - 400 + i * 200
        draw_person_glyph(d, px, py, int(80 * sc), ORANGE, opacity=0.7 * op)
    return canvas


# ============================================================
# 7. REPLACED 3 VAs / 2,000 LEADS
# ============================================================
def render_replaced_three_vas(t, dur=3.0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Top stat: 2,000 LEADS
    if t > 0.1:
        n_op = ease_out_cubic(min((t - 0.1) / 0.4, 1.0)) * op
        draw_bellefair_with_shadow(canvas, "2,000", cx, cy - 580, int(220 * sc),
                               color=ORANGE, shadow=ORANGE_DARK, opacity=n_op)
        f = MONT_B(int(56 * sc))
        d.text((cx, cy - 380), "LEADS", font=f, anchor="mm",
               fill=(*WHITE[:3], int(255 * n_op)))
    # Three VA icons being crossed out one-by-one
    for i in range(3):
        x_off = (i - 1) * 280
        px, py = cx + x_off, cy - 40
        appear = ease_out_cubic(min(max((t - 0.4 - i * 0.15) / 0.3, 0.0), 1.0)) * op
        # Circle bg
        r = int(140 * sc)
        d.ellipse((px - r, py - r, px + r, py + r),
                  fill=(*NAVY_LIGHT[:3], int(220 * appear)),
                  outline=(*ORANGE[:3], int(255 * appear)), width=int(5 * sc))
        # Person glyph (PIL-drawn)
        draw_person_glyph(d, px, py + 10, int(170 * sc), WHITE, opacity=appear)
        # Red X crossing out
        cross_t = t - 1.2 - i * 0.2
        if cross_t > 0:
            c_op = ease_out_cubic(min(cross_t / 0.3, 1.0)) * op
            d.line([(px - r, py - r), (px + r, py + r)],
                   fill=(*RED[:3], int(255 * c_op)), width=int(14 * sc))
            d.line([(px - r, py + r), (px + r, py - r)],
                   fill=(*RED[:3], int(255 * c_op)), width=int(14 * sc))
    if t > 1.9:
        s_op = ease_out_cubic(min((t - 1.9) / 0.4, 1.0)) * op
        draw_bellefair_with_shadow(canvas, "REPLACED 3 VAs", cx, cy + 380, int(120 * sc),
                               color=WHITE, shadow=ORANGE, opacity=s_op)
        f2 = MONT_B(int(48 * sc))
        d.text((cx, cy + 560), "WITH ONE AI AGENT", font=f2, anchor="mm",
               fill=(*ORANGE[:3], int(255 * s_op)))
    return canvas


# ============================================================
# 8. DJ → PHOTOGRAPHER (origin)
# ============================================================
def render_dj_to_photographer(t, dur=3.5):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # DJ deck (left/top phase)
    deck_alpha = 1.0 if t < 1.5 else max(0.0, 1.0 - (t - 1.5) / 0.6)
    if deck_alpha > 0:
        # Turntable circle (vinyl)
        vc_x, vc_y = cx, cy - 320
        r = int(220 * sc)
        # Outer vinyl
        d.ellipse((vc_x - r, vc_y - r, vc_x + r, vc_y + r),
                  fill=(20, 20, 24, int(255 * op * deck_alpha)))
        # Concentric grooves
        for gr in range(int(180 * sc), 40, -30):
            d.ellipse((vc_x - gr, vc_y - gr, vc_x + gr, vc_y + gr),
                      outline=(50, 50, 55, int(180 * op * deck_alpha)), width=2)
        # Orange centre label spinning
        spin = t * math.pi * 2
        lab_r = int(70 * sc)
        d.ellipse((vc_x - lab_r, vc_y - lab_r, vc_x + lab_r, vc_y + lab_r),
                  fill=(*ORANGE[:3], int(255 * op * deck_alpha)))
        # Small dot to show spin
        dot_x = vc_x + int(math.cos(spin) * lab_r * 0.6)
        dot_y = vc_y + int(math.sin(spin) * lab_r * 0.6)
        d.ellipse((dot_x - 8, dot_y - 8, dot_x + 8, dot_y + 8),
                  fill=(*NAVY[:3], int(255 * op * deck_alpha)))
        # DJ label
        f = MONT_B(int(64 * sc))
        d.text((cx, vc_y + 320), "DJ", font=f, anchor="mm",
               fill=(*DIM[:3], int(255 * op * deck_alpha)))
    # Arrow transition
    if 1.2 < t < 2.4:
        arr_op = ease_out_cubic(min((t - 1.2) / 0.3, 1.0)) * op
        f_arr = ANTON(int(180 * sc))
        d.text((cx, cy + 40), "→", font=f_arr, anchor="mm",
               fill=(*ORANGE[:3], int(255 * arr_op)))
    # Camera (right/bottom phase)
    if t > 1.8:
        cam_op = ease_out_cubic(min((t - 1.8) / 0.4, 1.0)) * op
        cam_cx, cam_cy = cx, cy + 380
        bw, bh = int(380 * sc), int(240 * sc)
        # Body
        d.rounded_rectangle((cam_cx - bw // 2, cam_cy - bh // 2,
                             cam_cx + bw // 2, cam_cy + bh // 2),
                            radius=int(20 * sc),
                            fill=(*NAVY[:3], int(255 * cam_op)),
                            outline=(*ORANGE[:3], int(255 * cam_op)),
                            width=int(6 * sc))
        # Lens
        lr = int(100 * sc)
        d.ellipse((cam_cx - lr, cam_cy - lr, cam_cx + lr, cam_cy + lr),
                  fill=(20, 20, 24, int(255 * cam_op)),
                  outline=(*ORANGE[:3], int(255 * cam_op)), width=int(6 * sc))
        d.ellipse((cam_cx - lr // 2, cam_cy - lr // 2, cam_cx + lr // 2, cam_cy + lr // 2),
                  fill=(*ORANGE_DARK[:3], int(255 * cam_op)))
        # Flash bulb
        d.rectangle((cam_cx + bw // 2 - 60, cam_cy - bh // 2 - 30,
                     cam_cx + bw // 2 - 20, cam_cy - bh // 2 + 10),
                    fill=(*WHITE[:3], int(255 * cam_op)))
        f = MONT_B(int(56 * sc))
        d.text((cam_cx, cam_cy + bh // 2 + 80), "PHOTOGRAPHER", font=f, anchor="mm",
               fill=(*ORANGE[:3], int(255 * cam_op)))
    return canvas


# ============================================================
# DM TRIGGER CARDS — 5 variants
# ============================================================
def _render_dm_card(t, dur, keyword):
    """Sam-brand DM trigger card — navy pill, orange border, Anton keyword."""
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Navy pill with orange border
    bw, bh = int(940 * sc), int(680 * sc)
    bx, by = cx - bw // 2, cy - bh // 2
    # Shadow
    d.rounded_rectangle((bx + 14, by + 16, bx + bw + 14, by + bh + 16),
                        radius=int(50 * sc),
                        fill=(0, 0, 0, int(110 * op)))
    # Navy card
    d.rounded_rectangle((bx, by, bx + bw, by + bh), radius=int(50 * sc),
                        fill=(*NAVY[:3], int(250 * op)),
                        outline=(*ORANGE[:3], int(255 * op)), width=int(8 * sc))
    # "COMMENT" header in orange Anton (small + skewed)
    draw_bellefair_with_shadow(canvas, "COMMENT",
                           cx, by + int(120 * sc),
                           int(110 * sc),
                           color=ORANGE, shadow=ORANGE_DARK, opacity=op)
    # Divider line
    d.line([(bx + int(80 * sc), by + int(220 * sc)),
            (bx + bw - int(80 * sc), by + int(220 * sc))],
           fill=(*ORANGE[:3], int(180 * op)), width=int(4 * sc))
    # The keyword — BIG Anton, white text with orange shadow (Sam's house style)
    if t > 0.2:
        k_op = ease_out_cubic(min((t - 0.2) / 0.4, 1.0)) * op
        pulse = 1.0 + 0.04 * math.sin(2 * math.pi * t / 0.8)
        # Surrounding orange Anton quote marks
        f_q = ANTON(int(180 * sc))
        d.text((bx + int(60 * sc), by + int(360 * sc)), "“", font=f_q, anchor="lm",
               fill=(*ORANGE[:3], int(255 * k_op)))
        d.text((bx + bw - int(60 * sc), by + int(440 * sc)), "”", font=f_q, anchor="rm",
               fill=(*ORANGE[:3], int(255 * k_op)))
        # Keyword sized down for long words
        size = int(220 * sc * pulse)
        if len(keyword) >= 6: size = int(180 * sc * pulse)
        if len(keyword) >= 7: size = int(150 * sc * pulse)
        draw_bellefair_with_shadow(canvas, keyword, cx, by + int(400 * sc),
                               size,
                               color=WHITE, shadow=ORANGE, opacity=k_op)
    # Footer
    if t > 0.7:
        f_op = ease_out_cubic(min((t - 0.7) / 0.4, 1.0)) * op
        f_ft = MONT_B(int(38 * sc))
        d.text((cx, by + bh - int(80 * sc)),
               "& I'LL DM YOU THE BREAKDOWN",
               font=f_ft, anchor="mm",
               fill=(*CREAM[:3], int(255 * f_op)))
    return canvas


def render_comment_clients(t, dur=3.0): return _render_dm_card(t, dur, "CLIENTS")
def render_comment_grow(t, dur=3.0):    return _render_dm_card(t, dur, "GROW")
def render_comment_audit(t, dur=3.0):   return _render_dm_card(t, dur, "AUDIT")
def render_comment_system(t, dur=3.0):  return _render_dm_card(t, dur, "SYSTEM")
def render_comment_ai(t, dur=3.0):      return _render_dm_card(t, dur, "AI")


# ============================================================
# HANDLE LOWER-THIRD — @sameyeam.secrets
# ============================================================
def render_handle_sameyeam_secrets(t, dur=3.0):
    """Bottom-of-frame Instagram handle badge. Slides in from left."""
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    # Slide in
    slide = ease_out_cubic(min(t / 0.5, 1.0))
    bw, bh = int(980 * sc), int(180 * sc)
    by = H - int(380 * sc)  # safe-zone above captions
    bx_target = (W - bw) // 2
    bx = int(-bw + (bx_target + bw) * slide)
    d = ImageDraw.Draw(canvas)
    # Shadow
    d.rounded_rectangle((bx + 8, by + 12, bx + bw + 8, by + bh + 12),
                        radius=int(30 * sc),
                        fill=(0, 0, 0, int(120 * op)))
    # Navy pill
    d.rounded_rectangle((bx, by, bx + bw, by + bh), radius=int(30 * sc),
                        fill=(*NAVY[:3], int(245 * op)),
                        outline=(*ORANGE[:3], int(255 * op)), width=int(5 * sc))
    # Sam-orange icon square with @ symbol (Sam brand, not IG-pink)
    ig_r = int(60 * sc)
    ig_cx = bx + int(80 * sc)
    ig_cy = by + bh // 2
    d.rounded_rectangle((ig_cx - ig_r, ig_cy - ig_r, ig_cx + ig_r, ig_cy + ig_r),
                        radius=int(20 * sc),
                        fill=(*ORANGE[:3], int(255 * op)))
    # @ glyph instead of empty circle
    f_at = MONT_B(int(80 * sc))
    d.text((ig_cx, ig_cy), "@", font=f_at, anchor="mm",
           fill=(*NAVY[:3], int(255 * op)))
    # Handle text — sized to leave room for FOLLOW pill
    f = MONT_B(int(48 * sc))
    d.text((bx + int(170 * sc), ig_cy), "@sameyeam.secrets",
           font=f, anchor="lm",
           fill=(*WHITE[:3], int(255 * op)))
    # FOLLOW CTA pill on right
    if t > 0.6:
        c_op = ease_out_cubic(min((t - 0.6) / 0.4, 1.0)) * op
        pulse = 1.0 + 0.04 * math.sin(2 * math.pi * t / 0.6)
        pw, ph = int(170 * sc * pulse), int(70 * sc * pulse)
        px = bx + bw - pw - int(20 * sc)
        py = by + (bh - ph) // 2
        d.rounded_rectangle((px, py, px + pw, py + ph), radius=int(20 * sc),
                            fill=(*ORANGE[:3], int(255 * c_op)))
        f_c = MONT_B(int(34 * sc))
        d.text((px + pw // 2, py + ph // 2), "FOLLOW", font=f_c, anchor="mm",
               fill=(*NAVY[:3], int(255 * c_op)))
    return canvas


# ============================================================
# REGISTRY
# ============================================================
CONCEPTS_PART3 = {
    # 8 new concepts
    "thirty_k_in_2_days":         (render_thirty_k_in_2_days,         3.2),
    "five_hundred_to_5000":       (render_five_hundred_to_5000,       3.5),
    "yacht_week_badge":           (render_yacht_week_badge,           3.0),
    "nike_ping_pong":             (render_nike_ping_pong,             3.0),
    "one_fifty_calls":            (render_one_fifty_calls,            3.0),
    "five_hundred_k_followers":   (render_five_hundred_k_followers,   3.0),
    "replaced_three_vas":         (render_replaced_three_vas,         3.0),
    "dj_to_photographer":         (render_dj_to_photographer,         3.5),
    # 5 DM trigger cards
    "comment_clients":            (render_comment_clients,            3.0),
    "comment_grow":               (render_comment_grow,               3.0),
    "comment_audit":              (render_comment_audit,              3.0),
    "comment_system":             (render_comment_system,             3.0),
    "comment_ai":                 (render_comment_ai,                 3.0),
    # 1 reusable lower-third
    "handle_sameyeam_secrets":    (render_handle_sameyeam_secrets,    3.0),
}


if __name__ == "__main__":
    print(f"Building {len(CONCEPTS_PART3)} part-3 graphics...")
    for name, (fn, dur) in CONCEPTS_PART3.items():
        render_clip(name, fn, dur)
    print(f"\n✓ Done → {OUT}")
