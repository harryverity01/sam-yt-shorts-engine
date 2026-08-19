#!/usr/bin/env python3
"""v3 b-roll: REAL photos + REAL screenshots, timed to the SPOKEN word, yellow
highlighter (not red circles), clean photos. Renders -> broll/<id>/spec.json."""
import json, os, sys, glob
from PIL import Image
from edgeboil import render_all
import dmphone
HERE=os.path.dirname(os.path.abspath(__file__))
P=lambda n:f"broll_src/stock/{n}.jpg"
SH=lambda n:f"broll_src/shots/{n}_crop.png"
HLY="rgba(255,221,0,0.5)"

def dm(convo, hand=None, sub="Active now", banner=None, dur=3.0, handpos=None):
    """A RECREATED Instagram DM conversation beat (Sam locked: for DMs we recreate, since
    a private DM can't be screenshotted). Rendered by dmphone.py."""
    b={"kind":"dm","convo":convo,"dur":dur,"sub":sub}
    if hand: b["hand"]=hand
    if banner: b["banner"]=banner
    if handpos: b["handpos"]=handpos
    return b

def _downscale():
    for f in glob.glob("broll_src/shots/*_crop.png"):
        im=Image.open(f)
        if im.width>1300: im.resize((1300,int(1300*im.height/im.width))).save(f)
    for f in glob.glob("broll_src/stock/*.jpg")+["broll_src/hero/trump.jpg"]:
        if not os.path.exists(f): continue
        im=Image.open(f).convert("RGB")
        if im.width>1300: im.resize((1300,int(1300*im.height/im.width))).save(f,quality=88)

# NOTE: `stamp` arg is accepted but IGNORED everywhere — Sam locked "no red stamps"
# (NIGHTMARE/SCAM/etc.) 2026-06-27. Kept in the signature so existing calls don't break.
def photo(img,hand=None,stamp=None,dur=2.3):
    b={"kind":"photo","img":img,"dur":dur}          # clean: no circle, no stamp
    if hand:b["hand"]=hand
    return b

def shot(img,hand=None,stamp=None,dur=2.6,hi=(0.5,0.30),hlw=0.82,hlh=0.15,cardw=1020,rot=-1.6):
    iw,ih=Image.open(img).size
    chh=int(cardw*ih/iw); cardx=(1080-cardw)//2; cardy=max(150,(1920-chh)//2-30)
    bw=int(cardw*hlw); bh=int(chh*hlh)
    bx=int(cardx+cardw*hi[0]-bw/2); by=int(cardy+chh*hi[1]-bh/2)
    anno={"type":"highlight","geo":[bx,by,bw,bh],"color":HLY}
    b={"kind":"shot","img":img,"dur":dur,"cardw":cardw,"cardy":cardy,"rot":rot,"anno":anno}
    if hand:b["hand"]=hand; b["handpos"]=[120,1500,60,-3]
    return b

# beats timed to when Sam SAYS the thing (out-times verified from plan.json)
PLAN={
# Clip 1: REAL screenshots of actual Claude Code / Gemini / Whisper as edge-boil graphics.
1:[(0.8,shot(SH("claudehero"),hand="but it's blind + deaf",hi=(0.5,0.60),hlw=0.66,hlh=0.11,dur=3.0)),
   (6.4,shot(SH("geminispark"),hand="Gemini = eyes + ears",hi=(0.5,0.80),hlw=0.62,hlh=0.11,dur=2.6,cardw=1044)),      # "Gemini" @6.7
   (9.7,shot(SH("whispergh"),hand="Whisper hears even better",hi=(0.66,0.13),hlw=0.46,hlh=0.09,dur=2.4))],            # "Whisper" @10.0
# Clip 2: AI reads + replies to his Instagram DMs -> recreated DM conversation.
2:[(2.6,shot(SH("claudehero"),hand="runs 24/7 on a schedule",hi=(0.5,0.60),hlw=0.66,hlh=0.11,dur=2.8)),
   (9.3,dm([{"who":"them","text":"hey! that reel on automating DMs was 🔥"},
            {"who":"them","text":"do you reply to everyone yourself??"},
            {"who":"me","text":"honestly an AI handles my DMs now 😄","hi":True},
            {"who":"me","text":"checks every few mins + replies for me"},
            {"who":"them","text":"no way, that's actually genius"}],
        hand="it reads + replies as him",dur=3.2))],                                                                  # "responds to them" @11.6
# Clip 3: how people spot AI in his DMs -> recreated DM convo + the timing tells.
3:[(7.4,dm([{"who":"them","text":"yo are you a real person or a bot lol"},
            {"who":"me","text":"haha very real — what's up? 😂","hi":True},
            {"who":"them","text":"ok good 😅 loved your last post"},
            {"who":"me","text":"appreciate you 🙏 what stood out?"},
            {"who":"them","text":"the bit on staying consistent"}],
        dur=3.2)),                                                                                                    # "people think it's me" @8 (label removed per Sam)
   (12.2,dm([{"who":"them","text":"you around?","time":"9:02 AM"},
             {"who":"me","text":"yep — what's up","time":"9:04 AM","hi":True},
             {"who":"them","text":"got a sec later?","time":"2:15 PM"},
             {"who":"me","text":"yep — what's up","time":"2:17 PM","hi":True}],
        dur=2.8)),                                                                                                    # "pattern recognition" @15 (label removed per Sam)
   (18.3,dm([{"who":"them","text":"wait did you just reply in like 5 seconds 😂"},
             {"who":"me","text":"...maybe 🤖","hi":True},
             {"who":"them","text":"lol knew it — no one replies that fast"}],
        dur=2.6))],                                                                                                   # "within 10 seconds" @19 (label removed per Sam)
4:[(4.0,shot(SH("microsoft"),hand="Word + Microsoft",hi=(0.5,0.16),stamp="WORD")),            # "Word/Microsoft" @4.3-5.1
   (17.6,photo(P("burnout"),hand="people burn out",stamp="NIGHTMARE")),                       # "burn out" @18.0
   (40.3,photo(P("code"),hand="AI does it in 10 min"))],                                       # "minutes" @42.2
5:[(2.5,shot(SH("microsoft"),hand="...a C-player",hi=(0.5,0.16),stamp="C PLAYER")),            # "Microsoft C player" @2.8
   (5.2,shot(SH("google"),hand="A-player",dur=2.0,hi=(0.5,0.22))),                             # "Google" @5.3
   (7.2,shot(SH("apple"),hand="A-player",dur=2.0,hi=(0.5,0.28)))],                             # "Apple" @5.8
6:[(1.4,photo(P("handshake"),hand="DM setters + editors")),
   (5.0,photo(P("burnout"),hand="managing them = hell",stamp="NIGHTMARE"))],
7:[(1.4,photo(P("cash"),hand="not I cant afford it",stamp="HOW?"))],
8:[(1.8,photo(P("handshake"),hand="sold for half a billion")),                                # "company/billion" @2-3
   (13.2,shot(SH("cole_pr"),hand="Cole Gordon, the best",dur=2.6,hi=(0.62,0.42),hlw=0.42,hlh=0.36,stamp="$7M/MO")),  # "Cole Gordon" @13.4
   (15.6,photo(P("cash"),hand="7 million a month",stamp="LEARN SALES"))],                      # "million" @15.8
9:[(2.0,photo(P("creator"),hand="just post",stamp="COLD FEET")),
   (10.0,shot(SH("instagram"),hand="6x a day",dur=2.3))],
10:[(2.0,photo(P("government"),hand="they want you employed",stamp="A JOB")),
    (12.0,photo(P("invoice"),hand="invoices, tax, tracking"))],
11:[(1.2,shot(SH("bankfees"),hand="banks' hidden “junk fees”",hi=(0.145,0.48),hlw=0.27,hlh=0.15,cardw=1044,dur=3.0)),  # real CFPB headline (was generic bankcard)
    (13.9,shot(SH("claude"),hand="even AI agreed",hi=(0.5,0.30),dur=2.2))],                    # "I ask AI" @14.3                    # "I ask AI" @14.3
12:[(1.4,photo("broll_src/hero/trump.jpg",hand="reputation = money",stamp="THE FUTURE")),
    (8.5,shot(SH("cnbc"),hand="764,000 lost money",hi=(0.5,0.66),hlh=0.13,stamp="$2B LOST",dur=2.8)),
    (18.0,shot(SH("cbs"),hand="everyone will do this",dur=2.5,hi=(0.5,0.22)))],
13:[(2.0,photo(P("phonecrypto"),hand="he sent them his gains")),
    (8.5,shot(SH("coinmarketcap"),hand="they thought it was a scam",dur=2.5,hi=(0.5,0.18),hlh=0.1))],
14:[(1.4,shot(SH("instagram"),hand="social media",dur=2.2)),
    (9.8,shot(SH("tiktok"),hand="open TikTok",dur=2.0,hi=(0.5,0.2))),                           # "TikTok" @10.5
    (12.0,photo(P("crying"),hand="a girl crying",stamp="RAW"))],                                # "crying" @11.7
15:[(1.2,photo(P("cash"),hand="men strive for 100K",stamp="STRIVE")),
    (7.0,photo(P("cash"),hand="women: Im comfortable",dur=2.3))],
}

def build(ids):
    _downscale()
    card_items=[]; dm_items=[]; meta=[]
    for cid in ids:
        os.makedirs(os.path.join(HERE,"broll",f"{cid:02d}"),exist_ok=True)
        for k,(at,beat) in enumerate(PLAN.get(cid,[])):
            out=os.path.join(HERE,"broll",f"{cid:02d}",f"b{k}.mp4")
            (dm_items if beat["kind"]=="dm" else card_items).append((beat,out))
            meta.append((cid,k,at,beat,out))
    print(f"rendering {len(card_items)} cards + {len(dm_items)} DM beats...",flush=True)
    results={}
    if card_items: results.update(dict(render_all(card_items)))
    if dm_items:   results.update(dict(dmphone.render_all_dm(dm_items)))
    specs={}
    for cid,k,at,beat,out in meta:
        if results.get(out):
            specs.setdefault(cid,[]).append({"file":out,"start":round(at,2),"end":round(at+beat["dur"],2),"kind":beat["kind"]})
            print(f"  #{cid:02d} b{k} {beat['kind']:5} @{at:4.1f} ✓",flush=True)
        else: print(f"  #{cid:02d} b{k} FAIL",flush=True)
    res={}
    for cid in ids:
        sp=sorted(specs.get(cid,[]),key=lambda x:x["start"])
        json.dump(sp,open(os.path.join(HERE,"broll",f"{cid:02d}","spec.json"),"w"),indent=1)
        res[cid]=len(sp)
    return res

if __name__=="__main__":
    ids=[int(x) for x in sys.argv[1:]] if len(sys.argv)>1 else list(PLAN)
    r=build(ids); print("beats:",r,"total",sum(r.values()))
