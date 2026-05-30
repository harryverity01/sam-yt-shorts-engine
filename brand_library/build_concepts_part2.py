#!/usr/bin/env python3
"""Build the REMAINING 20 concept Remotion graphics for Sam's brand library.

Reuses helpers (envelope, draw_bellefair_with_shadow, palette, fonts) from
build_concepts.py so style stays consistent with the first 10.
"""
import os, math, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
from build_concepts import (
    W, H, FPS, OUT, TMP,
    ORANGE, ORANGE_DARK, NAVY, NAVY_LIGHT, CREAM, INK, RED, WHITE, DIM,
    ANTON, MONT_B, MONT_R, BELLEFAIR,
    ease_out_cubic, envelope, draw_bellefair_with_shadow, draw_bellefair_with_shadow,
    render_clip,
)

GREEN = (60, 200, 120, 255)
BLUE = (80, 140, 230, 255)
GOLD = (230, 190, 80, 255)


# ============================================================
# 7. 150K / 4K / 12 MONTHS GROWTH-CHART TRIO
# ============================================================
def render_growth_trio(t, dur=3.5):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Three stats stacked, each pops in sequentially
    stats = [
        ("4K", "WHERE WE STARTED", DIM, cy - 480, 0.0),
        ("12", "MONTHS LATER", WHITE, cy - 60, 0.6),
        ("150K", "SUBSCRIBERS", ORANGE, cy + 380, 1.2),
    ]
    for big, sub, color, y, t0 in stats:
        if t < t0: continue
        local_op = ease_out_cubic(min((t - t0) / 0.4, 1.0)) * op
        big_size = int(260 * sc) if color == ORANGE else int(200 * sc)
        shadow = ORANGE_DARK if color == ORANGE else (color if color == DIM else ORANGE)
        draw_bellefair_with_shadow(canvas, big, cx, y, big_size,
                               color=color, shadow=shadow, opacity=local_op)
        f = MONT_B(int(48 * sc))
        d.text((cx, y + 160), sub, font=f, anchor="mm",
               fill=(*CREAM[:3], int(255 * local_op)))
    # Upward arrow lining the right side once 150K is in
    if t > 1.6:
        arr_op = ease_out_cubic(min((t - 1.6) / 0.4, 1.0)) * op
        f_arr = ANTON(int(220 * sc))
        ImageDraw.Draw(canvas).text((cx + 380, cy - 220), "↗", font=f_arr,
                                     anchor="mm",
                                     fill=(*ORANGE[:3], int(255 * arr_op)))
    return canvas


# ============================================================
# 8. 1 MILLION VIEWS TROPHY CARD
# ============================================================
def render_one_million_views(t, dur=3.0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Burst rays behind
    rays = 16
    for i in range(rays):
        ang = (i / rays) * 2 * math.pi + t * 0.3
        x2 = cx + math.cos(ang) * 700
        y2 = cy + math.sin(ang) * 700
        d.line([(cx, cy), (x2, y2)], fill=(*ORANGE[:3], int(60 * op)), width=8)
    # Big number lands
    if t > 0.2:
        n_op = ease_out_cubic(min((t - 0.2) / 0.4, 1.0)) * op
        pulse = 1.0 + 0.03 * math.sin(2 * math.pi * t / 1.2)
        draw_bellefair_with_shadow(canvas, "1,000,000", cx, cy - 60,
                               int(220 * sc * pulse),
                               color=ORANGE, shadow=ORANGE_DARK, opacity=n_op)
    if t > 0.6:
        v_op = ease_out_cubic(min((t - 0.6) / 0.4, 1.0)) * op
        draw_bellefair_with_shadow(canvas, "VIEWS", cx, cy + 160, int(180 * sc),
                               color=WHITE, shadow=ORANGE_DARK, opacity=v_op)
    # 🏆 trophy emoji
    if t > 1.0:
        tr_op = ease_out_cubic(min((t - 1.0) / 0.4, 1.0)) * op
        f = ANTON(int(220 * sc))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((cx, cy - 480), "🏆", font=f, anchor="mm",
                                     fill=(*GOLD[:3], int(255 * tr_op)))
        canvas.alpha_composite(layer)
    return canvas


# ============================================================
# 11. STRIPE LOGO + $10,000 IN FEES
# ============================================================
def render_stripe_fees(t, dur=3.0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Stripe logo block (rounded rect with "stripe")
    block_w, block_h = int(560 * sc), int(220 * sc)
    bx, by = cx - block_w // 2, cy - 480
    d.rounded_rectangle((bx, by, bx + block_w, by + block_h),
                        radius=int(40 * sc),
                        fill=(99, 91, 255, int(255 * op)))
    f_stripe = MONT_B(int(110 * sc))
    d.text((cx, by + block_h // 2), "stripe", font=f_stripe, anchor="mm",
           fill=(*WHITE[:3], int(255 * op)))
    # Falling $ symbols (animated)
    n_drops = 8
    for i in range(n_drops):
        seed = i * 1.371
        dx = ((seed * 137) % W) - W // 2
        progress = ((t * 0.7 + seed) % 1.5) / 1.5
        dy = -200 + progress * 800
        f_d = ANTON(int(80 * sc))
        ImageDraw.Draw(canvas).text((cx + dx, cy - 100 + int(dy)), "$",
                                      font=f_d, anchor="mm",
                                      fill=(*ORANGE[:3], int(180 * op * (1 - progress))))
    # Big stat
    if t > 0.6:
        s_op = ease_out_cubic(min((t - 0.6) / 0.4, 1.0)) * op
        draw_bellefair_with_shadow(canvas, "$10,000", cx, cy + 280, int(260 * sc),
                               color=ORANGE, shadow=ORANGE_DARK, opacity=s_op)
        f = MONT_B(int(54 * sc))
        d.text((cx, cy + 480), "IN FEES", font=f, anchor="mm",
               fill=(*WHITE[:3], int(255 * s_op)))
    return canvas


# ============================================================
# 12. "THE GAME" / HORMOZI REFERENCE CARD
# ============================================================
def render_the_game(t, dur=3.0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Book-cover style block
    book_w, book_h = int(620 * sc), int(820 * sc)
    bx, by = cx - book_w // 2, cy - book_h // 2
    # Shadow
    sh = Image.new("RGBA", (book_w + 80, book_h + 80), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((40, 50, book_w + 40, book_h + 50),
                                          radius=12, fill=(0, 0, 0, int(160 * op)))
    sh = sh.filter(ImageFilter.GaussianBlur(20))
    canvas.alpha_composite(sh, (bx - 40, by - 40))
    # Cover
    d.rounded_rectangle((bx, by, bx + book_w, by + book_h),
                        radius=12,
                        fill=(*NAVY[:3], int(255 * op)),
                        outline=(*ORANGE[:3], int(255 * op)), width=int(8 * sc))
    # Title big
    draw_bellefair_with_shadow(canvas, "THE", cx, by + 200, int(200 * sc),
                           color=WHITE, shadow=ORANGE, opacity=op)
    draw_bellefair_with_shadow(canvas, "GAME", cx, by + 400, int(280 * sc),
                           color=ORANGE, shadow=ORANGE_DARK, opacity=op)
    # Author bar
    f = MONT_B(int(40 * sc))
    d.text((cx, by + book_h - 80), "ALEX HORMOZI", font=f, anchor="mm",
           fill=(*CREAM[:3], int(255 * op)))
    return canvas


# ============================================================
# 13. TONY ROBBINS EVENT SILHOUETTE
# ============================================================
def render_tony_robbins(t, dur=3.0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Stage silhouette: stage bar at bottom + raked-seat triangles
    stage_y = cy + 200
    d.rectangle((cx - 500, stage_y, cx + 500, stage_y + 30),
                fill=(*ORANGE[:3], int(255 * op)))
    # Audience seats (rows of dashes)
    for row in range(7):
        y = stage_y + 80 + row * 50
        dash_w = 30 + row * 8
        n = 14 + row * 2
        for i in range(n):
            x = cx - (n * dash_w) // 2 + i * dash_w + 4
            d.rectangle((x, y, x + dash_w - 8, y + 16),
                        fill=(*CREAM[:3], int(int(200 - row * 18) * op)))
    # Single figure on stage
    fig_x, fig_y = cx, stage_y - 200
    # head
    d.ellipse((fig_x - 30, fig_y - 40, fig_x + 30, fig_y + 20),
              fill=(*WHITE[:3], int(255 * op)))
    # body
    d.polygon([(fig_x - 60, fig_y + 200), (fig_x + 60, fig_y + 200),
               (fig_x + 30, fig_y + 20), (fig_x - 30, fig_y + 20)],
              fill=(*WHITE[:3], int(255 * op)))
    # Arms out wide (pulse)
    arm_swing = 30 * math.sin(2 * math.pi * t / 1.5)
    d.polygon([(fig_x + 30, fig_y + 30),
               (fig_x + 200 + int(arm_swing), fig_y - 100),
               (fig_x + 210 + int(arm_swing), fig_y - 80),
               (fig_x + 30, fig_y + 80)], fill=(*WHITE[:3], int(255 * op)))
    d.polygon([(fig_x - 30, fig_y + 30),
               (fig_x - 200 - int(arm_swing), fig_y - 100),
               (fig_x - 210 - int(arm_swing), fig_y - 80),
               (fig_x - 30, fig_y + 80)], fill=(*WHITE[:3], int(255 * op)))
    # Spotlight glow
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((fig_x - 180, fig_y - 240, fig_x + 180, fig_y + 220),
                                   fill=(*ORANGE[:3], int(120 * op)))
    glow = glow.filter(ImageFilter.GaussianBlur(40))
    canvas = Image.alpha_composite(glow, canvas)
    # Title
    draw_bellefair_with_shadow(canvas, "THE GOAL", cx, 280, int(120 * sc),
                           color=WHITE, shadow=ORANGE, opacity=op)
    draw_bellefair_with_shadow(canvas, "FILL ARENAS", cx, 440, int(160 * sc),
                           color=ORANGE, shadow=ORANGE_DARK, opacity=op)
    return canvas


# ============================================================
# 15. 20% PIE CHART
# ============================================================
def render_twenty_percent_pie(t, dur=3.0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    r = int(360 * sc)
    # Animated pie wedge
    sweep = min(t / 1.2, 1.0) * 72  # 20% = 72° of 360
    # Base circle (dim)
    d.ellipse((cx - r, cy - r, cx + r, cy + r),
              fill=(*NAVY_LIGHT[:3], int(255 * op)),
              outline=(*ORANGE[:3], int(255 * op)), width=int(8 * sc))
    # Orange wedge (the 20%)
    if sweep > 0:
        d.pieslice((cx - r, cy - r, cx + r, cy + r),
                   start=-90, end=-90 + sweep,
                   fill=(*ORANGE[:3], int(255 * op)))
    # 20% text in centre
    if t > 0.4:
        c_op = ease_out_cubic(min((t - 0.4) / 0.3, 1.0)) * op
        draw_bellefair_with_shadow(canvas, "20%", cx, cy, int(220 * sc),
                               color=WHITE, shadow=ORANGE_DARK, opacity=c_op)
    # Caption
    draw_bellefair_with_shadow(canvas, "OF WHAT THEY", cx, cy - 580, int(80 * sc),
                           color=CREAM, shadow=ORANGE, opacity=op)
    draw_bellefair_with_shadow(canvas, "EARN", cx, cy + 580, int(180 * sc),
                           color=ORANGE, shadow=ORANGE_DARK, opacity=op)
    return canvas


# ============================================================
# 17. PHILIPPINES OUTSOURCING (PIN ON MAP)
# ============================================================
def render_philippines(t, dur=3.0):
    """Rebuilt: solid navy globe, painted PH archipelago, callout pin, clear hierarchy."""
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)

    # ---- TOP HEADLINE (Bellefair — Sam brand) ----
    draw_bellefair_with_shadow(canvas, "OUTSOURCE", cx, cy - int(700 * sc), int(150 * sc),
                                color=ORANGE, shadow=ORANGE_DARK, opacity=op)

    # ---- GLOBE (navy disc, cream grid) ----
    r = int(360 * sc)
    gcx, gcy = cx - int(80 * sc), cy - int(40 * sc)
    # Solid navy fill (gives it weight on light footage)
    d.ellipse((gcx - r, gcy - r, gcx + r, gcy + r),
              fill=(*NAVY[:3], int(245 * op)),
              outline=(*ORANGE[:3], int(255 * op)), width=int(8 * sc))
    # Cream latitude lines
    for lat in [-0.7, -0.4, 0, 0.4, 0.7]:
        yl = gcy + int(r * lat)
        wl = int(r * math.sqrt(max(0, 1 - lat * lat)))
        d.line([(gcx - wl, yl), (gcx + wl, yl)],
               fill=(*CREAM[:3], int(70 * op)), width=2)
    d.line([(gcx, gcy - r), (gcx, gcy + r)],
           fill=(*CREAM[:3], int(70 * op)), width=2)

    # ---- PHILIPPINES ARCHIPELAGO (painted orange islands) ----
    # Position: lower-right of globe (roughly Pacific quadrant)
    ph_cx, ph_cy = gcx + int(140 * sc), gcy + int(60 * sc)
    # Luzon (top, largest)
    d.polygon([
        (ph_cx - 18, ph_cy - 90), (ph_cx + 8, ph_cy - 95),
        (ph_cx + 22, ph_cy - 70), (ph_cx + 18, ph_cy - 30),
        (ph_cx - 8, ph_cy - 25), (ph_cx - 22, ph_cy - 55),
    ], fill=(*ORANGE[:3], int(255 * op)))
    # Mindoro / Samar / smaller central islands
    d.ellipse((ph_cx - 28, ph_cy - 12, ph_cx - 8, ph_cy + 8),
              fill=(*ORANGE[:3], int(255 * op)))
    d.ellipse((ph_cx + 4, ph_cy - 5, ph_cx + 26, ph_cy + 22),
              fill=(*ORANGE[:3], int(255 * op)))
    # Palawan (long thin SW)
    d.polygon([
        (ph_cx - 50, ph_cy + 15), (ph_cx - 32, ph_cy + 8),
        (ph_cx - 22, ph_cy + 38), (ph_cx - 42, ph_cy + 48),
    ], fill=(*ORANGE[:3], int(255 * op)))
    # Mindanao (large south)
    d.polygon([
        (ph_cx - 15, ph_cy + 35), (ph_cx + 25, ph_cy + 30),
        (ph_cx + 35, ph_cy + 55), (ph_cx + 20, ph_cy + 80),
        (ph_cx - 18, ph_cy + 70),
    ], fill=(*ORANGE[:3], int(255 * op)))

    # ---- PULSING PIN ----
    pulse = 1.0 + 0.25 * math.sin(2 * math.pi * t / 0.7)
    pr_outer = int(80 * sc * pulse)
    pr_inner = int(28 * sc)
    # Two pulse rings
    d.ellipse((ph_cx - pr_outer, ph_cy - pr_outer,
               ph_cx + pr_outer, ph_cy + pr_outer),
              outline=(*ORANGE[:3], int(140 * op)), width=int(5 * sc))
    d.ellipse((ph_cx - pr_outer - 30, ph_cy - pr_outer - 30,
               ph_cx + pr_outer + 30, ph_cy + pr_outer + 30),
              outline=(*ORANGE[:3], int(70 * op)), width=int(3 * sc))
    # Inner solid dot (cream so it pops against orange islands)
    d.ellipse((ph_cx - pr_inner, ph_cy - pr_inner,
               ph_cx + pr_inner, ph_cy + pr_inner),
              fill=(*CREAM[:3], int(255 * op)),
              outline=(*ORANGE_DARK[:3], int(255 * op)), width=int(4 * sc))

    # ---- CALLOUT LABEL (slides in from right) ----
    if t > 0.4:
        l_op = ease_out_cubic(min((t - 0.4) / 0.4, 1.0)) * op
        # Callout line from pin to label
        lb_x, lb_y = gcx + r + int(80 * sc), gcy - int(120 * sc)
        d.line([(ph_cx + pr_outer, ph_cy),
                (lb_x - int(20 * sc), lb_y + int(30 * sc))],
               fill=(*ORANGE[:3], int(255 * l_op)), width=int(5 * sc))
        # Label pill — navy with orange border + cream PHILIPPINES text
        lbw, lbh = int(440 * sc), int(120 * sc)
        d.rounded_rectangle((lb_x - lbw, lb_y - lbh // 2,
                             lb_x, lb_y + lbh // 2),
                            radius=int(20 * sc),
                            fill=(*NAVY[:3], int(245 * l_op)),
                            outline=(*ORANGE[:3], int(255 * l_op)),
                            width=int(5 * sc))
        f_lb = BELLEFAIR(int(60 * sc))
        d.text((lb_x - lbw // 2, lb_y), "PHILIPPINES",
               font=f_lb, anchor="mm",
               fill=(*CREAM[:3], int(255 * l_op)))

    # ---- BOTTOM PUNCHLINE (Bellefair) ----
    if t > 0.7:
        b_op = ease_out_cubic(min((t - 0.7) / 0.4, 1.0)) * op
        draw_bellefair_with_shadow(canvas, "THE EDIT", cx, cy + int(540 * sc), int(220 * sc),
                                    color=WHITE, shadow=ORANGE, opacity=b_op)
    # Stat ribbon (Bellefair)
    if t > 1.1:
        s_op = ease_out_cubic(min((t - 1.1) / 0.4, 1.0)) * op
        rw, rh = int(580 * sc), int(120 * sc)
        rx, ry = cx - rw // 2, cy + int(720 * sc)
        d.rounded_rectangle((rx, ry, rx + rw, ry + rh), radius=int(20 * sc),
                            fill=(*ORANGE[:3], int(255 * s_op)))
        f_s = BELLEFAIR(int(70 * sc))
        d.text((cx, ry + rh // 2), "$5/HR EDITORS", font=f_s, anchor="mm",
               fill=(*NAVY[:3], int(255 * s_op)))
    return canvas


# ============================================================
# 18. AI vs VIDEOGRAPHER CARD
# ============================================================
def render_ai_vs_videographer(t, dur=3.0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Left: 🤖 robot (AI)
    f = ANTON(int(360 * sc))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((cx - 240, cy - 80), "🤖", font=f, anchor="mm",
                                 fill=(*WHITE[:3], int(255 * op)))
    canvas.alpha_composite(layer)
    draw_bellefair_with_shadow(canvas, "AI", cx - 240, cy + 200, int(160 * sc),
                           color=ORANGE, shadow=ORANGE_DARK, opacity=op)
    # Right: 📷 camera (videographer)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((cx + 240, cy - 80), "📷", font=f, anchor="mm",
                                 fill=(*WHITE[:3], int(255 * op)))
    canvas.alpha_composite(layer)
    draw_bellefair_with_shadow(canvas, "EDITORS", cx + 240, cy + 200, int(120 * sc),
                           color=WHITE, shadow=ORANGE, opacity=op)
    # vs in middle
    draw_bellefair_with_shadow(canvas, "vs", cx, cy - 80,
                           int(120 * sc),
                           color=ORANGE, shadow=ORANGE_DARK, opacity=op)
    # Title above
    draw_bellefair_with_shadow(canvas, "MOST HATERS", cx, cy - 520, int(110 * sc),
                           color=WHITE, shadow=ORANGE, opacity=op)
    draw_bellefair_with_shadow(canvas, "WERE EDITORS", cx, cy + 480, int(110 * sc),
                           color=ORANGE, shadow=ORANGE_DARK, opacity=op)
    return canvas


# ============================================================
# 19. VESTED INTEREST — DOMINOES FALLING
# ============================================================
def render_vested_interest(t, dur=3.0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # 5 dominoes — fall in sequence
    dom_w, dom_h = int(70 * sc), int(220 * sc)
    spacing = int(120 * sc)
    base_y = cy + 60
    n_dom = 5
    base_x = cx - (n_dom - 1) * spacing // 2
    for i in range(n_dom):
        # Each domino starts to lean at t0
        t0 = 0.4 + i * 0.25
        if t < t0:
            angle = 0  # standing
            top_x_off = 0
        elif t < t0 + 0.3:
            # Falling
            p = (t - t0) / 0.3
            angle = p * 80
            top_x_off = int(math.sin(math.radians(angle)) * dom_h)
        else:
            angle = 80
            top_x_off = int(math.sin(math.radians(angle)) * dom_h)
        x = base_x + i * spacing
        # Approximate skew via affine: draw on layer & paste
        dom_layer = Image.new("RGBA", (dom_w * 4, dom_h * 2), (0, 0, 0, 0))
        ImageDraw.Draw(dom_layer).rectangle(
            (dom_w * 2 - dom_w // 2, dom_h, dom_w * 2 + dom_w // 2, dom_h * 2),
            fill=(*ORANGE[:3], int(255 * op)),
            outline=(*ORANGE_DARK[:3], int(255 * op)), width=int(4 * sc))
        # rotate around bottom-centre
        dom_layer = dom_layer.rotate(-angle, resample=Image.BICUBIC,
                                       center=(dom_w * 2, dom_h * 2))
        canvas.alpha_composite(dom_layer,
                                 (x - dom_w * 2, base_y - dom_h * 2))
    # Title
    draw_bellefair_with_shadow(canvas, "VESTED", cx, cy - 540, int(180 * sc),
                           color=WHITE, shadow=ORANGE, opacity=op)
    draw_bellefair_with_shadow(canvas, "INTEREST", cx, cy - 360, int(180 * sc),
                           color=ORANGE, shadow=ORANGE_DARK, opacity=op)
    return canvas


# ============================================================
# 20. 5:00 AM CLOCK
# ============================================================
def render_five_am(t, dur=3.0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Big clock face
    r = int(380 * sc)
    d.ellipse((cx - r, cy - r, cx + r, cy + r),
              fill=(*NAVY_LIGHT[:3], int(255 * op)),
              outline=(*ORANGE[:3], int(255 * op)), width=int(10 * sc))
    # Hour ticks
    for h in range(12):
        ang = math.radians(h * 30 - 90)
        x1 = cx + math.cos(ang) * (r - 30)
        y1 = cy + math.sin(ang) * (r - 30)
        x2 = cx + math.cos(ang) * (r - 60)
        y2 = cy + math.sin(ang) * (r - 60)
        d.line([(x1, y1), (x2, y2)],
               fill=(*CREAM[:3], int(255 * op)), width=int(8 * sc))
    # Hands at 5:00 — hour hand to 5, minute to 12
    # Subtle tick: minute hand twitches
    twitch = 4 * math.sin(2 * math.pi * t / 0.5)
    hour_ang = math.radians(5 * 30 - 90)
    d.line([(cx, cy),
            (cx + math.cos(hour_ang) * (r - 120),
             cy + math.sin(hour_ang) * (r - 120))],
           fill=(*ORANGE[:3], int(255 * op)), width=int(18 * sc))
    min_ang = math.radians(0 - 90 + twitch)
    d.line([(cx, cy),
            (cx + math.cos(min_ang) * (r - 60),
             cy + math.sin(min_ang) * (r - 60))],
           fill=(*WHITE[:3], int(255 * op)), width=int(12 * sc))
    d.ellipse((cx - 20, cy - 20, cx + 20, cy + 20),
              fill=(*ORANGE[:3], int(255 * op)))
    # Big 5:00 AM caption
    draw_bellefair_with_shadow(canvas, "5:00 AM", cx, cy - 580, int(180 * sc),
                           color=ORANGE, shadow=ORANGE_DARK, opacity=op)
    f = MONT_B(int(54 * sc))
    d.text((cx, cy + 580), "EVERY DAY", font=f, anchor="mm",
           fill=(*WHITE[:3], int(255 * op)))
    return canvas


# ============================================================
# 21. FESTIVAL / CLUB CAMERA FLASH B-ROLL
# ============================================================
def render_festival_camera(t, dur=3.0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Three random flashes from offset positions
    for fi in range(6):
        seed = fi * 0.41
        flash_t0 = seed
        if flash_t0 < t < flash_t0 + 0.18:
            local = (t - flash_t0) / 0.18
            fade = 1 - local
            fx = cx + int((fi * 191) % 700) - 350
            fy = cy + int((fi * 311) % 1000) - 500
            radius = int(180 * sc * (0.5 + local))
            flash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(flash).ellipse((fx - radius, fy - radius,
                                             fx + radius, fy + radius),
                                            fill=(255, 240, 200, int(220 * op * fade)))
            flash = flash.filter(ImageFilter.GaussianBlur(30))
            canvas.alpha_composite(flash)
    # Camera emoji centre
    f = ANTON(int(420 * sc))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((cx, cy), "📸", font=f, anchor="mm",
                                 fill=(*WHITE[:3], int(255 * op)))
    canvas.alpha_composite(layer)
    # Caption
    draw_bellefair_with_shadow(canvas, "FESTIVAL", cx, cy - 540, int(140 * sc),
                           color=WHITE, shadow=ORANGE, opacity=op)
    draw_bellefair_with_shadow(canvas, "PHOTOGRAPHER", cx, cy + 520, int(100 * sc),
                           color=ORANGE, shadow=ORANGE_DARK, opacity=op)
    return canvas


# ============================================================
# 22. CELEBRITY CLIENT TRIO (LOGO PLACEHOLDERS)
# ============================================================
def render_celeb_trio(t, dur=3.0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    names = ["HILTON", "TOMMY", "HUGO"]
    subs = ["the Hotels", "Hilfiger", "Boss"]
    for i, (n, s) in enumerate(zip(names, subs)):
        t0 = 0.2 + i * 0.3
        if t < t0: continue
        local_op = ease_out_cubic(min((t - t0) / 0.3, 1.0)) * op
        y = cy - 360 + i * 360
        # Pill
        w_pill = int(720 * sc)
        h_pill = int(220 * sc)
        x0 = cx - w_pill // 2
        d.rounded_rectangle((x0, y - h_pill // 2,
                              x0 + w_pill, y + h_pill // 2),
                             radius=int(40 * sc),
                             fill=(*NAVY_LIGHT[:3], int(255 * local_op)),
                             outline=(*ORANGE[:3], int(255 * local_op)),
                             width=int(6 * sc))
        draw_bellefair_with_shadow(canvas, n, cx, y - 30, int(110 * sc),
                               color=WHITE, shadow=ORANGE, opacity=local_op)
        f = MONT_B(int(36 * sc))
        d.text((cx, y + 60), s, font=f, anchor="mm",
               fill=(*ORANGE[:3], int(255 * local_op)))
    return canvas


# ============================================================
# 23. STAIRCASE — WORK A FEW STEPS ABOVE YOU
# ============================================================
def render_staircase(t, dur=3.0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # 5 steps ascending
    step_w = int(160 * sc)
    step_h = int(60 * sc)
    base_x = cx - int(400 * sc)
    base_y = cy + int(360 * sc)
    for i in range(5):
        t0 = 0.2 + i * 0.15
        local_op = ease_out_cubic(min(max((t - t0) / 0.3, 0), 1.0)) * op
        x0 = base_x + i * step_w
        y0 = base_y - (i + 1) * step_h
        d.rectangle((x0, y0, x0 + step_w + 4, base_y),
                    fill=(*ORANGE[:3], int(255 * local_op)),
                    outline=(*ORANGE_DARK[:3], int(255 * local_op)),
                    width=int(4 * sc))
    # Figure climbing (small) at the top
    if t > 1.0:
        f_op = ease_out_cubic(min((t - 1.0) / 0.4, 1.0)) * op
        fig_x = base_x + 4 * step_w + step_w // 2
        fig_y = base_y - 5 * step_h - 60
        d.ellipse((fig_x - 24, fig_y - 60, fig_x + 24, fig_y - 12),
                  fill=(*WHITE[:3], int(255 * f_op)))
        d.polygon([(fig_x - 30, fig_y + 100), (fig_x + 30, fig_y + 100),
                   (fig_x + 18, fig_y - 12), (fig_x - 18, fig_y - 12)],
                  fill=(*WHITE[:3], int(255 * f_op)))
    # Title
    draw_bellefair_with_shadow(canvas, "WORK WITH PEOPLE", cx, cy - 600, int(78 * sc),
                           color=WHITE, shadow=ORANGE, opacity=op)
    draw_bellefair_with_shadow(canvas, "A FEW STEPS", cx, cy - 480, int(120 * sc),
                           color=ORANGE, shadow=ORANGE_DARK, opacity=op)
    draw_bellefair_with_shadow(canvas, "ABOVE YOU", cx, cy - 350, int(120 * sc),
                           color=WHITE, shadow=ORANGE, opacity=op)
    return canvas


# ============================================================
# 24. DON'T WORK WITH PEOPLE YOUR AGE — AGE AXIS
# ============================================================
def render_age_axis(t, dur=3.0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Horizontal age axis
    axis_y = cy + 60
    d.line([(cx - 460, axis_y), (cx + 460, axis_y)],
           fill=(*ORANGE[:3], int(255 * op)), width=int(8 * sc))
    # Ticks 20 / 30 / 40 / 50
    ages = [20, 30, 40, 50]
    for i, a in enumerate(ages):
        x = cx - 460 + i * (920 // 3)
        d.line([(x, axis_y - 14), (x, axis_y + 14)],
               fill=(*ORANGE[:3], int(255 * op)), width=int(6 * sc))
        f = MONT_B(int(48 * sc))
        d.text((x, axis_y + 80), str(a), font=f, anchor="mm",
               fill=(*WHITE[:3], int(255 * op)))
    # Red X over "your age" (20)
    your_x = cx - 460
    x_size = int(70 * sc)
    d.line([(your_x - x_size, axis_y - x_size - 60),
            (your_x + x_size, axis_y + x_size - 60)],
           fill=(*RED[:3], int(255 * op)), width=int(14 * sc))
    d.line([(your_x - x_size, axis_y + x_size - 60),
            (your_x + x_size, axis_y - x_size - 60)],
           fill=(*RED[:3], int(255 * op)), width=int(14 * sc))
    f = MONT_B(int(42 * sc))
    d.text((your_x, axis_y - 180), "YOUR AGE", font=f, anchor="mm",
           fill=(*RED[:3], int(255 * op)))
    # Green check over 40
    target_x = cx + 460 - (920 // 3)
    pulse_op = (0.7 + 0.3 * math.sin(2 * math.pi * t / 1.0)) * op
    f_chk = ANTON(int(120 * sc))
    ImageDraw.Draw(canvas).text((target_x, axis_y - 150), "↓", font=f_chk,
                                  anchor="mm",
                                  fill=(*ORANGE[:3], int(255 * pulse_op)))
    # Title
    draw_bellefair_with_shadow(canvas, "WORK WITH", cx, cy - 540, int(120 * sc),
                           color=WHITE, shadow=ORANGE, opacity=op)
    draw_bellefair_with_shadow(canvas, "OLDER PEOPLE", cx, cy - 380, int(140 * sc),
                           color=ORANGE, shadow=ORANGE_DARK, opacity=op)
    return canvas


# ============================================================
# 25. ELON MUSK SILHOUETTE — SCALE ANCHOR
# ============================================================
def render_elon_silhouette(t, dur=3.0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Stylised abstract head silhouette (simple shape)
    head_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(head_layer)
    # Big oval head
    hd.ellipse((cx - 180, cy - 220, cx + 180, cy + 80),
               fill=(*WHITE[:3], int(255 * op)))
    # Shoulders
    hd.polygon([(cx - 320, cy + 360),
                (cx + 320, cy + 360),
                (cx + 240, cy + 80),
                (cx - 240, cy + 80)],
               fill=(*WHITE[:3], int(255 * op)))
    canvas.alpha_composite(head_layer)
    # X glyph in front (Elon's X logo abstract)
    f_x = ANTON(int(260 * sc))
    ImageDraw.Draw(canvas).text((cx, cy - 60), "𝕏", font=f_x, anchor="mm",
                                  fill=(*NAVY[:3], int(255 * op)))
    # Caption
    draw_bellefair_with_shadow(canvas, "WON'T EVEN", cx, cy - 580, int(110 * sc),
                           color=WHITE, shadow=ORANGE, opacity=op)
    draw_bellefair_with_shadow(canvas, "READ YOUR DM", cx, cy + 560, int(120 * sc),
                           color=ORANGE, shadow=ORANGE_DARK, opacity=op)
    return canvas


# ============================================================
# 26. GUARDIAN COLUMN MOCKUP
# ============================================================
def render_guardian_column(t, dur=3.0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Newspaper card
    pw, ph = int(820 * sc), int(1080 * sc)
    px, py = cx - pw // 2, cy - ph // 2
    d.rounded_rectangle((px, py, px + pw, py + ph), radius=8,
                        fill=(*CREAM[:3], int(255 * op)))
    # Masthead bar (Guardian blue)
    d.rectangle((px, py, px + pw, py + 110),
                fill=(5, 41, 84, int(255 * op)))
    f_mast = MONT_B(int(68 * sc))
    d.text((px + 40, py + 30), "the Guardian", font=f_mast,
           fill=(*WHITE[:3], int(255 * op)))
    # Headline
    f_head = MONT_B(int(56 * sc))
    head_lines = ["The teenage", "columnist", "no one saw", "coming"]
    for i, line in enumerate(head_lines):
        d.text((px + 40, py + 200 + i * 80), line, font=f_head,
               fill=(*INK[:3], int(255 * op)))
    # Byline
    f_by = MONT_B(int(36 * sc))
    d.text((px + 40, py + 600), "By Harry Cunningham", font=f_by,
           fill=(*ORANGE[:3], int(255 * op)))
    # Body text bars
    for row in range(8):
        y = py + 700 + row * 36
        bar_len = int(pw * 0.85) if row != 7 else int(pw * 0.55)
        d.rectangle((px + 40, y, px + 40 + bar_len, y + 14),
                    fill=(120, 120, 130, int(180 * op)))
    return canvas


# ============================================================
# 27. GCORE LOWER THIRD
# ============================================================
def render_gcore_lower_third(t, dur=3.0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Lower-third bar
    bar_h = int(280 * sc)
    bar_y = cy + 200
    d.rectangle((0, bar_y, W, bar_y + bar_h),
                fill=(*NAVY[:3], int(230 * op)))
    # Accent bar (Gcore blue/orange)
    d.rectangle((0, bar_y, int(20 * sc), bar_y + bar_h),
                fill=(*ORANGE[:3], int(255 * op)))
    # "Gcore" big
    f_g = MONT_B(int(120 * sc))
    d.text((80, bar_y + 50), "Gcore", font=f_g,
           fill=(*WHITE[:3], int(255 * op)))
    # Sub
    f_s = MONT_B(int(44 * sc))
    d.text((80, bar_y + 180), "EDGE AI · DATA CENTRES", font=f_s,
           fill=(*ORANGE[:3], int(255 * op)))
    # Server-rack icon (right)
    rack_x = W - int(280 * sc)
    rack_y = bar_y + 40
    rw, rh = int(180 * sc), int(200 * sc)
    d.rectangle((rack_x, rack_y, rack_x + rw, rack_y + rh),
                outline=(*WHITE[:3], int(255 * op)), width=int(5 * sc))
    for i in range(4):
        y_line = rack_y + 30 + i * 38
        d.rectangle((rack_x + 16, y_line, rack_x + rw - 16, y_line + 16),
                    fill=(*ORANGE[:3], int(220 * op)))
    return canvas


# ============================================================
# 28. UNIVERSITY = PRISON
# ============================================================
def render_university_prison(t, dur=3.0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Tassel + cap up top
    f = ANTON(int(280 * sc))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((cx, cy - 380), "🎓", font=f, anchor="mm",
                                 fill=(*WHITE[:3], int(255 * op)))
    canvas.alpha_composite(layer)
    # Vertical prison bars in lower 60% with cap behind
    bars_y0 = cy - 200
    bars_y1 = cy + 660
    n_bars = 7
    bar_w = int(40 * sc)
    gap = (W - n_bars * bar_w) // (n_bars + 1)
    for i in range(n_bars):
        x = gap + i * (bar_w + gap)
        d.rectangle((x, bars_y0, x + bar_w, bars_y1),
                    fill=(*ORANGE[:3], int(255 * op)))
    # Horizontal cross bars
    d.rectangle((0, bars_y0 - 30, W, bars_y0),
                fill=(*ORANGE_DARK[:3], int(255 * op)))
    d.rectangle((0, bars_y1, W, bars_y1 + 30),
                fill=(*ORANGE_DARK[:3], int(255 * op)))
    # Caption
    draw_bellefair_with_shadow(canvas, "UNI =", cx, cy + 740, int(120 * sc),
                           color=WHITE, shadow=ORANGE, opacity=op)
    draw_bellefair_with_shadow(canvas, "PRISON", cx, cy + 880, int(160 * sc),
                           color=RED, shadow=ORANGE_DARK, opacity=op)
    return canvas


# ============================================================
# 29. LONG MARCH THROUGH INSTITUTIONS
# ============================================================
def render_long_march(t, dur=3.0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Big classical columns silhouette (5 columns + pediment)
    n_col = 5
    col_w = int(110 * sc)
    col_h = int(560 * sc)
    spacing = int(20 * sc)
    total = n_col * col_w + (n_col - 1) * spacing
    base_x = cx - total // 2
    col_y = cy - 60
    # Pediment triangle
    d.polygon([(base_x - 40, col_y),
               (base_x + total + 40, col_y),
               (cx, col_y - 200)],
              fill=(*CREAM[:3], int(255 * op)))
    for i in range(n_col):
        x = base_x + i * (col_w + spacing)
        d.rectangle((x, col_y, x + col_w, col_y + col_h),
                    fill=(*CREAM[:3], int(255 * op)))
        # Fluting (vertical lines)
        for fl in range(4):
            fx = x + 18 + fl * (col_w - 36) // 3
            d.line([(fx, col_y + 30), (fx, col_y + col_h - 30)],
                   fill=(180, 175, 165, int(200 * op)), width=3)
    # Base
    d.rectangle((base_x - 40, col_y + col_h, base_x + total + 40, col_y + col_h + 30),
                fill=(*CREAM[:3], int(255 * op)))
    # Marching arrow over the top
    arr_t = (t % 1.5) / 1.5
    arr_x = int(W * arr_t)
    f_arr = ANTON(int(180 * sc))
    ImageDraw.Draw(canvas).text((arr_x, col_y - 320), "→", font=f_arr,
                                  anchor="mm",
                                  fill=(*ORANGE[:3], int(255 * op)))
    # Caption
    draw_bellefair_with_shadow(canvas, "LONG MARCH", cx, cy - 760, int(120 * sc),
                           color=WHITE, shadow=ORANGE, opacity=op)
    draw_bellefair_with_shadow(canvas, "THROUGH", cx, cy + 660, int(90 * sc),
                           color=WHITE, shadow=ORANGE, opacity=op)
    draw_bellefair_with_shadow(canvas, "INSTITUTIONS", cx, cy + 800, int(110 * sc),
                           color=ORANGE, shadow=ORANGE_DARK, opacity=op)
    return canvas


# ============================================================
# 30. ROCKEFELLER QUOTE CARD — NATION OF WORKERS NOT THINKERS
# ============================================================
def render_rockefeller_quote(t, dur=3.5):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= dur: return canvas
    op, sc = envelope(t, dur)
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(canvas)
    # Quote marks (top)
    f_q = ANTON(int(280 * sc))
    d.text((cx - 380, cy - 580), "“", font=f_q, anchor="mm",
           fill=(*ORANGE[:3], int(255 * op)))
    # Quote lines
    if t > 0.2:
        op1 = ease_out_cubic(min((t - 0.2) / 0.4, 1.0)) * op
        draw_bellefair_with_shadow(canvas, "I DON'T WANT", cx, cy - 320, int(110 * sc),
                               color=WHITE, shadow=ORANGE, opacity=op1)
        draw_bellefair_with_shadow(canvas, "A NATION OF", cx, cy - 180, int(110 * sc),
                               color=WHITE, shadow=ORANGE, opacity=op1)
    if t > 0.7:
        op2 = ease_out_cubic(min((t - 0.7) / 0.4, 1.0)) * op
        draw_bellefair_with_shadow(canvas, "THINKERS.", cx, cy - 20, int(160 * sc),
                               color=DIM, shadow=DIM, opacity=op2 * 0.6)
        # Strike
        f_strike = MONT_B(int(160 * sc))
        bbox = f_strike.getbbox("THINKERS.")
        tw = bbox[2] - bbox[0]
        line_y = cy - 20
        d.line([(cx - tw // 2 - 20, line_y),
                (cx + tw // 2 + 20, line_y)],
               fill=(*RED[:3], int(255 * op2)), width=int(14 * sc))
    if t > 1.3:
        op3 = ease_out_cubic(min((t - 1.3) / 0.4, 1.0)) * op
        draw_bellefair_with_shadow(canvas, "I WANT A", cx, cy + 200, int(110 * sc),
                               color=WHITE, shadow=ORANGE, opacity=op3)
        draw_bellefair_with_shadow(canvas, "NATION OF", cx, cy + 340, int(110 * sc),
                               color=WHITE, shadow=ORANGE, opacity=op3)
        draw_bellefair_with_shadow(canvas, "WORKERS.", cx, cy + 520, int(180 * sc),
                               color=ORANGE, shadow=ORANGE_DARK, opacity=op3)
    # Attribution
    if t > 1.8:
        a_op = ease_out_cubic(min((t - 1.8) / 0.4, 1.0)) * op
        f_a = MONT_B(int(42 * sc))
        d.text((cx, cy + 760), "— J.D. ROCKEFELLER", font=f_a, anchor="mm",
               fill=(*CREAM[:3], int(255 * a_op)))
    return canvas


# ============================================================
# REGISTRY
# ============================================================
CONCEPTS_PART2 = {
    "growth_trio":         (render_growth_trio,        3.5),
    "one_million_views":   (render_one_million_views,  3.0),
    "stripe_fees":         (render_stripe_fees,        3.0),
    "the_game_hormozi":    (render_the_game,           3.0),
    "tony_robbins":        (render_tony_robbins,       3.0),
    "twenty_percent_pie":  (render_twenty_percent_pie, 3.0),
    "ai_vs_videographer":  (render_ai_vs_videographer, 3.0),
    "vested_interest":     (render_vested_interest,    3.0),
    "five_am":             (render_five_am,            3.0),
    "festival_camera":     (render_festival_camera,    3.0),
    "celeb_trio":          (render_celeb_trio,         3.0),
    "staircase":           (render_staircase,          3.0),
    "age_axis":            (render_age_axis,           3.0),
    "elon_silhouette":     (render_elon_silhouette,    3.0),
    "university_prison":   (render_university_prison,  3.0),
    "long_march":          (render_long_march,         3.0),
    "rockefeller_quote":   (render_rockefeller_quote,  3.5),
}


if __name__ == "__main__":
    print(f"Building {len(CONCEPTS_PART2)} additional concept graphics...")
    for name, (fn, dur) in CONCEPTS_PART2.items():
        render_clip(name, fn, dur)
    print(f"\n✓ Done → {OUT}")
