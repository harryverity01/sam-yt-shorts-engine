#!/usr/bin/env python3
"""Build faithful EDLs + caption timelines for the 15 Sam x Danielle clips.

Per clip: start on the hook, keep ONLY Sam (speaker_0) words (+ explicit Danielle
keeps), drop umms/false-starts + flagged tangents, silence-strip between words.
Outputs plan.json (ranges + remapped caption words) and prints the as-cut transcript
for each clip so faithfulness can be eyeballed before rendering.
"""
import json, re, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORDS = json.load(open(os.path.join(HERE, "source.words.json")))["words"]
SAM = "speaker_0"

# Sam locked cut knobs (brand_assets.json) ----------------------------------
MAX_GAP, LEAD_PAD, TAIL_PAD, FINAL_TAIL = 0.28, 0.05, 0.08, 0.18
FILLER = {"um","uh","uhh","uhm","mm","mmhmm","hmm","mhm","mmm","er","erm","eh",
          "uhhuh","hm","mmhm"}

def norm(t): return re.sub(r"[^\w']","",(t or "")).lower()

SPOKEN = [w for w in WORDS if w.get("type","word")=="word" and w.get("start") is not None]
SPOKEN.sort(key=lambda w: w["start"])

def words_in(a,b,who=None):
    return [w for w in SPOKEN if a-0.02 <= w["start"] < b and (who is None or w.get("speaker_id")==who)]

def find_anchor(phrase, win_a, win_b, who=SAM, want="start"):
    """Find contiguous runs of `who` words in [win_a,win_b] matching phrase tokens.
    Return the FIRST match's start (want='start') or the LAST match's end (want='end')."""
    toks = [norm(x) for x in phrase.split() if norm(x)]
    pool = words_in(win_a, win_b, who)
    npool = [norm(w["text"]) for w in pool]
    hits=[]
    for i in range(len(pool)-len(toks)+1):
        if npool[i:i+len(toks)] == toks:
            hits.append((pool[i]["start"], pool[i+len(toks)-1]["end"]))
    if hits:
        return hits[0][0] if want=="start" else hits[-1][1]
    raise SystemExit(f"ANCHOR NOT FOUND ({want}): {phrase!r} in [{win_a},{win_b}]  "
                     f"pool={' '.join(npool)}")

def in_ranges(t, rngs):
    return any(a<=t<=b for a,b in (rngs or []))

def clip_words(clip_start, clip_end, drops, keep_d):
    """Kept words: Sam in-window minus filler/drops, plus Danielle keep-ranges."""
    out=[]
    for w in SPOKEN:
        s=w["start"]
        if not (clip_start-0.02 <= s < clip_end): continue
        is_sam = w.get("speaker_id")==SAM
        keep_dan = (not is_sam) and in_ranges((s+w["end"])/2, keep_d)
        if not (is_sam or keep_dan): continue
        if in_ranges((s+w["end"])/2, drops): continue
        out.append(w)
    out.sort(key=lambda w: w["start"])
    # filler + stutter strip
    cleaned=[]
    for i,w in enumerate(out):
        nt=norm(w["text"])
        if nt in FILLER: continue
        if cleaned and norm(cleaned[-1]["text"])==nt and nt not in ("no","so","very","really"):
            cleaned[-1]=w; continue   # collapse immediate duplicate ("I, I, I")
        # prefix-fragment stutter: short token that is a prefix of the next ("w-"->"we")
        if i+1<len(out):
            nx=norm(out[i+1]["text"])
            if len(nt)<=2 and nx.startswith(nt) and nt!=nx and nt not in ("a","i","it","is","to","do","no","so","my","ai","go"):
                continue
        cleaned.append(w)
    return cleaned

def build_ranges(kept):
    runs=[[kept[0]]]
    for prev,w in zip(kept,kept[1:]):
        (runs.append([w]) if (w["start"]-prev["end"])>MAX_GAP else runs[-1].append(w))
    rngs=[]
    for i,run in enumerate(runs):
        last = i==len(runs)-1
        rngs.append({"start":max(0,run[0]["start"]-LEAD_PAD),
                     "end":run[-1]["end"]+(FINAL_TAIL if last else TAIL_PAD),
                     "w0":run[0],"w1":run[-1],"run":run})
    for p,r in zip(rngs,rngs[1:]):
        if r["start"]<p["end"]: r["start"]=p["end"]
    return rngs

def map_out(t, rngs):
    off=0.0
    for r in rngs:
        if t<r["start"]: return round(off,3)
        if t<=r["end"]: return round(off+(t-r["start"]),3)
        off+=r["end"]-r["start"]
    return round(off,3)

# ---- the 15 clips (times in seconds) --------------------------------------
def ts(m,s): return m*60+s
C = [
 dict(id=1, slug="claude-blind-and-deaf", win=(ts(81,38),ts(82,45)),
      start="Claude is blind and deaf", end="200 bucks a month",
      drops=[(ts(82,13),ts(82,18)), (4948.84, 4953.1)]),
 dict(id=2, slug="ai-runs-my-instagram", win=(ts(82,44),ts(83,12)),
      start="I have basically AI running for me", end="open the computer again", drops=[]),
 dict(id=3, slug="how-people-spot-ai", win=(ts(77,20),ts(78,40)),
      start="AI is not random enough", end="one time he responds at the moment",
      drops=[(ts(77,42),4695.1)]),
 dict(id=4, slug="microsoft-burnout", win=(ts(86,40),ts(87,52)),
      start="they have a lot of employees", end="10 minutes, and it's done",
      drops=[(5208.7,5212.75),(5215.5,5216.5),(5219.0,5219.8),
             (5227.7,5228.75),(5235.7,5236.6),(5239.6,5240.95)]),
 dict(id=5, slug="microsoft-c-player", win=(ts(87,58),ts(88,35)),
      start="everything is B players and A players", end="gonna be so common",
      drops=[], keep_d=[(ts(88,24),ts(88,29))]),
 dict(id=6, slug="managing-people-nightmare", win=(ts(85,37),ts(85,56)),
      start="you go and hire DM setters", end="it's hard", drops=[]),
 dict(id=7, slug="stop-saying-cant-afford", win=(ts(27,22),ts(27,47)),
      start="when you're an entrepreneur", end="How do I afford it", drops=[]),
 dict(id=8, slug="half-a-billion-learn-sales", win=(ts(73,18),ts(74,55)),
      keep_spans=[(4402.0,4416.5),(4456.0,4464.0),(4475.0,4479.0),(4480.0,4485.5)],
      start=None, end=None, drops=[]),
 dict(id=9, slug="most-people-get-cold-feet", win=(ts(36,51),ts(37,32)),
      start="I don't think many people understood", end="Let's post",
      drops=[(2216.05,2221.6)]),
 dict(id=10, slug="trained-to-need-a-job", win=(ts(94,12),ts(94,49)),
      start="governments are so corrupt", end="this is why people gave up", drops=[]),
 dict(id=11, slug="your-bank-is-scamming-you", win=(ts(65,3),ts(65,33)),
      start="I just found out that my bank is scamming me", end="Yeah", drops=[]),  # end on Sam's confirming "Yeah." so "...right to be" isn't a cut-off trail
 dict(id=12, slug="trump-future-of-money", win=(ts(52,46),ts(53,25)),
      start="One of the most interesting things", end="Everyone's gonna do that", drops=[]),
 dict(id=13, slug="my-family-thought-i-got-hacked", win=(ts(50,52),ts(51,25)),
      start="I started sending my family", end="people just don't get it", drops=[]),
 dict(id=14, slug="social-media-more-real", win=(ts(97,51),ts(98,32)),
      start="social media is more real than real life", end="really real and raw and extreme",
      drops=[(5892.0,5896.7)]),
 dict(id=15, slug="men-women-chase-money", win=(ts(108,35),ts(109,3)),
      start="a man, when you tell him", end="I will work less now", drops=[]),
]

plan=[]
print("="*70)
for c in C:
    a,b = c["win"]
    if c.get("keep_spans"):
        # gather Sam words inside any keep_span, then filler-strip
        raw=[w for w in SPOKEN if w.get("speaker_id")==SAM
             and any(s-0.02<=w["start"]<e for s,e in c["keep_spans"])]
        if not raw: raise SystemExit(f"#{c['id']} keep_spans empty")
        cs, ce = raw[0]["start"], raw[-1]["end"]
        kept = clip_words(cs-0.01, ce+0.05, c.get("drops",[]), c.get("keep_d",[]))
        kept = [w for w in kept if any(s-0.05<=w["start"]<e+0.05 for s,e in c["keep_spans"])]
    else:
        cs = find_anchor(c["start"], a, b, SAM, "start")
        ce = find_anchor(c["end"], a, b, SAM, "end")
        kept = clip_words(cs, ce, c.get("drops",[]), c.get("keep_d",[]))
    rngs = build_ranges(kept)
    out_dur = sum(r["end"]-r["start"] for r in rngs)
    # caption words: each kept word -> out time
    capwords=[]
    for w in kept:
        capwords.append({"t":map_out(w["start"],rngs),"e":map_out(w["end"],rngs),
                         "text":w["text"]})
    transcript=" ".join(w["text"] for w in kept)
    transcript=re.sub(r"\s+([,.\?!])",r"\1",transcript)
    plan.append(dict(id=c["id"],slug=c["slug"],
                     ranges=[{"start":round(r["start"],3),"end":round(r["end"],3)} for r in rngs],
                     out_dur=round(out_dur,2),capwords=capwords,transcript=transcript))
    print(f"#{c['id']:>2} {c['slug']:<30} {out_dur:5.1f}s  {len(rngs)} cuts")
    print(f"    {transcript}")
    print("-"*70)

json.dump(plan, open(os.path.join(HERE,"plan.json"),"w"), indent=1)
print(f"\nTotal: {sum(p['out_dur'] for p in plan):.0f}s across {len(plan)} clips -> plan.json")
