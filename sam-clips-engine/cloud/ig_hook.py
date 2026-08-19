#!/usr/bin/env python3
"""Instagram version: add a Bellefair title-card hook sitting at the BOTTOM from frame 0
(NO slide-in — it transitions OUT only) for the first ~2.5s, with karaoke captions suppressed while it's on screen (so nothing clashes).
Card sits low (clear of Sam's face), does not fill the screen. Output finals_ig/<id>_ig.mp4
Usage: python ig_hook.py <id> "Line one" "Line two"
"""
import os, sys, subprocess, re
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE=os.path.dirname(os.path.abspath(__file__))
FF=imageio_ffmpeg.get_ffmpeg_exe()
BELLE=os.path.join(HERE,"assets/fonts/Bellefair-Regular.ttf")
HOOK_DUR=2.2; FONTS=os.path.join(HERE,"assets/fonts")
import json
PLAN={c["id"]:c for c in json.load(open(os.path.join(HERE,"plan.json")))}

def render_hook(lines, out, font_px=98):
    font=ImageFont.truetype(BELLE,font_px)
    dd=ImageDraw.Draw(Image.new("RGBA",(10,10)))
    widths=[dd.textbbox((0,0),l,font=font)[2]-dd.textbbox((0,0),l,font=font)[0] for l in lines]
    asc,desc=font.getmetrics(); lh=asc+desc
    padx,pady,gap,margin=90,58,14,46
    cardw=min(1000,max(widths)+2*padx); cardh=len(lines)*lh+(len(lines)-1)*gap+2*pady
    img=Image.new("RGBA",(cardw+2*margin,cardh+2*margin),(0,0,0,0))
    sh=Image.new("RGBA",img.size,(0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle(
        [margin,margin+10,margin+cardw,margin+cardh+10],radius=24,fill=(0,0,0,95))
    img=Image.alpha_composite(img,sh.filter(ImageFilter.GaussianBlur(20)))
    d=ImageDraw.Draw(img)
    d.rounded_rectangle([margin,margin,margin+cardw,margin+cardh],radius=24,fill=(255,255,255,255))
    y=margin+pady
    for i,l in enumerate(lines):
        bb=d.textbbox((0,0),l,font=font); x=margin+(cardw-(bb[2]-bb[0]))//2-bb[0]
        d.text((x,y-bb[1]+2),l,font=font,fill=(15,15,15,255)); y+=lh+gap
    img.save(out); return img.size

def delayed_ass(cid, brolls=None):
    d=os.path.join(HERE,"caps",f"{cid:02d}")
    use_bf=os.path.exists(os.path.join(d,"bellefair.ass"))      # Bellefair single-word style?
    src=os.path.join(d,"bellefair.ass" if use_bf else "karaoke.ass")
    dst=os.path.join(d,"bellefair_ig.ass" if use_bf else "karaoke_ig.ass")
    out=[]
    def t2s(t):
        h,m,s=t.split(":"); return int(h)*3600+int(m)*60+float(s)
    # Bellefair: suppress under ANY b-roll; karaoke: only over DMs
    wins=[(b["start"],b["end"]) for b in (brolls or []) if use_bf or b.get("kind")=="dm"]
    for ln in open(src):
        if ln.startswith("Dialogue:"):
            f=ln.split(","); st=t2s(f[1]); en=t2s(f[2])
            if st < HOOK_DUR-0.02: continue                       # suppressed under the hook card
            if any(st<we and en>ws for ws,we in wins): continue   # suppressed over b-roll
        out.append(ln)
    open(dst,"w").write("".join(out)); return dst

def composite_ig(cid, lines):
    clip=PLAN[cid]; slug=clip["slug"]; dur=clip["out_dur"]
    base=os.path.join(HERE,"bases",f"base_{cid:02d}.mp4")
    brolls=json.load(open(os.path.join(HERE,"broll",f"{cid:02d}","spec.json")))
    ass=delayed_ass(cid, brolls)
    hook=os.path.join(HERE,"_hook.png"); hw,hh=render_hook(lines,hook)
    rest=1920-hh-70                       # card rests low, ~70px from bottom
    inputs=["-i",base]; parts=[]; cur="[0:v]"; idx=1
    for b in brolls:
        f=b["file"]; s,e=b["start"],b["end"]
        inputs+=["-i",f]
        parts.append(f"[{idx}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                     f"setpts=PTS-STARTPTS+{s}/TB[b{idx}]")
        parts.append(f"{cur}[b{idx}]overlay=0:0:enable='between(t,{s},{e})':eof_action=pass[v{idx}]")
        cur=f"[v{idx}]"; idx+=1
    parts.append(f"{cur}ass={ass}:fontsdir={FONTS}[vcap]")
    inputs+=["-loop","1","-t",f"{HOOK_DUR}","-i",hook]
    hi=idx
    # LOCKED 2026-08-04 (Sam/Harry): card is fully present from frame 0 — NO slide-in,
    # NO fade-in. It only transitions OUT.
    parts.append(f"[{hi}:v]format=rgba,fade=t=out:st={HOOK_DUR-0.35:.2f}:d=0.35:alpha=1[hk]")
    parts.append(f"[vcap][hk]overlay=x=(W-w)/2:y={rest}:enable='between(t,0,{HOOK_DUR})'[vout]")
    fc=";".join(parts)
    od=os.path.join(HERE,"finals_ig"); os.makedirs(od,exist_ok=True)
    out=os.path.join(od,f"{cid:02d}_{slug}_ig.mp4")
    cmd=[FF,"-y","-nostdin"]+inputs+["-filter_complex",fc,"-map","[vout]","-map","0:a",
         "-r","30","-c:v","libx264","-crf","19","-preset","veryfast","-pix_fmt","yuv420p",
         "-c:a","aac","-b:a","192k","-movflags","+faststart","-t",f"{dur+0.1:.2f}",out]
    p=subprocess.run(cmd,capture_output=True,text=True)
    if p.returncode!=0: print("FAIL\n",p.stderr[-1500:]); return None
    print(f"#{cid} IG ✓ card {hw}x{hh} rest@{rest} -> {out}"); return out

if __name__=="__main__":
    cid=int(sys.argv[1]); lines=sys.argv[2:]
    composite_ig(cid,lines)
