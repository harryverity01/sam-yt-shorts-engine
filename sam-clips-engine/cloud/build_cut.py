#!/usr/bin/env python3
"""Build the EDL + caption timeline for the 12 Karel/Melvin shorts.

Differs from cut_build.py (Danielle) in one way that matters: these clips are
GUEST-dominant, so we keep both speakers inside the window instead of Sam only.
Everything else is the locked method - anchor phrases, filler + stutter strip,
silence strip to whole-word runs, out-time map for the captions.

Each clip names its own section file under sec/ (one Higgsfield pull per clip).
"""
import json, re, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_GAP, LEAD_PAD, TAIL_PAD, FINAL_TAIL = 0.28, 0.05, 0.08, 0.18
FILLER = {"um", "uh", "uhh", "uhm", "mm", "mmhmm", "hmm", "mhm", "mmm", "er", "erm",
          "eh", "uhhuh", "hm", "mmhm", "mmmm", "uhhh"}
BANNED = {"fuck", "fucking", "shit"}


def norm(t):
    return re.sub(r"[^\w']", "", (t or "")).lower()


def load(sec):
    w = json.load(open(os.path.join(HERE, "words", f"{sec}.json")))["words"]
    sp = [x for x in w if x.get("type", "word") == "word" and x.get("start") is not None]
    sp.sort(key=lambda x: x["start"])
    return sp


def find_anchor(pool, phrase, want="start"):
    toks = [norm(x) for x in phrase.split() if norm(x)]
    npool = [norm(w["text"]) for w in pool]
    hits = []
    for i in range(len(pool) - len(toks) + 1):
        if npool[i:i + len(toks)] == toks:
            hits.append((pool[i]["start"], pool[i + len(toks) - 1]["end"]))
    if not hits:
        raise SystemExit(f"ANCHOR NOT FOUND ({want}): {phrase!r}")
    return hits[0][0] if want == "start" else hits[-1][1]


def in_ranges(t, rngs):
    return any(a <= t <= b for a, b in (rngs or []))


def resolve_drops(pool, pairs):
    out = []
    for s_ph, e_ph in (pairs or []):
        out.append((find_anchor(pool, s_ph, "start") - 0.02,
                    find_anchor(pool, e_ph, "end") + 0.02))
    return out


def clean(pool, a, b, drops, drop_words):
    out = [w for w in pool if a - 0.02 <= w["start"] < b
           and not in_ranges((w["start"] + w["end"]) / 2, drops)]
    cleaned = []
    for i, w in enumerate(out):
        nt = norm(w["text"])
        if nt in FILLER or nt in BANNED or nt in drop_words:
            continue
        if cleaned and norm(cleaned[-1]["text"]) == nt and nt not in ("no", "so", "very", "really", "yeah"):
            cleaned[-1] = w
            continue
        if i + 1 < len(out):
            nx = norm(out[i + 1]["text"])
            if len(nt) <= 2 and nx.startswith(nt) and nt != nx and nt not in (
                    "a", "i", "it", "is", "to", "do", "no", "so", "my", "ai", "go", "we", "of", "in", "on", "up", "he"):
                continue
        cleaned.append(w)
    return cleaned


SIDE = {  # section -> {speaker_id: crop side}. Sam is always camera-left.
 "kv1": {"speaker_1": "L", "speaker_0": "R"},
 "kv2": {"speaker_0": "L", "speaker_1": "R"},
 "kv3": {"speaker_1": "L", "speaker_0": "R"},
 "kv4": {"speaker_1": "L", "speaker_0": "R"},
 "kv5a": {"speaker_1": "L", "speaker_0": "R"},
 "kv5b": {"speaker_1": "L", "speaker_0": "R"},
 "kv6": {"speaker_1": "L", "speaker_0": "R"},
 "kv7": {"speaker_0": "L", "speaker_1": "R"},
 "ml1": {"speaker_0": "L", "speaker_1": "R"},
 "ml2": {"speaker_1": "L", "speaker_0": "R"},
 "ml3": {"speaker_1": "L", "speaker_0": "R"},
 "ml4": {"speaker_0": "L", "speaker_1": "R"},
 "ml5": {"speaker_1": "L", "speaker_0": "R"},
}


def dominant_side(sec, words, a, b):
    """Which speaker owns this range -> which side of the two-shot to crop."""
    ws = [w for w in words if a - 0.05 <= w["start"] <= b + 0.05]
    tally = {}
    for w in ws:
        sd = SIDE.get(sec, {}).get(w.get("speaker_id"), "R")
        tally[sd] = tally.get(sd, 0) + 1
    return max(tally, key=tally.get) if tally else "R"


def build_ranges(kept):
    runs = [[kept[0]]]
    for prev, w in zip(kept, kept[1:]):
        (runs.append([w]) if (w["start"] - prev["end"]) > MAX_GAP else runs[-1].append(w))
    rngs = []
    for i, run in enumerate(runs):
        last = i == len(runs) - 1
        rngs.append({"start": max(0, run[0]["start"] - LEAD_PAD),
                     "end": run[-1]["end"] + (FINAL_TAIL if last else TAIL_PAD)})
    for p, r in zip(rngs, rngs[1:]):
        if r["start"] < p["end"]:
            r["start"] = p["end"]
    return rngs


def map_out(t, rngs):
    off = 0.0
    for r in rngs:
        if t < r["start"]:
            return round(off, 3)
        if t <= r["end"]:
            return round(off + (t - r["start"]), 3)
        off += r["end"] - r["start"]
    return round(off, 3)


# --- the 12 clips ----------------------------------------------------------
C = [
 dict(id=1, sec="kv1", slug="kv-under-1pc-notice-ai",
      start="But we have",
      end="it's a robot maybe after 10 or 20 minutes of conversation",
      drop_phrases=[("Well, yeah, so that is", "if you know what makes something human")]),
 dict(id=2, sec="kv2", slug="kv-20-leads-to-100",
      start="I'll give you one stat",
      end="for the same amount of money, for the same deal",
      drop_phrases=[("You need more time and investment", "and now another stat")]),
 dict(id=3, sec="kv3", slug="kv-the-blank-ad",
      start="he even bought out",
      end="that some people really are tuned to",
      drop_phrases=[]),
 dict(id=4, sec="kv4", slug="kv-the-day-chatgpt-came-out",
      start="that is literally the day that ChatGPT came out",
      end="people could actually create an app in the App Store",
      drop_phrases=[("And I thought", "I'll make it specifically useful")]),
 dict(id=5, sec="kv5a", slug="kv-couldnt-afford-the-desk",
      start="And honestly, I couldn't pay it that month",
      end="If we don't get opportunities out of it, you can go",
      drop_phrases=[("Why is it so important", "because I wouldn't have gone"),
                    ("I can sit on the floor", "I don't need the good Wi-Fi. It doesn't matter")],
      join=[dict(sec="kv5b", start="and then you met a guy who changed your life",
                 end="we plan to sell out $25 million in one day",
                 drop_phrases=[("Absolutely. Yeah.", "All right.")])]),
 dict(id=6, sec="kv6", slug="kv-dont-invest-under-a-million",
      start="my current assumption is this",
      end="real estate is great",
      drop_phrases=[]),
 dict(id=7, sec="kv7", slug="kv-give-away-the-scalable",
      start="I've been giving courses away for free",
      end="you charge for the non-scalable",
      drop_words={"hormozi"},
      drop_phrases=[("Can I have it, too", "Very nice.")]),
 dict(id=8, sec="ml1", slug="ml-the-ghana-scriptwriter",
      start="I speak with a lot of freelancers from the Netherlands",
      end="I get goosebumps",
      drop_phrases=[("You think that", "which they can use")]),
 dict(id=9, sec="ml2", slug="ml-follow-your-passion",
      start="I wanna start a whole channel about CRMs",
      end="what the audience wants to see",
      drop_phrases=[("Oh, yeah, I want to sell this product", "if there is demand for it")]),
 dict(id=10, sec="ml3", slug="ml-he-rented-a-prison",
      start="I found out about the business model",
      end="I was, \"Okay, I'm doing the right thing\"",
      drop_phrases=[("we call it in Dutch anti-crack", "Never mind, but it was"),
                    ("I didn't went to parties", "Nothing"),
                    ("How old? What age", "Yeah, three years ago was it"),
                    ("When you saw your what", "When you saw your results, you said")]),
 dict(id=11, sec="ml4", slug="ml-60-freelancers",
      start="if you got more than 60 freelancers",
      end="I think like 60, 65",
      join=[dict(sec="ml4", start="that also means that your structure needs to be good",
                 end="So structures and work processes",
                 drop_phrases=[("it's gonna be a big mess", "that's with every business")]),
            dict(sec="ml4", start="Hire a leader",
                 end="Yeah, it's full-time",
                 drop_phrases=[("but he does extra jobs as well", "he's fixing an edit")])]),
 dict(id=12, sec="ml5", slug="ml-could-l-ever-catch",
      start="there was a channel",
      end="outperforming all his other videos",
      drop_phrases=[("well, don't", "Something in that area")],
      join=[dict(sec="ml5", start="So I took it out and I saw like",
                 end="repeatedly make a video about that format",
                 drop_phrases=[("Could L ever catch, well, name it", "I can like")])]),
]

SRC = {c["id"]: c["sec"] for c in C}

plan = []
print("=" * 74)
for c in C:
    pool = load(c["sec"])
    a = find_anchor(pool, c["start"], "start")
    b = find_anchor(pool, c["end"], "end")
    drops = c.get("drops", []) + resolve_drops(pool, c.get("drop_phrases"))
    kept = clean(pool, a, b, drops, c.get("drop_words", set()))
    parts = [{"sec": c["sec"], "words": kept}]
    for j in c.get("join", []):
        p2 = load(j["sec"])
        a2 = find_anchor(p2, j["start"], "start")
        b2 = find_anchor(p2, j["end"], "end")
        d2 = resolve_drops(p2, j.get("drop_phrases"))
        parts.append({"sec": j["sec"], "words": clean(p2, a2, b2, d2, set())})
    segs = []
    capwords = []
    off = 0.0
    trans = []
    for p in parts:
        rngs = build_ranges(p["words"])
        for w in p["words"]:
            capwords.append({"t": round(off + map_out(w["start"], rngs), 3),
                             "e": round(off + map_out(w["end"], rngs), 3),
                             "text": w["text"]})
        segs += [{"sec": p["sec"], "start": round(r["start"], 3), "end": round(r["end"], 3),
                  "side": dominant_side(p["sec"], p["words"], r["start"], r["end"])}
                 for r in rngs]
        off += sum(r["end"] - r["start"] for r in rngs)
        trans.append(" ".join(w["text"] for w in p["words"]))
    out_dur = round(off, 2)
    transcript = re.sub(r"\s+([,.\?!])", r"\1", " ".join(trans))
    plan.append(dict(id=c["id"], slug=c["slug"], sec=c["sec"], ranges=segs,
                     out_dur=out_dur, capwords=capwords, transcript=transcript))
    print(f"#{c['id']:>2} {c['slug']:<28} {out_dur:5.1f}s  {len(segs)} cuts")
    print(f"    {transcript}")
    print("-" * 74)

json.dump(plan, open(os.path.join(HERE, "plan.json"), "w"), indent=1)
print(f"\nTotal {sum(p['out_dur'] for p in plan):.0f}s over {len(plan)} clips -> plan.json")
