#!/usr/bin/env python3
"""Server-side screenshot via microlink (Chromium nav is proxy-blocked locally)."""
import sys, json, urllib.parse, requests, urllib3, os
urllib3.disable_warnings()
S=requests.Session(); S.verify=False

def shot(url, out, w=1280, h=2200, full=False, retina=True):
    enc=urllib.parse.quote(url, safe='')
    api=(f"https://api.microlink.io/?url={enc}&screenshot=true&meta=false"
         f"&viewport.width={w}&viewport.height={h}&waitUntil=networkidle2"
         f"&screenshot.type=png"+("&screenshot.fullPage=true" if full else "")
         +("&device=true" if False else ""))
    try:
        j=S.get(api,timeout=70).json()
        surl=(j.get("data") or {}).get("screenshot",{}).get("url","")
        if not surl: print(f"  {out}: no url ({j.get('status')})"); return False
        data=S.get(surl,timeout=50).content
        open(out,"wb").write(data)
        from PIL import Image
        print(f"  {out}: {Image.open(out).size} {len(data)//1024}KB"); return True
    except Exception as e:
        print(f"  {out}: ERR {repr(e)[:120]}"); return False

if __name__=="__main__":
    url, out = sys.argv[1], sys.argv[2]
    kw={}
    for a in sys.argv[3:]:
        k,v=a.split("="); kw[k]= (v=="1") if v in ("0","1") and k=="full" else int(v) if v.isdigit() else v
    shot(url,out,**kw)
