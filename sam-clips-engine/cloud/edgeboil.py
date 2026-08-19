#!/usr/bin/env python3
"""Render ONE edge-boil b-roll beat -> short mp4 (1080x1920, opaque).

A beat = a real photo (cover) OR a kraft card holding a logo / typeset headline /
stat, with a boiling hand-drawn marker annotation (circle|underline|scribble) that
draws on, a handwritten label, optional red stamp, slow Ken-Burns, film grain +
vignette. Deterministic seek(t) so Playwright renders exact frames.
Local render only (set_content) — no external navigation needed.
"""
import json, os, sys, subprocess, base64, glob, shutil
import imageio_ffmpeg
from PIL import Image as _PIL
from playwright.sync_api import sync_playwright
HERE=os.path.dirname(os.path.abspath(__file__))
FF=imageio_ffmpeg.get_ffmpeg_exe()
CHROME="/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
FONTS=os.path.join(HERE,"assets/fonts")
FPS=24

def datauri(path):
    ext=os.path.splitext(path)[1].lstrip(".").lower().replace("jpg","jpeg")
    return f"data:image/{ext};base64,"+base64.b64encode(open(path,'rb').read()).decode()

def font_face(name,file,weight=400):
    p=os.path.join(FONTS,file)
    if not os.path.exists(p): return ""
    return f"@font-face{{font-family:'{name}';src:url('{datauri(p).replace('image/','font/')}');font-weight:{weight};}}"

TEMPLATE = """<!DOCTYPE html><html><head><meta charset=utf-8><style>
__FONTS__
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:1080px;height:1920px;overflow:hidden;background:#2b241c;}
#stage{position:absolute;width:1080px;height:1920px;overflow:hidden;}
#zoom{position:absolute;inset:0;}
.kraft{position:absolute;inset:0;background:
  radial-gradient(ellipse at 50% 38%, rgba(255,244,214,0.10), rgba(0,0,0,0.42)),
  linear-gradient(160deg,#8a7355,#6d5a40 55%,#57462f);}
.cover{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;}
.card{position:absolute;background:#fff;box-shadow:0 34px 80px rgba(0,0,0,0.6);border-radius:10px;}
.card img{display:block;max-width:100%;max-height:100%;margin:auto;}
.lcard{display:flex;align-items:center;justify-content:center;}
.txtcard{position:absolute;background:#f6f0e0;box-shadow:0 36px 90px rgba(0,0,0,0.6);
  border-radius:8px;padding:64px 60px;}
.txtcard .lab{font-family:'Archivo';font-weight:900;font-size:30px;letter-spacing:.12em;color:#8a2c1d;text-transform:uppercase;}
.txtcard .rule{height:4px;background:#1d1a14;margin:24px 0;}
.txtcard h1{font-family:'Archivo';font-weight:900;font-size:84px;line-height:1.05;color:#171310;}
.txtcard .big{font-family:'Archivo';font-weight:900;font-size:200px;line-height:1;color:#171310;text-align:center;}
.txtcard .attr{font-family:'Archivo';font-weight:900;font-size:26px;color:#5c5648;margin-top:24px;letter-spacing:.06em;}
.igcard{position:absolute;background:#fff;border-radius:26px;box-shadow:0 34px 80px rgba(0,0,0,.6);padding:46px 50px;}
.igcard .row{display:flex;align-items:center;gap:30px;}
.igcard .av{width:150px;height:150px;border-radius:50%;background:linear-gradient(135deg,#feda75,#d62976,#962fbf);}
.igcard .h{font-family:'Archivo';font-weight:900;font-size:50px;color:#111;}
.igcard .s{font-family:'Archivo';font-weight:400;font-size:34px;color:#666;margin-top:6px;}
.igcard .stat{font-family:'Archivo';font-weight:900;font-size:96px;color:#111;margin-top:30px;text-align:center;}
.hand{position:absolute;font-family:'Caveat';font-weight:700;color:#fff;text-shadow:0 3px 14px rgba(0,0,0,.85);}
.stamp{position:absolute;font-family:'Archivo';font-weight:900;color:#b3261e;border:6px solid #b3261e;
  padding:12px 26px;border-radius:8px;letter-spacing:.08em;background:rgba(246,240,224,.18);}
svg.anno{position:absolute;inset:0;width:1080px;height:1920px;pointer-events:none;}
.grain{position:absolute;inset:0;width:1080px;height:1920px;opacity:.10;pointer-events:none;}
#vig{position:absolute;inset:0;pointer-events:none;background:radial-gradient(ellipse at 50% 46%,rgba(0,0,0,0) 56%,rgba(0,0,0,.40));}
</style></head><body>
<div id=stage><div id=zoom>__BODY__
  <svg class=anno><g id=annog>__ANNO__</g></svg>
  __HAND__ __STAMP__
</div>
<svg class=grain><filter id=gr><feTurbulence id=grainT type=fractalNoise baseFrequency=0.8 numOctaves=2 seed=1/>
<feColorMatrix type=matrix values="0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0.9 0"/></filter><rect width=1080 height=1920 filter=url(#gr)/></svg>
<div id=vig></div>
<svg width=0 height=0><filter id=boil x=-20% y=-20% width=140% height=140%>
<feTurbulence id=bT1 type=fractalNoise baseFrequency=0.012 numOctaves=2 seed=1 result=t1/>
<feDisplacementMap in=SourceGraphic in2=t1 scale=8 result=d1/>
<feTurbulence id=bT2 type=fractalNoise baseFrequency=0.06 numOctaves=2 seed=11 result=t2/>
<feDisplacementMap in=d1 in2=t2 scale=3/></filter></svg></div>
<script>
const $=s=>document.querySelector(s),$$=s=>document.querySelectorAll(s);
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x)),P=(t,a,b)=>clamp((t-a)/(b-a),0,1);
const eo=p=>1-Math.pow(1-p,3),back=p=>{const c=2.0,q=p-1;return 1+(c+1)*q*q*q+c*q*q;};
function draw(el,t,t0,t1){if(!el._len){el._len=el.getTotalLength?el.getTotalLength():0;el.style.strokeDasharray=el._len;}
  const p=eo(P(t,t0,t1));el.style.strokeDashoffset=el._len*(1-p);el.style.opacity=p<=0?0:1;}
function seek(t){
  const s=1+Math.floor(t*4)%7;$('#bT1').setAttribute('seed',s);$('#bT2').setAttribute('seed',s+13);
  $('#grainT').setAttribute('seed',1+Math.floor(t*8)%11);
  $('#zoom').style.transform=`scale(${1.0+0.06*(t/__DUR__)})`;
  const k=Math.floor(t*4); const fr=(n)=>{const x=Math.sin(k*12.9898+n*78.233)*43758.5; return (x-Math.floor(x))-0.5;};
  const ag=$('#annog'); if(ag){ag.setAttribute('transform',`translate(${(fr(1)*5).toFixed(2)} ${(fr(2)*5).toFixed(2)}) rotate(${(fr(3)*1.1).toFixed(2)} 540 950)`);}
  $$('.draw').forEach(el=>draw(el,t,0.4,1.25));
  const hl=$('.hl'); if(hl){const p=eo(P(t,0.35,1.05)); hl.style.transform=`scaleX(${p.toFixed(3)})`;}
  const h=$('.hand'); if(h){const p=eo(P(t,0.7,1.15));h.style.opacity=p;h.style.transform=(h.dataset.r||'')+` translateY(${(1-p)*26}px)`;}
  const st=$('.stamp'); if(st){const p=P(t,1.0,1.28);st.style.opacity=p<=0?0:1;st.style.transform=(st.dataset.r||'')+` scale(${2.4-1.4*eo(p)})`;}
}
window.seek=seek;
</script></body></html>"""

def build_html(beat):
    fonts="".join([font_face("Archivo","ArchivoBlack.ttf",900),
                   font_face("Caveat","Caveat.ttf",700)])
    body=""; kind=beat["kind"]
    if kind=="photo":
        body+=f'<img class=cover src="{datauri(beat["img"])}">'
    else:
        body+='<div class=kraft></div>'
    if kind=="logo":
        x,y,w,h=beat.get("card",[230,640,620,520])
        body+=(f'<div class="card lcard" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;'
               f'padding:70px;transform:rotate({beat.get("rot",-2)}deg);">'
               f'<img src="{datauri(beat["img"])}"></div>')
    elif kind=="doc":
        x,y,w=beat.get("card",[70,560,940])
        body+=(f'<div class=txtcard style="left:{x}px;top:{y}px;width:{w}px;transform:rotate({beat.get("rot",-1.4)}deg);">'
               f'<div class=lab>{beat.get("lab","")}</div><div class=rule></div>'
               f'<h1>{beat["head"]}</h1>'
               + (f'<div class=attr>{beat["attr"]}</div>' if beat.get("attr") else "")+'</div>')
    elif kind=="stat":
        x,y,w=beat.get("card",[120,690,840])
        body+=(f'<div class=txtcard style="left:{x}px;top:{y}px;width:{w}px;transform:rotate({beat.get("rot",-1.5)}deg);text-align:center;">'
               + (f'<div class=lab style="text-align:center">{beat.get("lab","")}</div>' if beat.get("lab") else "")
               + f'<div class=big>{beat["big"]}</div>'
               + (f'<div class=attr style="text-align:center">{beat["attr"]}</div>' if beat.get("attr") else "")+'</div>')
    elif kind=="shot":
        # a REAL screenshot crop, framed as a browser/paper card on kraft
        cw=beat.get("cardw",1010)
        iw,ih=_PIL.open(beat["img"]).size
        chh=int(cw*ih/iw)
        x=(1080-cw)//2; y=beat.get("cardy",max(150,(1920-chh)//2-40))
        body+=(f'<div class="card" style="left:{x}px;top:{y}px;width:{cw}px;height:{chh}px;'
               f'overflow:hidden;border:9px solid #fff;transform:rotate({beat.get("rot",-1.6)}deg);">'
               f'<img src="{datauri(beat["img"])}" style="width:100%;display:block;"></div>')
    # annotation
    anno=""; a=beat.get("anno")
    if a:
        col=a.get("color","#e03020"); sw=a.get("w",12)
        if a["type"]=="circle":
            x,y,rx,ry=a["xywh"] if False else a["geo"]
            anno=f'<ellipse class=draw cx={x} cy={y} rx={rx} ry={ry} fill=none stroke="{col}" stroke-width={sw}/>'
        elif a["type"]=="underline":
            x1,y1,x2,y2=a["geo"]
            anno=f'<path class=draw d="M {x1} {y1} C {(x1+x2)/2} {y1+18}, {(x1+x2)/2} {y2+18}, {x2} {y2}" fill=none stroke="{col}" stroke-width={a.get("w",26)} stroke-linecap=round/>'
        elif a["type"]=="scribble":
            x,y,w=a["geo"]
            pts=" ".join(f"L {x+w*i/6} {y+(28 if i%2 else -28)}" for i in range(7))
            anno=f'<path class=draw d="M {x} {y} {pts}" fill=none stroke="{col}" stroke-width={sw} stroke-linejoin=round/>'
        elif a["type"]=="arrow":
            x1,y1,x2,y2=a["geo"]
            anno=(f'<path class=draw d="M {x1} {y1} C {x1} {(y1+y2)/2}, {x2} {(y1+y2)/2}, {x2} {y2}" fill=none stroke="{col}" stroke-width={sw}/>'
                  f'<path class=draw d="M {x2-26} {y2-30} L {x2} {y2} L {x2+30} {y2-22}" fill=none stroke="{col}" stroke-width={sw}/>')
        elif a["type"]=="highlight":
            x,y,w,h=a["geo"]
            anno=(f'<rect class=hl x={x} y={y} width={w} height={h} rx=12 '
                  f'fill="{a.get("color","rgba(255,221,0,0.5)")}" '
                  f'style="transform-box:fill-box;transform-origin:left center;"/>')
    hand=""
    if beat.get("hand"):
        hx,hy,fs,rot=beat.get("handpos",[120,1480,62,-3])
        hand=f'<div class=hand data-r="rotate({rot}deg)" style="left:{hx}px;top:{hy}px;font-size:{fs}px;transform:rotate({rot}deg);">{beat["hand"]}</div>'
    # Sam locked: NO red stamps, EVER (NIGHTMARE/SCAM/etc). Called out 2026-07-06 as a
    # recurring habit. Hard-disabled at the engine level so no per-interview beat config
    # can reintroduce them — `stamp` on a beat is now silently ignored.
    stamp=""
    html=TEMPLATE.replace("__FONTS__",fonts).replace("__BODY__",body).replace("__ANNO__",anno)
    html=html.replace("__HAND__",hand).replace("__STAMP__",stamp).replace("__DUR__",str(beat["dur"]))
    return html

def _frames_to_mp4(tmp,dur,out):
    subprocess.run([FF,"-y","-nostdin","-framerate",str(FPS),"-i",os.path.join(tmp,"f_%03d.jpg"),
        "-t",f"{dur}","-r","30","-c:v","libx264","-crf","18","-preset","veryfast","-pix_fmt","yuv420p",out],
        capture_output=True)
    shutil.rmtree(tmp,ignore_errors=True)
    return os.path.exists(out)

def _shoot(page,beat,out):
    dur=beat["dur"]; n=int(dur*FPS)
    tmp=out+"_frames"; shutil.rmtree(tmp,ignore_errors=True); os.makedirs(tmp)
    page.set_content(build_html(beat),wait_until="load"); page.wait_for_timeout(200)
    for i in range(n):
        page.evaluate(f"window.seek({i/FPS})")
        page.screenshot(path=os.path.join(tmp,f"f_{i:03d}.jpg"),type="jpeg",quality=86)
    return _frames_to_mp4(tmp,dur,out)

def render_beat(beat,out,page=None):
    if page is not None:
        return _shoot(page,beat,out)
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=CHROME,args=["--no-sandbox","--ignore-certificate-errors"])
        pg=b.new_page(viewport={"width":1080,"height":1920},device_scale_factor=1)
        ok=_shoot(pg,beat,out); b.close()
    return ok

def render_all(items):
    """items: list of (beat,out). One browser for all -> much faster."""
    res=[]
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=CHROME,args=["--no-sandbox","--ignore-certificate-errors"])
        pg=b.new_page(viewport={"width":1080,"height":1920},device_scale_factor=1)
        for beat,out in items:
            try: res.append((out,_shoot(pg,beat,out)))
            except Exception as e: print("  beat ERR",out,repr(e)[:100]); res.append((out,False))
        b.close()
    return res

if __name__=="__main__":
    beat=json.loads(sys.argv[1]); out=sys.argv[2]
    print("ok" if render_beat(beat,out) else "fail")
