#!/usr/bin/env python3
"""Recreate a realistic Instagram DM conversation (dark mode) as an animated 1080x1920
beat. Full-bleed phone screen: header w/ real Sam avatar, bubbles, timestamps, input bar.
Our techniques on top: yellow highlight OUTLINE on the key bubble (not a red circle),
handwritten Caveat label, subtle Ken-Burns zoom, light grain + vignette, boil jitter.

Sam locked: for DMs we RECREATE an actual conversation (can't screenshot a private DM).
Renders via Playwright set_content (proxy can't navigate). render_all_dm(items) = one
browser for many beats (matches edgeboil.render_all)."""
import os, base64, subprocess, shutil, json, sys
import imageio_ffmpeg
from playwright.sync_api import sync_playwright
HERE=os.path.dirname(os.path.abspath(__file__))
FF=imageio_ffmpeg.get_ffmpeg_exe()
CHROME="/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
FONTS=os.path.join(HERE,"assets/fonts")
AVATAR=os.path.join(HERE,"broll_src/sam_avatar.jpg")
FPS=24

def datauri(path):
    ext=os.path.splitext(path)[1].lstrip(".").lower().replace("jpg","jpeg")
    return f"data:image/{ext};base64,"+base64.b64encode(open(path,'rb').read()).decode()

def font_face(name,file,weight):
    p=os.path.join(FONTS,file)
    return f"@font-face{{font-family:'{name}';src:url('{datauri(p).replace('image/','font/')}');font-weight:{weight};}}"

def build_dm_html(beat):
    convo=beat["convo"]; name=beat.get("name","sam.ey.am"); sub=beat.get("sub","Active now")
    hand=beat.get("hand"); dur=beat["dur"]; banner=beat.get("banner")
    handpos=beat.get("handpos",[110,250,66,-3])
    fonts="".join([font_face("Inter","Inter-Regular.ttf",400),
                   font_face("Inter","Inter-SemiBold.ttf",600),
                   font_face("Inter","Inter-Bold.ttf",700),
                   font_face("Caveat","Caveat.ttf",700)])
    rows=(f'<div class=ts>{banner}</div>' if banner else "")
    for m in convo:
        who=m["who"]; hi="hi" if m.get("hi") else ""
        tm=f'<div class="tm {who}">{m["time"]}</div>' if m.get("time") else ""
        if who=="them":
            rows+=(f'<div class="row them"><img class=avm src="{datauri(AVATAR)}">'
                   f'<div class="bwrap"><div class="b in {hi}">{m["text"]}</div>{tm}</div></div>')
        else:
            rows+=(f'<div class="row me"><div class="bwrap"><div class="b out {hi}">{m["text"]}</div>{tm}</div></div>')
    handdiv=""
    if hand:
        hx,hy,fs,rot=handpos
        handdiv=f'<div class=hand id=hand style="left:{hx}px;top:{hy}px;font-size:{fs}px;transform:rotate({rot}deg);">{hand}</div>'
    return f"""<!DOCTYPE html><html><head><meta charset=utf-8><style>
{fonts}
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Inter',sans-serif;-webkit-font-smoothing:antialiased;}}
html,body{{width:1080px;height:1920px;background:#000;overflow:hidden;}}
#zoom{{position:absolute;inset:0;transform-origin:50% 58%;}}
.status{{height:64px;display:flex;align-items:center;justify-content:space-between;padding:0 54px 0 60px;color:#fff;}}
.status .t{{font-weight:600;font-size:34px;letter-spacing:.5px;}}
.status .r{{display:flex;align-items:center;gap:14px;}}
.status .bars{{font-size:30px;letter-spacing:-2px;}}
.status .bat{{width:52px;height:26px;border:3px solid #fff;border-radius:7px;position:relative;opacity:.95;}}
.status .bat::after{{content:'';position:absolute;right:-7px;top:8px;width:5px;height:9px;background:#fff;border-radius:0 3px 3px 0;}}
.status .bat i{{position:absolute;left:3px;top:3px;bottom:3px;width:72%;background:#fff;border-radius:3px;display:block;}}
.head{{height:150px;display:flex;align-items:center;gap:26px;padding:0 44px;margin-top:20px;border-bottom:1px solid #1c1c1e;}}
.head .back{{color:#fff;font-size:70px;font-weight:300;line-height:1;margin-top:-8px;}}
.head .av{{width:92px;height:92px;border-radius:50%;object-fit:cover;}}
.head .who{{flex:1;}}
.head .who b{{display:block;color:#fff;font-size:40px;font-weight:700;line-height:1.1;}}
.head .who span{{color:#8e8e93;font-size:30px;font-weight:400;}}
.head .ic{{color:#fff;font-size:44px;opacity:.9;}}
.body{{padding:30px 40px 0;display:flex;flex-direction:column;gap:20px;height:1620px;justify-content:flex-end;}}
.ts{{text-align:center;color:#8e8e93;font-size:28px;font-weight:600;margin:10px 0 18px;letter-spacing:.3px;}}
.row{{display:flex;align-items:flex-end;gap:20px;max-width:100%;}}
.row.them{{justify-content:flex-start;}}
.row.me{{justify-content:flex-end;}}
.avm{{width:60px;height:60px;border-radius:50%;object-fit:cover;flex:0 0 60px;}}
.bwrap{{display:flex;flex-direction:column;max-width:72%;}}
.row.me .bwrap{{align-items:flex-end;}}
.b{{font-size:41px;line-height:1.32;padding:24px 34px;border-radius:34px;color:#fff;word-wrap:break-word;position:relative;}}
.b.in{{background:#262629;border-bottom-left-radius:10px;}}
.b.out{{background:linear-gradient(118deg,#5b6ef6 0%,#8a49e6 52%,#c13aa8 100%);border-bottom-right-radius:10px;}}
.tm{{color:#7d7d82;font-size:26px;margin:8px 12px 2px;font-weight:500;}}
.tm.me{{text-align:right;}}
/* yellow highlight = a soft glowing rounded OUTLINE around the key bubble (not a red circle) */
.b.hi{{box-shadow:0 0 0 5px rgba(255,221,0,var(--hl,0)), 0 0 34px 6px rgba(255,221,0,calc(var(--hl,0)*0.55));}}
.input{{position:absolute;bottom:0;left:0;right:0;height:132px;display:flex;align-items:center;gap:24px;padding:0 40px;border-top:1px solid #1c1c1e;background:#000;}}
.input .cam{{width:74px;height:74px;border-radius:50%;background:#3797f0;display:flex;align-items:center;justify-content:center;font-size:40px;flex:0 0 74px;}}
.input .field{{flex:1;height:82px;border:2px solid #2c2c2e;border-radius:41px;display:flex;align-items:center;padding:0 36px;color:#8e8e93;font-size:36px;}}
.input .ic{{color:#fff;font-size:44px;opacity:.9;}}
.hand{{position:absolute;font-family:'Caveat';font-weight:700;color:#fff;text-shadow:0 3px 16px rgba(0,0,0,.95);opacity:0;z-index:20;}}
.grain{{position:absolute;inset:0;width:1080px;height:1920px;opacity:.05;pointer-events:none;z-index:15;}}
#vig{{position:absolute;inset:0;pointer-events:none;z-index:14;background:radial-gradient(ellipse at 50% 46%,rgba(0,0,0,0) 66%,rgba(0,0,0,.34));}}
</style></head><body>
<div id=zoom>
<div class=head><div class=back>‹</div><img class=av src="{datauri(AVATAR)}"><div class=who><b>{name}</b><span>{sub}</span></div>
  <span class=ic>📞</span><span class=ic>📹</span></div>
<div class=body>{rows}</div>
<div class=input><div class=cam>📷</div><div class=field>Message...</div><span class=ic>🎤</span><span class=ic>🖼️</span></div>
{handdiv}
</div>
<svg class=grain><filter id=gr><feTurbulence id=grainT type=fractalNoise baseFrequency=0.85 numOctaves=2 seed=3/>
<feColorMatrix type=matrix values="0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0.9 0"/></filter><rect width=1080 height=1920 filter=url(#gr)/></svg>
<div id=vig></div>
<script>
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x)),P=(t,a,b)=>clamp((t-a)/(b-a),0,1);
const eo=p=>1-Math.pow(1-p,3);
function seek(t){{
  const dur={dur};
  document.getElementById('grainT').setAttribute('seed',3+Math.floor(t*8)%11);
  document.getElementById('zoom').style.transform=`scale(${{1.0+0.03*(t/dur)}})`;
  const hlv=eo(P(t,0.45,1.15));
  document.querySelectorAll('.b.hi').forEach(el=>el.style.setProperty('--hl',hlv.toFixed(3)));
  const h=document.getElementById('hand');
  if(h){{const k=Math.floor(t*4);const fr=(Math.sin(k*12.9)*43758.5);const j=(fr-Math.floor(fr)-0.5)*4;
    const p=eo(P(t,0.75,1.2));h.style.opacity=p;h.style.transform=`rotate(-3deg) translateY(${{(1-p)*24}}px) translateX(${{j.toFixed(2)}}px)`;}}
}}
window.seek=seek;
</script>
</body></html>"""

def _shoot(page,beat,out):
    dur=beat["dur"]; n=int(dur*FPS)
    tmp=out+"_f"; shutil.rmtree(tmp,ignore_errors=True); os.makedirs(tmp)
    page.set_content(build_dm_html(beat),wait_until="load"); page.wait_for_timeout(250)
    for i in range(n):
        page.evaluate(f"window.seek({i/FPS})")
        page.screenshot(path=os.path.join(tmp,f"f_{i:03d}.jpg"),type="jpeg",quality=90)
    subprocess.run([FF,"-y","-nostdin","-framerate",str(FPS),"-i",os.path.join(tmp,"f_%03d.jpg"),
        "-t",f"{dur}","-r","30","-c:v","libx264","-crf","18","-preset","veryfast","-pix_fmt","yuv420p",out],
        capture_output=True)
    shutil.rmtree(tmp,ignore_errors=True); return os.path.exists(out)

def render_all_dm(items):
    res=[]
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=CHROME,args=["--no-sandbox","--ignore-certificate-errors"])
        pg=b.new_page(viewport={"width":1080,"height":1920},device_scale_factor=1)
        for beat,out in items:
            try: res.append((out,_shoot(pg,beat,out)))
            except Exception as e: print("  dm ERR",out,repr(e)[:120]); res.append((out,False))
        b.close()
    return res

def render_still(beat,out):
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=CHROME,args=["--no-sandbox","--ignore-certificate-errors"])
        pg=b.new_page(viewport={"width":1080,"height":1920},device_scale_factor=1)
        pg.set_content(build_dm_html(beat),wait_until="load"); pg.wait_for_timeout(250)
        pg.evaluate("window.seek(2.2)"); pg.screenshot(path=out); b.close()
    return out

if __name__=="__main__":
    beat={"dur":3.0,"sub":"Active now","hand":"the AI is replying 🤖",
      "convo":[
      {"who":"them","text":"yo just watched your reel on AI systems 🔥"},
      {"who":"them","text":"do you actually reply to all these yourself?"},
      {"who":"me","text":"haha honestly? an AI runs my DMs 😄","hi":True},
      {"who":"me","text":"it checks every few mins + replies for me"},
      {"who":"them","text":"wait that's actually genius 😂"},
    ]}
    render_still(beat,"_dm_proto.png"); print("ok")
