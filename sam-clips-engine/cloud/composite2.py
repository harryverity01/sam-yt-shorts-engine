#!/usr/bin/env python3
"""v3 composite: base + real b-roll cutaways (under) + karaoke ASS (last). NO music."""
import json, os, subprocess, sys
import imageio_ffmpeg
HERE=os.path.dirname(os.path.abspath(__file__))
FF=imageio_ffmpeg.get_ffmpeg_exe()
PLAN={c["id"]:c for c in json.load(open(os.path.join(HERE,"plan.json")))}
OUT=os.path.join(HERE,"finals"); os.makedirs(OUT,exist_ok=True)

def load(p): return json.load(open(p)) if os.path.exists(p) else []

def _t2s(t): h,m,s=t.split(":"); return int(h)*3600+int(m)*60+float(s)

def _trim(src, dst, wins):
    """Drop caption events overlapping any window in `wins`."""
    if not wins: return src
    out=[]
    for ln in open(src):
        if ln.startswith("Dialogue:"):
            f=ln.split(","); st=_t2s(f[1]); en=_t2s(f[2])
            if any(st<we and en>ws for ws,we in wins): continue
        out.append(ln)
    open(dst,"w").write("".join(out)); return dst

def caption_ass(cid, brolls):
    """Prefer Bellefair single-word captions if generated (suppress under ANY b-roll so
    they never obstruct what's on screen); else the karaoke look (suppress over DMs only)."""
    d=os.path.join(HERE,"caps",f"{cid:02d}")
    bf=os.path.join(d,"bellefair.ass")
    if os.path.exists(bf):
        return _trim(bf, os.path.join(d,"bellefair_clean.ass"),
                     [(b["start"],b["end"]) for b in brolls])
    return _trim(os.path.join(d,"karaoke.ass"), os.path.join(d,"karaoke_nodm.ass"),
                 [(b["start"],b["end"]) for b in brolls if b.get("kind")=="dm"])

def composite(cid):
    clip=PLAN[cid]; slug=clip["slug"]; dur=clip["out_dur"]
    base=os.path.join(HERE,"bases",f"base_{cid:02d}.mp4")
    brolls=load(os.path.join(HERE,"broll",f"{cid:02d}","spec.json"))
    ass=caption_ass(cid,brolls)
    inputs=["-i",base]; parts=[]; cur="[0:v]"; idx=1
    for b in brolls:
        f=b["file"]; s,e=b["start"],b["end"]; d=round(e-s,3)
        is_vid=f.lower().endswith((".mp4",".mov"))
        inputs+=(["-i",f] if is_vid else ["-loop","1","-t",f"{d:.3f}","-i",f])
        parts.append(f"[{idx}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                     f"crop=1080:1920,setpts=PTS-STARTPTS+{s}/TB[b{idx}]")
        nl=f"[v{idx}]"
        parts.append(f"{cur}[b{idx}]overlay=0:0:enable='between(t,{s},{e})':eof_action=pass{nl}")
        cur=nl; idx+=1
    # karaoke captions LAST
    parts.append(f"{cur}ass={ass}:fontsdir={os.path.join(HERE,'assets/fonts')}[vout]")
    fc=";".join(parts)
    out=os.path.join(OUT,f"{cid:02d}_{slug}.mp4")
    cmd=[FF,"-y","-nostdin"]+inputs+["-filter_complex",fc,"-map","[vout]","-map","0:a",
         "-r","30","-c:v","libx264","-crf","19","-preset","veryfast","-pix_fmt","yuv420p",
         "-c:a","aac","-b:a","192k","-movflags","+faststart","-t",f"{dur+0.1:.2f}",out]
    p=subprocess.run(cmd,capture_output=True,text=True)
    if p.returncode!=0:
        print(f"#{cid} FAIL\n{p.stderr[-1200:]}"); return False
    print(f"#{cid:02d} {slug:<30} {dur:5.1f}s broll={len(brolls)} caps=karaoke noMusic ✓")
    return True

if __name__=="__main__":
    ids=[int(x) for x in sys.argv[1:]] if len(sys.argv)>1 else list(PLAN)
    ok=sum(composite(i) for i in ids); print(f"done {ok}/{len(ids)}")
