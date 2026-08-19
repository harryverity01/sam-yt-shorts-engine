#!/usr/bin/env python3
"""Karaoke captions: full running line, active word highlighted as Sam says it.
Outputs caps/<id>/karaoke.ass (burned last via ffmpeg ass=... in composite)."""
import json, os, re, sys
HERE=os.path.dirname(os.path.abspath(__file__))
PLAN={c["id"]:c for c in json.load(open(os.path.join(HERE,"plan.json")))}

WHITE="&H00FFFFFF"; ACTIVE="&H0030F6FF"   # active word = warm yellow (BBGGRR)
MAXW=3        # words per visible line
GAP_BREAK=0.6

def cc(t):
    cs=int(round(t*100)); h=cs//360000; cs%=360000; m=cs//6000; cs%=6000; s=cs//100; cs%=100
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def disp(w):
    return re.sub(r"^[^\w$%]+|[^\w$%']+$","",w).upper()

HEAD="""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: K,Archivo Black,78,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,1,0,1,7,3,5,40,40,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def lines_for(words):
    out=[]; cur=[]
    for i,w in enumerate(words):
        cur.append(w)
        nxt=words[i+1] if i+1<len(words) else None
        endsent=bool(re.search(r"[.?!]$", w["text"]))
        biggap=nxt and (nxt["t"]-w["e"]>GAP_BREAK)
        if len(cur)>=MAXW or endsent or biggap or nxt is None:
            out.append(cur); cur=[]
    return out

def build(clip):
    cid=clip["id"]; dur=clip["out_dur"]; words=clip["capwords"]
    d=os.path.join(HERE,"caps",f"{cid:02d}"); os.makedirs(d,exist_ok=True)
    evs=[]
    for line in lines_for(words):
        toks=[disp(w["text"]) for w in line]
        toks=[t for t in toks if t]
        if not toks: continue
        n=len(line)
        for j in range(n):
            st=line[j]["t"]
            en=line[j+1]["t"] if j+1<n else min(line[j]["e"]+0.12, dur)
            if en<=st: en=st+0.08
            parts=[]
            for k,tk in enumerate(toks):
                col=ACTIVE if k==j else WHITE
                parts.append(f"{{\\c{col}}}{tk}")
            text="{\\an5\\pos(540,1190)}"+" ".join(parts)
            evs.append((st,en,text))
    evs.sort()
    body="".join(f"Dialogue: 0,{cc(s)},{cc(e)},K,,0,0,0,,{t}\n" for s,e,t in evs)
    open(os.path.join(d,"karaoke.ass"),"w").write(HEAD+body)
    print(f"#{cid:02d} {clip['slug']:<28} {len(evs)} karaoke events")
    return True

if __name__=="__main__":
    ids=[int(x) for x in sys.argv[1:]] if len(sys.argv)>1 else list(PLAN)
    for i in ids: build(PLAN[i])
