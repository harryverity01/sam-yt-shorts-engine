#!/usr/bin/env python3
"""Render the tight, vertical, graded BASE cut for each clip from plan.json.

Hard-rule method: per-segment INPUT-SEEK extract (fast) with Sam reframe + grade +
30ms audio fades baked per segment, then lossless concat-demux. One small encode per
range. Output: bases/base_<id>.mp4 (1080x1920, Sam's voice only, tight).
"""
import json, os, subprocess, sys, shutil
import imageio_ffmpeg
HERE=os.path.dirname(os.path.abspath(__file__))
FF=imageio_ffmpeg.get_ffmpeg_exe()
SRC=os.path.join(HERE,"source.mp4")
PLAN=json.load(open(os.path.join(HERE,"plan.json")))
OUT=os.path.join(HERE,"bases"); os.makedirs(OUT,exist_ok=True)

CROP="crop=540:960:96:40,scale=1080:1920"
# Per-clip reframe overrides: Sam sits differently across the 2hr shoot, so a couple
# of clips need the crop window nudged to keep him centred like clip 1.
# #11: at 65min Sam leans forward/right — shift window right (x 96->135) to re-centre him.
CROP_OVERRIDE={11:"crop=540:960:135:40,scale=1080:1920"}
GRADE=("curves=red='0/0 0.5/0.53 1/1':blue='0/0 0.5/0.45 1/1',"
       "eq=saturation=0.95:contrast=1.03:brightness=0.01")
FADE=0.03

def run(cmd):
    return subprocess.run(cmd,capture_output=True,text=True)

def render(clip):
    rngs=clip["ranges"]; cid=clip["id"]
    crop=CROP_OVERRIDE.get(cid,CROP)
    tmp=os.path.join(OUT,f"tmp_{cid:02d}"); shutil.rmtree(tmp,ignore_errors=True); os.makedirs(tmp)
    segs=[]
    for i,r in enumerate(rngs):
        s,e=r["start"],r["end"]; d=round(e-s,3)
        seg=os.path.join(tmp,f"seg_{i:03d}.mp4")
        af=f"afade=t=in:st=0:d={FADE},afade=t=out:st={max(0,d-FADE):.3f}:d={FADE}"
        cmd=[FF,"-y","-nostdin","-ss",f"{s:.3f}","-i",SRC,"-t",f"{d:.3f}",
             "-vf",f"{crop},{GRADE},format=yuv420p","-af",af,
             "-r","30","-c:v","libx264","-crf","18","-preset","veryfast",
             "-c:a","aac","-b:a","192k","-ar","44100","-video_track_timescale","30000",seg]
        p=run(cmd)
        if p.returncode!=0 or not os.path.exists(seg):
            print(f"#{cid} seg{i} FAIL\n{p.stderr[-800:]}"); return False
        segs.append(seg)
    # concat demuxer (identical params -> stream copy)
    lst=os.path.join(tmp,"list.txt")
    open(lst,"w").write("\n".join(f"file '{s}'" for s in segs)+"\n")
    out=os.path.join(OUT,f"base_{cid:02d}.mp4")
    p=run([FF,"-y","-nostdin","-f","concat","-safe","0","-i",lst,"-c","copy",
           "-movflags","+faststart",out])
    if p.returncode!=0:  # fallback: re-encode concat
        p=run([FF,"-y","-nostdin","-f","concat","-safe","0","-i",lst,
               "-c:v","libx264","-crf","18","-preset","veryfast","-c:a","aac","-b:a","192k",out])
    if p.returncode!=0:
        print(f"#{cid} concat FAIL\n{p.stderr[-800:]}"); return False
    shutil.rmtree(tmp,ignore_errors=True)
    sz=os.path.getsize(out)/1e6
    print(f"#{cid:02d} {clip['slug']:<30} {clip['out_dur']:5.1f}s  {sz:5.1f}MB  {len(rngs)} segs ✓")
    return True

if __name__=="__main__":
    ids=[int(x) for x in sys.argv[1:]] if len(sys.argv)>1 else [c["id"] for c in PLAN]
    ok=sum(render(c) for c in PLAN if c["id"] in ids)
    print(f"done: {ok}/{len(ids)}")
