#!/usr/bin/env python3
"""Bellefair single-word captions (Sam/Harry ref 2026-07-07): ONE word at a time,
elegant serif, centred low, soft shadow — matches the reference reels. Output
caps/<id>/bellefair.ass. Composite suppresses these during the hook card + any b-roll.

Pass 'box' to draw white text on an opaque BLACK BOX (for busy/low-contrast backgrounds):
  python cap_bellefair.py 3 box
"""
import json, os, re, sys
HERE=os.path.dirname(os.path.abspath(__file__))
PLAN={c["id"]:c for c in json.load(open(os.path.join(HERE,"plan.json")))}

def cc(t):
    cs=int(round(t*100)); h=cs//360000; cs%=360000; m=cs//6000; cs%=6000; s=cs//100; cs%=100
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def disp(w):
    return re.sub(r"^\W+|\W+$","",w)   # keep natural case, strip edge punctuation

Y=1450
# plain: white serif + soft shadow. box: white serif on opaque black box (BorderStyle 3).
STYLE_PLAIN="Style: B,Bellefair,120,&H00FFFFFF,&H00FFFFFF,&H00141414,&H90000000,0,0,0,0,100,100,1,0,1,3,5,5,60,60,60,1"
STYLE_BOX  ="Style: B,Bellefair,112,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,1,0,3,20,6,5,60,60,60,1"

def head(boxed):
    return ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n"
            "WrapStyle: 2\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
            "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
            "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            f"{STYLE_BOX if boxed else STYLE_PLAIN}\n\n[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

def build(clip, boxed=False, per=1):
    cid=clip["id"]; dur=clip["out_dur"]; words=clip["capwords"]
    d=os.path.join(HERE,"caps",f"{cid:02d}"); os.makedirs(d,exist_ok=True)
    evs=[]; n=len(words); i=0
    while i<n:                                    # group `per` words per on-screen caption
        grp=words[i:i+per]
        toks=[t for t in (disp(w["text"]) for w in grp) if t]
        st=grp[0]["t"]
        en=words[i+per]["t"] if i+per<n else min(grp[-1]["e"]+0.3, dur)
        if toks:
            if en<=st: en=st+0.12
            text=f"{{\\an5\\pos(540,{Y})\\fad(60,70)}}{' '.join(toks)}"
            evs.append((st,en,text))
        i+=per
    body="".join(f"Dialogue: 0,{cc(s)},{cc(e)},B,,0,0,0,,{t}\n" for s,e,t in evs)
    open(os.path.join(d,"bellefair.ass"),"w").write(head(boxed)+body)
    print(f"#{cid:02d} {clip['slug']:<28} {len(evs)} caps ({per}/screen) {'[BOX]' if boxed else ''}")

if __name__=="__main__":
    # Sam LOCKED default (2026-07-07): 2 words per screen on an opaque BLACK BOX.
    # Override with 'plain' (no box) or 'per1' (one word) if ever needed.
    args=[a for a in sys.argv[1:]]
    boxed="plain" not in args
    per=1 if "per1" in args else 2
    ids=[int(x) for x in args if x.isdigit()] or list(PLAN)
    for i in ids: build(PLAN[i], boxed=boxed, per=per)
