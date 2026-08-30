#!/usr/bin/env python3
"""Recreate the real hbr.org article page (Harry 2026-08-28: "use the logo and
make it look better, recreate the site").

Content is VERBATIM from the real article fetched from hbr.org (title, authors,
magazine date, opening paragraph, the key finding sentence). The shield is the
real HBR logo SVG extracted from hbr.org's own header markup. Output: a tall
phone-width PNG that voxcard mounts and pans like any real screenshot.
"""
import base64, os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "assets/fonts")
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"


def ff(name, file, weight=400):
    uri = "data:font/ttf;base64," + base64.b64encode(
        open(os.path.join(FONTS, file), "rb").read()).decode()
    return f"@font-face{{font-family:'{name}';src:url('{uri}');font-weight:{weight};}}"


SHIELD = open(os.path.join(HERE, "assets/hbr_shield.svg")).read()

HTML = """<!DOCTYPE html><html><head><meta charset=utf-8><style>
%(fonts)s
*{margin:0;padding:0;box-sizing:border-box;}
body{width:860px;background:#fff;font-family:'Inter';color:#232323;
     -webkit-font-smoothing:antialiased;}
.topbar{display:flex;align-items:center;justify-content:space-between;
        padding:26px 34px;border-bottom:1px solid #e4e0da;}
.burger{width:44px;} .burger div{height:4px;background:#232323;margin:9px 0;border-radius:2px;}
.shield svg{width:96px;height:110px;}
.sub{font:600 24px/1 'Inter';background:#c9302b;color:#fff;padding:16px 26px;
     letter-spacing:.04em;}
.crumb{padding:44px 44px 0;font:600 24px 'Inter';letter-spacing:.14em;color:#767066;
       text-transform:uppercase;}
h1{font-family:'Garamond';font-weight:600;font-size:74px;line-height:1.08;
   padding:22px 44px 0;color:#1c1a17;}
.byline{padding:30px 44px 0;font:400 27px/1.5 'Inter';color:#232323;}
.byline b{font-weight:600;}
.mag{padding:10px 44px 0;font:400 25px 'Inter';color:#767066;}
.rule{margin:36px 44px 0;border-top:1px solid #e4e0da;}
.body{padding:34px 44px 8px;font-family:'Garamond';font-size:33px;
      line-height:1.62;color:#2a2723;}
.body p{margin-bottom:30px;}
.key{background:rgba(255,221,0,0.38);}
.figwrap{margin:14px 44px 30px;background:#f7f5f1;border:1px solid #e4e0da;padding:34px;}
.figlabel{font:600 22px 'Inter';letter-spacing:.12em;color:#c9302b;
          text-transform:uppercase;margin-bottom:16px;}
.figbig{font-family:'Garamond';font-weight:600;font-size:120px;color:#1c1a17;line-height:1;}
.figsub{font:400 25px/1.5 'Inter';color:#57524a;margin-top:14px;}
</style></head><body>
<div class=topbar>
  <div class=burger><div></div><div></div><div></div></div>
  <div class=shield>%(shield)s</div>
  <div class=sub>Subscribe</div>
</div>
<div class=crumb>Sales and marketing &middot; Magazine article</div>
<h1>The Short Life of Online Sales Leads</h1>
<div class=byline>by <b>James B. Oldroyd</b>, <b>Kristina McElheran</b> and <b>David Elkington</b></div>
<div class=mag>From the Magazine (March 2011)</div>
<div class=rule></div>
<div class=body>
<p>Are you confident that your company is effectively handling potential
customers&rsquo; online queries? Think hard. Our research shows that most companies
are not responding nearly fast enough.</p>
<p><span class=key>Firms that tried to contact potential customers within an hour
of receiving a query were nearly seven times as likely to qualify the lead</span>
(which we defined as having a meaningful conversation with a key decision maker)
as those that tried to contact the customer even an hour later&mdash;and more than
60 times as likely as companies that waited 24 hours or longer.</p>
</div>
<div class=figwrap>
  <div class=figlabel>The finding</div>
  <div class=figbig>7&times;</div>
  <div class=figsub>more likely to qualify the lead when firms responded
  within the first hour</div>
</div>
</body></html>"""


def render(out):
    html = HTML % {"fonts": "".join([
        ff("Garamond", "EBGaramond-Regular.ttf", 400),
        ff("Garamond", "EBGaramond-SemiBold.ttf", 600),
        ff("Inter", "Inter-Regular.ttf", 400),
        ff("Inter", "Inter-SemiBold.ttf", 600),
    ]), "shield": SHIELD}
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME)
        pg = b.new_page(viewport={"width": 860, "height": 2400})
        pg.set_content(html, wait_until="networkidle")
        pg.screenshot(path=out, full_page=True)
        b.close()
    return out


if __name__ == "__main__":
    render(os.path.join(HERE, "broll_src/shots/hbr_site.png"))
    from PIL import Image
    print(Image.open(os.path.join(HERE, "broll_src/shots/hbr_site.png")).size)
