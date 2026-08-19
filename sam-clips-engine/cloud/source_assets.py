#!/usr/bin/env python3
"""Source real b-roll assets: brand logos (Brandfetch) + stock photos (Pexels).
SVG-only logos are rasterised via the preinstalled Chromium. Saves to broll_src/."""
import os, sys, json, requests, urllib3
urllib3.disable_warnings()
sys.path.insert(0,".")
import r2_helper as R
HERE=os.path.dirname(os.path.abspath(__file__))
BF=R.infisical_secret("BRANDFETCH_API_KEY","dev")
PX=R.infisical_secret("PEXELS_API_KEY","dev")
CHROME="/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
os.makedirs("broll_src/logos",exist_ok=True); os.makedirs("broll_src/stock",exist_ok=True)
S=requests.Session(); S.verify=False

LOGOS={  # name -> domain
 "claude":"anthropic.com","openai":"openai.com","gemini":"deepmind.google",
 "microsoft":"microsoft.com","apple":"apple.com","google":"google.com",
 "instagram":"instagram.com","tiktok":"tiktok.com","bitcoin":"bitcoin.org",
 "word":"microsoft.com",
}
STOCK={ # name -> (query, n)
 "burnout":"tired stressed office worker laptop","cash":"stack of cash money dollars",
 "creator":"person filming phone tripod content","government":"government parliament building",
 "marketcrash":"stock market chart red screen","crying":"sad woman crying phone",
 "handshake":"business handshake deal suit","bankcard":"credit card phone payment",
 "code":"hands typing laptop code dark","invoice":"paperwork tax documents desk",
 "phonecrypto":"hand holding phone trading chart",
}

def rasterize_svg(svg_bytes, out, w=600):
    from playwright.sync_api import sync_playwright
    html=f'<body style="margin:0;background:transparent"><div style="width:{w}px">{svg_bytes.decode("utf-8","ignore")}</div></body>'
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=CHROME,args=["--no-sandbox","--ignore-certificate-errors"])
        pg=b.new_page(viewport={"width":w,"height":w},device_scale_factor=2)
        pg.set_content(html); pg.wait_for_timeout(200)
        el=pg.query_selector("svg") or pg.query_selector("div")
        el.screenshot(path=out, omit_background=True); b.close()

def get_logo(name,domain):
    try:
        r=S.get(f"https://api.brandfetch.io/v2/brands/{domain}",
                headers={"Authorization":f"Bearer {BF}"},timeout=30)
        if r.status_code!=200: print(f"  [logo {name}] brandfetch {r.status_code}"); return False
        logos=r.json().get("logos",[])
        # prefer type 'logo', then 'symbol'; prefer raster png/webp/jpeg, else svg
        def fmts(t): return [f for L in logos if L.get("type")==t for f in L.get("formats",[])]
        cand=fmts("logo") or fmts("symbol") or [f for L in logos for f in L.get("formats",[])]
        raster=[f for f in cand if f.get("format") in ("png","webp","jpeg")]
        out=f"broll_src/logos/{name}.png"
        if raster:
            raster.sort(key=lambda f:-(f.get("width") or 0))
            data=S.get(raster[0]["src"],timeout=30).content
            open(out,"wb").write(data)
        else:
            svg=[f for f in cand if f.get("format")=="svg"]
            if not svg: print(f"  [logo {name}] no usable format"); return False
            rasterize_svg(S.get(svg[0]["src"],timeout=30).content, out)
        print(f"  [logo {name}] ✓ {os.path.getsize(out)//1024}KB"); return True
    except Exception as e:
        print(f"  [logo {name}] ERR {repr(e)[:120]}"); return False

def get_stock(name,query):
    try:
        r=S.get("https://api.pexels.com/v1/search",headers={"Authorization":PX},
                params={"query":query,"per_page":3,"orientation":"portrait"},timeout=30)
        if r.status_code!=200: print(f"  [stock {name}] pexels {r.status_code}"); return False
        ph=r.json().get("photos",[])
        if not ph: print(f"  [stock {name}] no results"); return False
        url=ph[0]["src"].get("portrait") or ph[0]["src"].get("large")
        out=f"broll_src/stock/{name}.jpg"
        open(out,"wb").write(S.get(url,timeout=30).content)
        print(f"  [stock {name}] ✓ {os.path.getsize(out)//1024}KB"); return True
    except Exception as e:
        print(f"  [stock {name}] ERR {repr(e)[:120]}"); return False

if __name__=="__main__":
    print("LOGOS:");  L=sum(get_logo(n,d) for n,d in LOGOS.items())
    print("STOCK:");  T=sum(get_stock(n,q) for n,q in STOCK.items())
    print(f"done logos {L}/{len(LOGOS)}  stock {T}/{len(STOCK)}")
