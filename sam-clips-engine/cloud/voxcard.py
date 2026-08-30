#!/usr/bin/env python3
"""Vox-style DECODER CARD b-roll beat -> 1080x1920 mp4.

Replaces the flat coloured band over a screenshot (Harry, 2026-08-27: "no annoying
bands on any of the articles - make it like the vox style decoder cards").

A beat is one of:
  kind="article"  a REAL article rendered as a paper clipping: outlet mono label,
                  verbatim headline in editorial serif, verbatim dek, date + domain.
                  One phrase gets a hand-drawn marker sweep (wobbly, translucent
                  yellow - Sam's locked highlighter colour), never a rectangle.
  kind="shot"     a REAL screenshot mounted on the cream paper with a soft shadow
                  and taped corners, mono caption strip, optional marker sweep over
                  a region given in screenshot pixel space.
  kind="photo"    a REAL photo, full bleed, desaturated, no annotation (locked rule).

Motion: slow drift + scale, plus a 4/sec reseed jitter on the drawn marks so they
"boil" like the Vox hand-drawn language. Same output contract as edgeboil.py, so
composite2.py consumes these beats unchanged.
"""
import json, os, sys, subprocess, base64, shutil, math
import imageio_ffmpeg
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
FF = imageio_ffmpeg.get_ffmpeg_exe()
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
FONTS = os.path.join(HERE, "assets/fonts")
FPS = 24

PAPER = "#F4EFDD"
PAPER_AGED = "#E6DDCC"
INK = "#27251D"
MARKER = "rgba(255,221,0,0.52)"          # Sam's locked yellow, never red
TEAL = "#306C60"                          # vox accent, used for rules + leader lines


def datauri(path):
    ext = os.path.splitext(path)[1].lstrip(".").lower().replace("jpg", "jpeg")
    return f"data:image/{ext};base64," + base64.b64encode(open(path, "rb").read()).decode()


def font_face(name, file, weight=400):
    p = os.path.join(FONTS, file)
    if not os.path.exists(p):
        return ""
    uri = "data:font/ttf;base64," + base64.b64encode(open(p, "rb").read()).decode()
    return f"@font-face{{font-family:'{name}';src:url('{uri}');font-weight:{weight};}}"


def _fonts():
    return "".join([
        font_face("Garamond", "EBGaramond-Regular.ttf", 400),
        font_face("Garamond", "EBGaramond-SemiBold.ttf", 600),
        font_face("PlexMono", "IBMPlexMono-Medium.ttf", 500),
        font_face("Caveat", "Caveat-Bold.ttf", 700),
        font_face("Inter", "Inter-Regular.ttf", 400),
    ])


def _marker_path(x, y, w, h, seed):
    """A wobbly marker sweep: a thick stroked path with a hand-drawn baseline."""
    n = 6
    pts = []
    for i in range(n + 1):
        px = x + w * i / n
        py = y + h / 2 + math.sin(seed * 1.7 + i * 1.3) * (h * 0.06)
        pts.append((px, py))
    d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f} " + " ".join(
        f"L {px:.1f} {py:.1f}" for px, py in pts[1:])
    return d


TEMPLATE = """<!DOCTYPE html><html><head><meta charset=utf-8><style>
__FONTS__
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:1080px;height:1920px;overflow:hidden;background:__PAPER__;}
#stage{position:absolute;width:1080px;height:1920px;overflow:hidden;background:__PAPER__;}
#zoom{position:absolute;inset:0;}
.paper{position:absolute;inset:-40px;background:
  radial-gradient(ellipse at 46% 34%, #FBF7EA 0%, __PAPER__ 45%, __AGED__ 100%);}
.smudge{position:absolute;border-radius:50%;filter:blur(26px);opacity:.16;background:#8a7f66;}
.clip{position:absolute;background:#FFFDF5;box-shadow:0 30px 70px rgba(40,34,20,.30);
  padding:70px 66px 58px;}
.clip:after{content:'';position:absolute;left:0;right:0;bottom:-14px;height:16px;
  background:repeating-linear-gradient(-46deg,#FFFDF5 0 16px,transparent 16px 30px);}
.tape{position:absolute;width:190px;height:56px;background:rgba(214,201,170,.72);
  box-shadow:0 3px 10px rgba(0,0,0,.14);}
.outlet{font-family:'PlexMono';font-weight:500;font-size:29px;letter-spacing:.22em;
  text-transform:uppercase;color:#7a7461;}
.rule{height:3px;background:__TEAL__;margin:22px 0 30px;width:120px;}
h1{font-family:'Garamond';font-weight:600;font-size:82px;line-height:1.08;color:__INK__;}
.dek{font-family:'Garamond';font-weight:400;font-size:44px;line-height:1.34;color:#4a4438;margin-top:30px;}
.meta{font-family:'PlexMono';font-weight:500;font-size:26px;letter-spacing:.10em;
  color:#8b8471;margin-top:38px;}
.shot{position:absolute;background:#fff;box-shadow:0 30px 70px rgba(40,34,20,.34);
  padding:14px;}
.shot img{display:block;width:100%;}
.cap{position:absolute;font-family:'PlexMono';font-weight:500;font-size:28px;
  letter-spacing:.10em;color:#7a7461;text-transform:uppercase;}
.hand{position:absolute;font-family:'Caveat';font-weight:700;color:__INK__;}
.cover{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;
  filter:saturate(.42) contrast(1.03);}
svg.anno{position:absolute;inset:0;width:1080px;height:1920px;pointer-events:none;}
.grain{position:absolute;inset:0;opacity:.13;pointer-events:none;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3'/></filter><rect width='240' height='240' filter='url(%23n)' opacity='.5'/></svg>");}
#vig{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(ellipse at 50% 46%,rgba(0,0,0,0) 58%,rgba(60,50,30,.24));}
</style></head><body>
<div id=stage><div id=zoom>
  <div class=paper></div>
  <div class=smudge style="left:120px;top:250px;width:260px;height:120px;"></div>
  <div class=smudge style="left:720px;top:1520px;width:220px;height:110px;"></div>
  __BODY__
  <svg class=anno viewBox="0 0 1080 1920">__ANNO__</svg>
  __HAND__
</div><div class=grain></div><div id=vig></div></div>
<script>
const DUR=__DUR__, DRIFT=__DRIFT__;
function seek(t){
  const p=Math.min(1,Math.max(0,t/DUR));
  const s=1.035+0.030*p, dx=DRIFT[0]*p, dy=DRIFT[1]*p;
  document.getElementById('zoom').style.transform=
    `translate(${dx}px,${dy}px) scale(${s})`;
  // marker sweep-on over the first 0.55s
  const sw=Math.min(1,t/0.55);
  document.querySelectorAll('.mk').forEach(function(el){
    const L=el.getTotalLength();
    el.style.strokeDasharray=L; el.style.strokeDashoffset=L*(1-sw);
  });
  // second-wave draws (gfx diagrams): 0.45s -> 1.15s
  const sw2=Math.min(1,Math.max(0,(t-0.45)/0.7));
  document.querySelectorAll('.mk2').forEach(function(el){
    const L=el.getTotalLength();
    el.style.strokeDasharray=L; el.style.strokeDashoffset=L*(1-sw2);
  });
  document.querySelectorAll('.late').forEach(function(el){
    el.style.opacity = t>1.0 ? 1 : 0;
  });
  // site scrolls: ease-in-out pan from 0.3s to DUR-0.3s
  const pt=Math.min(1,Math.max(0,(t-0.3)/(DUR-0.6)));
  const pe=pt<.5 ? 2*pt*pt : 1-Math.pow(-2*pt+2,2)/2;
  document.querySelectorAll('img.pan').forEach(function(el){
    el.style.transform=`translateY(${-pe*parseFloat(el.dataset.pan)}px)`;
  });
  // 4/sec reseed jitter on every drawn mark -> the vox boil
  const k=Math.floor(t*4);
  document.querySelectorAll('.boil').forEach(function(el,i){
    const a=Math.sin(k*12.9898+i*78.233)*43758.5453;
    const jx=((a-Math.floor(a))-0.5)*2.6, b=Math.sin(k*4.1414+i*13.7)*24634.6345;
    const jy=((b-Math.floor(b))-0.5)*2.6, r=((a-Math.floor(a))-0.5)*0.5;
    el.style.transform=`translate(${jx}px,${jy}px) rotate(${r}deg)`;
    el.style.transformOrigin='center';
  });
}
window.seek=seek; seek(0);
</script></body></html>"""


def _wob(pts, seed, amp=4.0):
    """Hand-drawn path through pts with per-vertex noise + midpoint wobble."""
    out = []
    for i, (x, y) in enumerate(pts):
        nx = x + math.sin(seed * 3.1 + i * 2.7) * amp
        ny = y + math.cos(seed * 5.7 + i * 1.9) * amp
        out.append((nx, ny))
    d = f"M {out[0][0]:.1f} {out[0][1]:.1f}"
    for i in range(1, len(out)):
        mx = (out[i-1][0] + out[i][0]) / 2 + math.sin(seed * 7.7 + i * 4.3) * amp * 0.6
        my = (out[i-1][1] + out[i][1]) / 2 + math.cos(seed * 2.3 + i * 5.1) * amp * 0.6
        d += f" Q {mx:.1f} {my:.1f} {out[i][0]:.1f} {out[i][1]:.1f}"
    return d


def _circle_pts(cx, cy, r, n=26, gap=0.10):
    """An almost-closed hand circle (the vox one-circle language)."""
    pts = []
    for i in range(n + 1):
        a = -math.pi / 2 + (i / n) * (2 * math.pi) * (1 - gap)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _stroke(d, col=None, w=9, cls="mk2 boil", cap="round"):
    return (f'<path class="{cls}" d="{d}" fill="none" stroke="{col or INK}" '
            f'stroke-width="{w}" stroke-linecap="{cap}" stroke-linejoin="round"/>')


def _gfx_svg(beat):
    """Hand-drawn vox diagram beats. Returns (anno_svg, hands list)."""
    g = beat["gfx"]
    seed = beat.get("seed", 3)
    anno, hands = "", list(beat.get("hands", []))
    AX = INK

    if g == "chart":                       # rising (or falling) line on drawn axes
        x0, y0, x1, y1 = 170, 1330, 930, 620
        anno += _stroke(_wob([(x0, 640), (x0, y0)], seed + 1, 3.5), AX, 8, "mk boil")
        anno += _stroke(_wob([(x0, y0), (950, y0)], seed + 2, 3.5), AX, 8, "mk boil")
        pts = beat.get("pts") or ([(x0+40, 1240), (330, 1180), (470, 1050),
                                   (600, 1090), (740, 860), (x1, y1)]
                                  if not beat.get("down") else
                                  [(x0+40, 700), (330, 760), (470, 900),
                                   (600, 870), (740, 1120), (x1, 1290)])
        anno += _stroke(_wob(pts, seed, 5.0), TEAL, 13)
        ex, ey = pts[-1]
        anno += (f'<circle class="late boil" cx="{ex}" cy="{ey}" r="16" '
                 f'fill="{TEAL}" opacity="0"/>')
        if beat.get("mark_end"):
            anno += _stroke(_wob(_circle_pts(ex, ey, 74, gap=.08), seed + 4, 5),
                            "rgba(255,221,0,0.85)", 14, "mk2 boil")

    elif g == "cross":                     # supply / demand crossing curves
        anno += _stroke(_wob([(190, 640), (190, 1330)], seed + 1, 3.5), AX, 8, "mk boil")
        anno += _stroke(_wob([(190, 1330), (950, 1330)], seed + 2, 3.5), AX, 8, "mk boil")
        anno += _stroke(_wob([(250, 700), (420, 850), (600, 1010), (900, 1240)],
                             seed, 5), TEAL, 13)
        anno += _stroke(_wob([(250, 1240), (430, 1080), (620, 940), (900, 700)],
                             seed + 3, 5), AX, 13)
        anno += _stroke(_wob(_circle_pts(575, 985, 88, gap=.08), seed + 5, 5),
                        "rgba(255,221,0,0.85)", 14)

    elif g == "clock":                     # the response-time clock
        cx, cy, r = 540, 950, 330
        anno += _stroke(_wob(_circle_pts(cx, cy, r), seed, 6), AX, 13, "mk boil")
        for k in range(12):
            a = k * math.pi / 6
            p1 = (cx + (r - 34) * math.sin(a), cy - (r - 34) * math.cos(a))
            p2 = (cx + (r - 8) * math.sin(a), cy - (r - 8) * math.cos(a))
            anno += _stroke(_wob([p1, p2], seed + k, 2.5), AX, 9, "mk boil")
        # hands: hour at 10, minute at the 1 (five past)
        anno += _stroke(_wob([(cx, cy), (cx - 105, cy - 150)], seed + 20, 3), AX, 15)
        anno += _stroke(_wob([(cx, cy), (cx + 128, cy - 222)], seed + 21, 3), TEAL, 15)
        # yellow sweep arc over the first five minutes
        arc = [(cx + (r + 46) * math.sin(a), cy - (r + 46) * math.cos(a))
               for a in [i / 10 * (math.pi / 6 * 1.05) for i in range(11)]]
        anno += _stroke(_wob(arc, seed + 7, 4), "rgba(255,221,0,0.85)", 26)

    elif g == "funnel":                    # many leads, one deal
        import random
        rnd = random.Random(seed)
        k = 0
        for row in range(10):
            for col in range(10):
                x = 205 + col * 74 + rnd.uniform(-7, 7)
                y = 640 + row * 62 + rnd.uniform(-6, 6)
                anno += (f'<circle class="boil" cx="{x:.0f}" cy="{y:.0f}" r="11" '
                         f'fill="none" stroke="{AX}" stroke-width="5.5"/>')
                k += 1
        fx, fy = 205 + 4 * 74, 640 + 9 * 62
        anno += (f'<circle class="late boil" cx="{fx}" cy="{fy}" r="11" fill="{TEAL}"/>')
        anno += _stroke(_wob(_circle_pts(fx, fy, 56, gap=.08), seed + 3, 4.5),
                        "rgba(255,221,0,0.85)", 13)

    elif g == "stack":                     # money stacking up month on month
        heights = beat.get("heights", [2, 3, 5, 8])
        bw = 150
        for i, hgt in enumerate(heights):
            bx = 210 + i * 190
            for j in range(hgt):
                y = 1290 - j * 64
                anno += _stroke(
                    _wob([(bx, y), (bx + bw, y), (bx + bw, y - 46),
                          (bx, y - 46), (bx, y)], seed + i * 10 + j, 3.2),
                    TEAL if i == len(heights) - 1 else AX, 8)
        anno += _stroke(_wob([(170, 1330), (960, 1330)], seed + 2, 3.5),
                        AX, 8, "mk boil")

    return anno, hands


def build_html(beat):
    body = ""
    anno = ""
    hand = ""
    kind = beat.get("kind", "article")

    if kind == "gfx":
        a, hands = _gfx_svg(beat)
        anno += a
        for h in hands:
            hx, hy, fs, rot, txt = h
            hand += (f'<div class="hand boil" style="left:{hx}px;top:{hy}px;'
                     f'font-size:{fs}px;transform:rotate({rot}deg);">{txt}</div>')

    elif kind == "blank":
        # the empty ad. Nothing on it. This is the joke, so it gets the space.
        body += ('<div style="position:absolute;inset:0;background:#F7F4EC;"></div>')

    elif kind == "photo":
        body += f'<img class=cover src="{datauri(beat["img"])}">'

    elif kind == "shot":
        w = beat.get("cardw", 940)
        from PIL import Image
        iw, ih = Image.open(beat["img"]).size
        ch = int(w * ih / iw)
        x = (1080 - w) // 2
        rot = beat.get("rot", -1.2)
        if beat.get("croph"):
            # tall screenshot pans inside a fixed-height card (site scrolls)
            full_ch = ch
            ch = beat["croph"]
            y = beat.get("cardy", max(190, (1920 - ch) // 2 - 60))
            pan = beat.get("panpx", max(0, full_ch - ch))
            body += (f'<div class=shot style="left:{x}px;top:{y}px;width:{w}px;'
                     f'height:{ch}px;overflow:hidden;transform:rotate({rot}deg);">'
                     f'<img class=pan data-pan="{pan}" src="{datauri(beat["img"])}">'
                     f'</div>')
        else:
            y = beat.get("cardy", max(190, (1920 - ch) // 2 - 60))
            body += (f'<div class=shot style="left:{x}px;top:{y}px;width:{w}px;'
                     f'transform:rotate({rot}deg);"><img src="{datauri(beat["img"])}"></div>')
        body += (f'<div class=tape style="left:{x-40}px;top:{y-26}px;'
                 f'transform:rotate(-7deg);"></div>')
        body += (f'<div class=tape style="left:{x+w-150}px;top:{y+ch-18}px;'
                 f'transform:rotate(5deg);"></div>')
        if beat.get("cap"):
            body += (f'<div class=cap style="left:{x+8}px;top:{y+ch+42}px;'
                     f'width:{w}px;">{beat["cap"]}</div>')
        hl = beat.get("mark")            # [x,y,w,h] in page coords
        if hl:
            hx, hy, hw, hh = hl
            d = _marker_path(hx, hy, hw, hh, beat.get("seed", 3))
            anno += (f'<path class="mk boil" d="{d}" fill=none stroke="{MARKER}" '
                     f'stroke-width={hh} stroke-linecap=round/>')

    else:  # article clipping
        w = beat.get("cardw", 900)
        x = (1080 - w) // 2
        y = beat.get("cardy", 470)
        rot = beat.get("rot", -1.4)
        head = beat["headline"]
        body += (f'<div class=clip style="left:{x}px;top:{y}px;width:{w}px;'
                 f'transform:rotate({rot}deg);">'
                 f'<div class=outlet>{beat.get("outlet","")}</div>'
                 f'<div class=rule></div>'
                 f'<h1>{head}</h1>'
                 + (f'<div class=dek>{beat["dek"]}</div>' if beat.get("dek") else "")
                 + f'<div class=meta>{beat.get("meta","")}</div></div>')
        body += (f'<div class=tape style="left:{x-46}px;top:{y-28}px;'
                 f'transform:rotate(-8deg);"></div>')
        hl = beat.get("mark")
        if hl:
            hx, hy, hw, hh = hl
            d = _marker_path(hx, hy, hw, hh, beat.get("seed", 5))
            anno += (f'<path class="mk boil" d="{d}" fill=none stroke="{MARKER}" '
                     f'stroke-width={hh} stroke-linecap=round/>')

    if beat.get("hand"):
        hx, hy, fs, rot = beat.get("handpos", [110, 1560, 64, -3])
        hand = (f'<div class="hand boil" style="left:{hx}px;top:{hy}px;'
                f'font-size:{fs}px;transform:rotate({rot}deg);">{beat["hand"]}</div>')

    drift = beat.get("drift", [-14, -10])
    html = (TEMPLATE.replace("__FONTS__", _fonts()).replace("__BODY__", body)
            .replace("__ANNO__", anno).replace("__HAND__", hand)
            .replace("__DUR__", str(beat["dur"])).replace("__DRIFT__", json.dumps(drift))
            .replace("__PAPER__", PAPER).replace("__AGED__", PAPER_AGED)
            .replace("__INK__", INK).replace("__TEAL__", TEAL))
    return html


def _frames_to_mp4(tmp, dur, out):
    subprocess.run([FF, "-y", "-nostdin", "-framerate", str(FPS),
                    "-i", os.path.join(tmp, "f_%03d.jpg"), "-t", f"{dur}", "-r", "30",
                    "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                    "-pix_fmt", "yuv420p", out], capture_output=True)
    shutil.rmtree(tmp, ignore_errors=True)
    return os.path.exists(out)


def _shoot(page, beat, out):
    dur = beat["dur"]
    n = int(dur * FPS)
    tmp = out + "_frames"
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    page.set_content(build_html(beat), wait_until="load")
    page.wait_for_timeout(200)
    for i in range(n):
        page.evaluate(f"window.seek({i/FPS})")
        page.screenshot(path=os.path.join(tmp, f"f_{i:03d}.jpg"), type="jpeg", quality=88)
    return _frames_to_mp4(tmp, dur, out)


def render_all(items):
    """items: list of (beat, out). One browser for all."""
    res = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME,
                              args=["--no-sandbox", "--ignore-certificate-errors"])
        pg = b.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
        for beat, out in items:
            try:
                res.append((out, _shoot(pg, beat, out)))
            except Exception as e:
                print("  beat ERR", out, repr(e)[:120])
                res.append((out, False))
        b.close()
    return res


if __name__ == "__main__":
    beat = json.loads(sys.argv[1])
    out = sys.argv[2]
    print("ok" if render_all([(beat, out)])[0][1] else "fail")
