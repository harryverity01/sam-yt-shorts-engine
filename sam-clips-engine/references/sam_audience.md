# Sam's Audience Profile

Used by `pick_moments.py` to score viral candidates.

## Who they are

- **Coaches, consultants, photographers, knowledge workers ages 25–45**
- Solo operators or small teams (1-5 people)
- Currently earning $40k–$200k/year, wanting to break $500k
- Tech-comfortable but NOT engineers — they want tools, not theory
- Active on Instagram + sometimes LinkedIn, rarely Twitter/X
- Bought at least one course or coaching program before
- English-speaking, mostly US/UK/AU/EU

## Who they are NOT

- Founders / startup people — Sam isn't a startup voice
- Engineers / devs — Sam doesn't teach code
- AI Twitter / Twitter influencer audience — different vibe entirely
- Enterprise CMOs / corporate strategy — too senior, wrong job
- "Manifestation" / pure mindset audience — Sam is mechanical, not woo

## What they want from a 30-45s Sam clip

1. **A specific number they can chase** — "$30K in 2 days", "150 calls from 1 post", "120K followers in 12 months"
2. **A mechanical why** — how the result was actually achieved (not "I just believed in myself")
3. **Permission to charge more** — Sam talks pricing constantly; that's the audience's #1 friction
4. **An immediate next step** — "comment AI", "follow me", "free course at sameyeam.info/course"
5. **Identity reinforcement** — they want to feel "I'm a serious operator who values my time"

## Hook patterns that land for this audience

| Pattern | Example |
|---|---|
| **Specific stat + timeframe** | "I made $30,000 in 2 days" |
| **Contrarian against industry truism** | "Stop posting reels every day" |
| **Insider revelation** | "Most photographers don't know this" |
| **Cost framing** | "This mistake cost me 5 years" |
| **Result with mechanism** | "150 leads from 1 post — here's how" |
| **Pricing reveal** | "I went from $400 to $4,000 a day" |
| **Free work paradox** | "Working for free 10x'd my prices" |

## Hooks that miss for this audience

- Generic motivation ("believe in yourself")
- Personal anecdotes without business connection
- Pure philosophy without mechanism
- Vague timeframes ("over the years…")
- Hedge language ("kind of", "I guess", "maybe")
- Topic drift to founder/startup/exit lingo

## Sam's recurring lanes (in priority order)

1. **Pricing** — going from low-ticket to high-ticket, why people charge what they charge
2. **Content systems** — how to make content that brings clients without 8 hours/day
3. **AI automation** — ChatGPT, Claude, ManyChat, automating DMs and lead-gen
4. **Client work** — getting better clients, raising rates, qualifying leads
5. **Photography business** — his original specialty, niche but high-engagement
6. **Personal brand** — how Sam built his own following
7. **Outsourcing** — VAs, editors, the "$5/hr editor" framing

A clip lands strongest when it sits clearly in one lane and resolves with a concrete claim.

## Script quality bar (apply when ranking AND when trimming a clip)

This is how Sam judges a cut. A clip only ships if it clears every line:

1. **Starts on the most interesting moment.** The first sentence is the strongest
   line in the window — the hook. If a stronger line sits 8s in, the clip should
   start there, not at the "natural" sentence start. Re-point `start` to the hook.
2. **Every single sentence is interesting.** No throat-clearing, no setup that
   doesn't pay off, no "so anyway", no "does that make sense". If a sentence isn't
   pulling its weight, cut it.
3. **No filler words.** "um", "like", "you know", "kind of", "I guess", "basically",
   "honestly" — the silence-strip removes dead air; these are removed at the word
   level by the editor flagging them.
4. **No repetition.** If Sam says the same idea twice, keep the sharper version.
5. **Builds to a payoff.** Every sentence should make the viewer want the next one,
   ending on the concrete result / punch / CTA.

### How to act on this when ranking (the handoff)

When you write `ranked_clips.json`, each clip may include an optional `cuts` field —
a list of `[start, end]` SOURCE-time ranges to **excise from inside the clip**
(filler sentences, a repeated point, a tangent). The cutter treats these exactly
like silences: it removes them and concatenates around them. Use it to make every
sentence land.

```json
{"id": 4, "start": 123.5, "end": 161.0, "score": 92, "beat": "STAT",
 "hook_preview": "I made thirty grand in two days",
 "cuts": [[140.2, 143.6]],
 "reason": "Strong stat hook + mechanism. Cut the 3s aside about his dog."}
```

Leave `cuts` out if the whole window is tight. Don't over-cut — the silence-strip
already removes pauses; `cuts` is only for whole filler/repeat sentences.

## Sam's spoken voice (style reference)

See `references/sam_voice.md` — a distilled profile of how Sam actually talks, built
from transcribing his voice memos. Read it when ranking so picks match the lines Sam
himself would find interesting (not generic "viral" lines). If that file is still a
stub, fall back to the hook patterns above.

## What the 14 viral shorts had in common

(Used as reference patterns for the ranker.)

1. **First-3-words hook** — specific number, contrarian claim, or visceral promise
2. **One mechanism per clip** — they don't try to teach three things
3. **Sam on camera ≥80% of runtime** — talking-head primary, b-roll secondary
4. **CTA at the end** — handle plug, free course, or DM trigger
5. **Tight cut** — pauses + filler words stripped, even mid-sentence
6. **30-45s total** — never under 25s, never over 50s
7. **One overlay every 8-15s** — keeps visual rhythm without crowding
