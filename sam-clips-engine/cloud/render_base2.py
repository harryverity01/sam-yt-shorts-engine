#!/usr/bin/env python3
"""Vertical, graded BASE cut per clip from plan.json.

Two differences from render_base.py (Danielle):
  * each EDL range names its own section file under sec/ (one pull per clip)
  * both podcasts are locked TWO-SHOTS, so the crop follows the speaker: Sam is
    camera-left, the guest camera-right. plan.json carries "side" per range.

Method is the proven one: per-segment input-seek extract with crop + grade + 30ms
audio fades baked in, then concat-demux (stream copy).
"""
import json, os, subprocess, sys, shutil
import imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
FF = imageio_ffmpeg.get_ffmpeg_exe()
PLAN = json.load(open(os.path.join(HERE, "plan.json")))
OUT = os.path.join(HERE, "bases")
os.makedirs(OUT, exist_ok=True)

# crop x-offset into the 1920x1080 two-shot, per shoot and per speaker side
CROPX = {("kv", "L"): 100, ("kv", "R"): 1180,
         ("ml", "L"): 200, ("ml", "R"): 1150}
CW, CH = 608, 1080

GRADE = ("curves=red='0/0 0.5/0.53 1/1':blue='0/0 0.5/0.45 1/1',"
         "eq=saturation=0.95:contrast=1.03:brightness=0.01")
FADE = 0.03


def vf_for(sec, side):
    shoot = "kv" if sec.startswith("kv") else "ml"
    x = CROPX[(shoot, side)]
    return f"crop={CW}:{CH}:{x}:0,scale=1080:1920,{GRADE},format=yuv420p"


def render(clip):
    cid = clip["id"]
    tmp = os.path.join(OUT, f"tmp_{cid:02d}")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    segs = []
    for i, r in enumerate(clip["ranges"]):
        src = os.path.join(HERE, "sec", f"{r['sec']}.mp4")
        s, e = r["start"], r["end"]
        d = round(e - s, 3)
        seg = os.path.join(tmp, f"seg_{i:03d}.mp4")
        af = f"afade=t=in:st=0:d={FADE},afade=t=out:st={max(0, d-FADE):.3f}:d={FADE}"
        cmd = [FF, "-y", "-nostdin", "-ss", f"{s:.3f}", "-i", src, "-t", f"{d:.3f}",
               "-vf", vf_for(r["sec"], r.get("side", "R")), "-af", af,
               "-r", "30", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
               "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
               "-video_track_timescale", "30000", seg]
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode != 0 or not os.path.exists(seg):
            print(f"#{cid} seg{i} FAIL\n{p.stderr[-700:]}")
            return False
        segs.append(seg)
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("\n".join(f"file '{s}'" for s in segs) + "\n")
    out = os.path.join(OUT, f"base_{cid:02d}.mp4")
    p = subprocess.run([FF, "-y", "-nostdin", "-f", "concat", "-safe", "0", "-i", lst,
                        "-c", "copy", "-movflags", "+faststart", out],
                       capture_output=True, text=True)
    if p.returncode != 0:
        p = subprocess.run([FF, "-y", "-nostdin", "-f", "concat", "-safe", "0", "-i", lst,
                            "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                            "-c:a", "aac", "-b:a", "192k", out], capture_output=True, text=True)
    if p.returncode != 0:
        print(f"#{cid} concat FAIL\n{p.stderr[-700:]}")
        return False
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"#{cid:02d} {clip['slug']:<30} {clip['out_dur']:5.1f}s  "
          f"{os.path.getsize(out)/1e6:5.1f}MB  {len(clip['ranges'])} segs ok")
    return True


if __name__ == "__main__":
    ids = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else [c["id"] for c in PLAN]
    ok = sum(render(c) for c in PLAN if c["id"] in ids)
    print(f"done {ok}/{len(ids)}")
