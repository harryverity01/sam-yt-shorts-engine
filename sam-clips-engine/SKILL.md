---
name: sam-clips-engine
description: End-to-end clips engine for Sam Eye Am (@sameyeam.secrets). Takes a long-form Sam interview/podcast (file or YouTube URL) and ships finished 30-45s vertical clips ready to upload — viral moment selection, precision cuts via Scribe word-level transcripts, REAL-screenshot edge-boil b-roll timed to the spoken word (plus recreated Instagram DM conversations for "AI in my DMs" clips), 2-word Bellefair captions on a black box (cut over the hook + b-roll), a music bed chosen per clip, and a Bellefair hook card for the Instagram cut. Cloud pipeline in cloud/ (see LOCKED DEFAULTS). Use this skill whenever the user mentions Sam Eye Am, Sam Ey Am, @sameyeam, @sameyeam.secrets, clipping a Sam interview/podcast/long-form, or processing a Sam video to Shorts/Reels. Triggers on phrases like "clip this sam interview", "sam shorts from this video", "build sam clips", "process sam's podcast", "cut this for sam", "sam ey am pipeline", and any variant mentioning Sam + shorts/clips/reels/cuts. Even if the user just hands a video file or URL and mentions Sam, use this skill — it knows the full pipeline.
---

# Sam Clips Engine

End-to-end clips engine for Sam Eye Am. Takes a long-form video → ships finished 1080×1920 .mp4 clips ready to upload.

## ⛔ LOCKED DEFAULTS — Sam feedback, 2026-06-27 + 2026-07-06 + 2026-07-07 (these OVERRIDE the steps below)

Sam reviewed a full batch (15 clips from the Danielle Lukins interview) and locked
these. Apply them **every run** — they win over any contradicting instruction below.

1. **MUSIC IS ON (reinstated 2026-08-29).** Every clip gets a bed. The old
   "no music" rule from 2026-06-27 is retired: the complaint then was that one
   flat bed ran across a whole batch and read as elevator music, not that music
   itself was wrong. The fix is per-clip selection, not silence. See rule 16 for
   how to pick and mix it.
2. **Captions = 2 words on a BLACK BOX in Bellefair (LOCKED 2026-07-07).** Two words per
   screen, white **Bellefair** serif on an **opaque black box**, centred low, timed to
   Sam's speech (`cloud/cap_bellefair.py` — boxed 2-word is the default; `plain`/`per1`
   only if ever needed). This **REPLACES** the old Archivo-Black yellow karaoke
   (`cap_ass.py`, retired): Sam found white-on-nothing clashed with the set and one word
   flashed too fast to read. **Cut the captions whenever they'd sit under the hook card or
   over ANY b-roll** — `cloud/composite2.py` + `cloud/ig_hook.py` suppress them
   automatically, so they only show over Sam's clean talking-head.
3. **REAL screenshots, never typeset/recreation cards.** Every b-roll beat is a REAL
   image: a real **news-article screenshot**, a real product/app page, the person's
   **actual photo**, or a real stock photo. NO made-up cards (no typeset headlines, stat
   cards, fake IG cards). To get a named person's face: **search Google → open a webpage
   that shows their photo → screenshot THAT page** (not the search-results page).
   - **Chromium can't navigate the cloud egress proxy** → real screenshots come from a
     server-side service (**microlink**, `cloud/mlshot.py`); Playwright is used only
     LOCALLY (`set_content`) to render cards, never to navigate.
4. **B-roll TIMED to the spoken word.** The visual must match what Sam is saying at that
   exact moment — verify every beat against the word-level transcript (show Gemini when
   he says "Gemini", Whisper when he says "Whisper"). Re-time beats to the trigger word.
5. **Yellow highlighter, not red circles.** Mark the key part of a screenshot with a
   translucent **yellow** highlight band (read the content through it). Red
   circles/underlines are obstructive — retired. **Photos get no annotation** (clean).
   - **NO red stamps, EVER** (rule 8 — this was a recurring habit).
6. **Bellefair hook ID card (Instagram version).** Each IG cut opens with a white
   **Bellefair** title card at the BOTTOM. **LOCKED 2026-08-04: the card is fully on
   screen from FRAME 0 — no slide-in, no fade-in. It transitions OUT only** (fade at
   ~2.5s). Viewers must be able to read the hook in the first frame. It
   must NOT cover Sam's face and must NOT clash with captions — **suppress the karaoke
   for the hook window** (`cloud/ig_hook.py`). 2 lines, statement-style.
7. **Process:** return the tight-hook clip IDEAS first for approval, then the as-cut
   transcripts; then cut EXACTLY to the approved transcript — hook first, every
   umm/err/false-start/repeat removed, silence-stripped, Sam-dominant.

**Added 2026-07-06 (Danielle batch review round 2):**

8. **NO red stamps — EVER.** The little red "NIGHTMARE / SCAM / C PLAYER" stamps Sam
   called out a *habit* of adding. They are **hard-disabled at the engine level**
   (`cloud/edgeboil.py` ignores any beat `stamp`). Do not re-enable them. The only marks
   on a b-roll beat are the **yellow highlight** + the handwritten **Caveat** label.
9. **Keep Sam CENTRED — re-dial the crop per clip.** A single fixed 2-shot crop drifts
   because Sam sits differently across a 2hr shoot (leans forward/right in some sections).
   Eyeball each clip against your best-framed clip; if he's off-centre or edging out of
   frame, add a per-clip crop override in `cloud/render_base.py` (`CROP_OVERRIDE={id:...}`,
   nudge the x-offset) so his face lands at the same spot every clip. Verify with a frame.
10. **End on a COMPLETE word/button, never a trailing fragment.** Don't let a clip end on
    a hanging "…to be—" even if the audio is technically whole; it reads as cut off.
    Extend the end anchor to the next complete beat (e.g. Sam's confirming "Yeah.") so the
    thought lands. Check the last kept word against the transcript before rendering.

**Added 2026-07-07 (Danielle batch review round 3):**

11. **"AI in my DMs" clips → RECREATE the DM conversation** (`cloud/dmphone.py`). A private
    DM can't be screenshotted, so this is the ONE sanctioned exception to rule 3. It renders
    a faithful dark-mode Instagram DM: Sam's **real face** as the avatar, real gradient
    bubbles, optional timestamps for a "timing" beat — with our marks on top (yellow
    highlight **outline** on the key bubble, since a highlighter band can't sit on a chat
    bubble). **NO fake iOS status bar** (the `9:41`/battery strip — Sam had it removed) and
    keep the handwritten labels OFF the DM beats (they read as clutter on a self-explanatory
    convo). `broll_plan2.py` has a `dm()` helper; `build()` routes dm beats to `dmphone`.

**Added 2026-08-28 (Karel + Melvin batch — the one Sam and Harry both signed off).
These rules made the difference. Apply them on every run:**

12. **ZERO generic stock. Ever.** A whole batch was rejected over one Pexels clip
    that was tagged "street festival crowd" and was actually a religious procession
    in Manila, used for a Netherlands King's Day line. Stock tags lie. Source every
    video beat down this ladder and stop at the first rung that works:
    1. **Sam's own R2 b-roll library** (2,000+ clips: phone, desks, poolside, villa
       networking, his real Lightroom screen recordings with face cam). Pull a frame
       from the DOWNLOADED file and look at it before the beat enters the plan. One
       key held completely different footage from what its name said.
    2. **The subject's own channel and website.** A guest's company gets THEIR
       vertical shorts (yt-dlp) and THEIR real pages. For site captures, use a tall
       viewport (h=3400) rather than fullPage, crop to the meaningful region, mount
       on the vox card and PAN inside it (`voxcard.py` shot beats take `croph`).
       Never start a capture on a decorative hero image: one company's homepage hero
       is a plant video, so the top of the page reads as random foliage.
    3. **A named real video of the named real thing.** Search the event by its own
       name (Koningsdag, not "crowd party") and pull that section.
    4. **A hand-drawn vox graphic** for abstract lines: `voxcard.py` kind `gfx` gives
       you `chart` (rising or falling), `cross` (supply and demand), `clock`,
       `funnel`, `stack`. Boiling ink and teal on cream paper, Caveat labels.
    If a page blocks the screenshot service, recreate it from its real fetched HTML
    with its real logo SVG pulled from the site's own markup (`hbr_page.py` is the
    worked example). Verbatim text only. Never invent a headline or a statistic.
13. **Landscape footage mounts on the vox paper** with a white border and soft
    shadow, sides trimmed to about 3:2. Never centre-crop landscape into 9:16; it
    cuts the subject in half. Portrait sources still fill the frame.
14. **The Bellefair hook card opens EVERY cut,** not only the Instagram one. The
    type auto-shrinks so a long line never clips.
15. **No annotations on a real source.** No marker sweeps, no source labels, no
    bands. The card itself is the design. A highlight inside a page you recreated
    is fine, because that is part of the page.
16. **One bed per clip, never one bed across a batch.** Pick the bed for what
    that clip has to do: money story gets something blunt, an underdog story
    gets a warm resolve, a joke beat gets the quietest bed so the joke carries.
    Mix it 16 dB under speech, 18 dB for the quietest beds, with speech
    normalised to -16 LUFS. `composite3.py` takes an explicit clip-to-bed map
    when you have made one, and otherwise rotates through the bundled library in
    `<repo>/music` by clip id, so consecutive clips never share a track. If a
    mapped bed is not on the machine it falls back to the library rather than
    failing the render.
17. **Look at a frame from EVERY beat before compositing,** as a contact sheet,
    then a 6-frame strip from every finished clip. This is what catches the wrong
    footage, a mislabelled file and a crop that drifted.
18. **Cut both speakers, guest-dominant, for interview clips** (`build_cut.py` and
    `render_base2.py`). Keep the guest on their own lines and drive the crop from
    whoever is speaking in each range.

## Which model runs this skill

- **A new batch from a fresh long-form: use Claude Fable.** Picking the moments,
  planning the beats, sourcing the assets and judging each beat is judgment work.
  That is where the quality comes from.
- **Revisions of an existing batch: Claude Opus is fine.** Re-cuts against an
  approved plan, swapping one beat, recompositing, re-uploading, metadata changes.
  The decisions are already made and Opus executes them at lower cost.
- The test: does this run CHOOSE anything, or only EXECUTE choices already made?

**The whole proven cloud pipeline is in `cloud/` — read `cloud/README.md` and reuse it.
Don't rebuild it.** (The Steps below + `helpers/` are the older local/video-use flow;
the LOCKED DEFAULTS + `cloud/` supersede them for caption style, music, and b-roll.)

## What this is and isn't

This skill **wraps** [video-use](../video-use/SKILL.md) with Sam-specific defaults. video-use is the cutting engine — Scribe transcription, waveform-aware cuts, EDL → render.py with proper hard-rule compliance (subtitles last, per-segment extract, 30ms fades, etc). You should compose with it, not duplicate it.

What this skill adds on top:
1. **Viral moment ranker** tuned for Sam's audience (coaches, consultants, AI-curious operators)
2. **B-roll picker** that scans the clip transcript and pulls assets from Sam's brand library
3. **Hormozi-style captions** matching the exact style of the 14 viral shorts already published
4. **Music** — Suno first (modern beds), then ElevenLabs, then Sam's 4-track library
5. **Silence-strip + re-listen cut** — tightens out dead air and verifies no word is clipped

Sam will use this directly. Keep all paths Sam-relative — never reference Harry / HV / Gcore / Lownie / Evacuees.

## Prerequisites

- **video-use** skill installed at `~/.claude/skills/video-use/` (foundation, do NOT duplicate)
- **ELEVENLABS_API_KEY** in env or `.env` at the video-use repo root (Scribe transcription + music generation)
- **ffmpeg + ffprobe** on PATH
- **yt-dlp** if ingesting from YouTube URL
- Sam's assets present at:
  - `<repo>/brand_library/` — manifest.json, concepts/, logos/, people/, build scripts
  - `<repo>/music/` — 4 fallback music tracks

Paths are read from `brand_assets.json` so Sam can override on his own machine.

**This skill runs inside Sam's Claude Code subscription. It does NOT call the Anthropic API directly.** The viral-moment ranking and any other LLM reasoning step is performed by Claude (the model running this skill in the session) — see Step 2 below for the handoff pattern.

## The pipeline (6 steps, in order)

The skill follows video-use's process but Sam-tunes each step. Each step has a helper script in `helpers/`.

### Step 1 — Ingest + transcribe

Input: file path OR YouTube URL.

- If URL, `yt-dlp` → `<work_dir>/source.mp4`
- `verify_sync.py source.mp4` — if drift > 1 frame, **stop** and tell user (Hard Rule from video-use)
- `transcribe.py source.mp4` — Scribe word-level, cached at `<work_dir>/transcripts/source.json`. Never re-transcribe if cached.
- `pack_transcripts.py --edit-dir <work_dir>` → `takes_packed.md` for the LLM to read at decision time

### Step 2 — Rank viral moments (CLAUDE-IN-SESSION, not an API call)

`helpers/pick_moments.py` **generates** candidate 30–45s windows. The ranking itself is done by Claude (the model running this skill in the user's Claude Code session) — NOT by an external API call.

**The handoff pattern:**

1. `pick_moments.py --transcript takes_packed.md -o candidates.json` writes every valid candidate window
2. The orchestrator detects no `ranked_clips.json` exists and prints a pause message
3. Claude (you, running this skill) reads `candidates.json` + the rubric in `references/sam_audience.md`, scores each candidate, picks top N, writes `ranked_clips.json`
4. The user re-runs the orchestrator — it picks up at `ranked_clips.json` and continues

This means the skill is portable across any Claude Code subscription with no API key setup, and the ranking quality scales with whatever model the user is on.

**The Sam viral rubric** (Claude follows this when scoring):

**Sam viral rubric** (the editor sub-agent brief uses this):
- **SAM-DOMINANT (non-negotiable)** — it's Sam's channel, so the clip must be **mostly Sam talking** (≥~80% of the words); a guest only interjects. Never ship a guest-monologue clip. When clipping an interview, identify Sam by **content, not the diarisation label** (Scribe speaker tags aren't consistent across a long/chunked file).
- **Hook strength** — first 3 words pull the viewer (specific number, contrarian claim, "I lost", "$30K in 2 days", "everyone tells you")
- **Self-contained payoff** — clip resolves without needing context from the rest of the interview
- **Specific claims** — concrete dollar amounts, dates, names, places, mechanisms (NOT abstractions like "mindset" or "value")
- **CTA opportunity** — moment leaves room for a "comment X" or "follow @sameyeam.secrets" at the end
- **Brand match** — content is about coaching / clients / AI systems / pricing / content / Sam's actual lanes (NOT off-topic personal stuff)
- **Audience fit** — coaches and consultants ages 25-45 are the target; clip lands for that demographic

Sam's audience is knowledge workers escaping drudge work — small business owners scaling with AI, consultants raising prices, content creators monetising audiences. NOT founders, NOT devs, NOT AI Twitter.

Output: `ranked_clips.json` — list of `{id, start, end, score, beat, hook_preview, reason}` where `id` references back into `candidates.json`. Each clip may also carry an optional **`cuts`** field — `[[start, end], ...]` source-time ranges to excise from inside the clip (filler/repeat sentences). Re-point `start` to the strongest line so the clip **opens on the hook**.

Apply the **Script quality bar** in `references/sam_audience.md` — starts on the most
interesting moment, every sentence interesting, no filler, no repetition, builds to a
payoff. That's exactly how Sam judges a cut.

Default: pick top 12 candidates. User can ask for more/fewer.

**See `references/sam_audience.md` for the audience profile + script quality bar, and `references/sam_viral_patterns.md` for the 14 already-shipped viral clip patterns to match.**

### Step 3 — Precision cut (silence-stripped + word-snapped + re-listened)

This is the step Sam gave feedback on: clips were **cutting mid-word / not fully
understandable / elevator-paced**. The root cause was that the old orchestrator built
a *single* EDL range per clip — it never actually stripped the silences the way Sam
does by hand. It does now.

How Sam cuts by hand (and what the code now replicates):
> "I look at the audio, I cut every word out that I see — every time it's silent I
> cut it out. Then I listen again to make sure all the words are recognisable."

`helpers/tighten_cut.py` does the first half:
- Selects the words inside the window from the **word-level Scribe transcript** and
  snaps the clip to whole-word boundaries (never mid-word) — start on the first word,
  end on the last word.
- Removes every internal silence longer than `--max-gap` (default **0.28s**) by
  splitting the clip into a **multi-range EDL** (one range per run of words). `render.py`
  extracts each range with the Sam grade + 30ms fades and **losslessly concatenates**
  them — so the result is tight but pop-free. Natural sub-0.28s gaps are kept so it
  still breathes (not robotic).
- Holds a larger tail pad on the **final word** (default 0.18s) so the payoff is
  never clipped — Sam's #1 complaint.
- Honors an optional `cuts` field on the ranked clip to excise whole filler/repeat
  sentences from inside the clip (see `references/sam_audience.md`).

`helpers/verify_cut.py` does the re-listen half (Sam's "extra protection"):
- Re-transcribes the rendered cut with Scribe and checks the first/last words are
  present and the final word isn't flush against the clip end (= clipped).
- If the end looks clipped, the orchestrator re-cuts **once** with a longer end tail,
  capped at +0.3s so it can never bleed the next sentence in (Sam's worry: "does it
  make it a mess?"). Still flagged after the retry → left for manual review, not shipped silently.
- Skippable with `--no-verify` (faster, costs no extra Scribe). On by default.

Because silence removal **compresses the timeline**, the orchestrator remaps every
caption and b-roll timing through `tighten_cut.map_src_to_out()` so they stay in sync.

**Sam color grade** (locked from the 14 shipped shorts — one grade baked per-segment by `render.py`):
```
curves=red='0/0 0.5/0.53 1/1':blue='0/0 0.5/0.45 1/1',eq=saturation=0.95:contrast=1.03:brightness=0.01
```
This is a subtle warmth lift (red mids +6%, blue mids -10%) + slight contrast/saturation tweak. It matches the long-form interview look and works on any of Sam's likely shoot locations (studio, villa, hotel room, outdoor). One grade for every clip — don't alternate by section, don't pick different grades for different beats. Consistency beats cleverness.

### Step 4 — B-roll overlay picker (Sam brand library)

Run `helpers/pick_broll.py <clip_transcript.json>` to scan the clip's words and propose b-roll overlays.

**Trigger logic** (consult `<repo>/brand_library/manifest.json`):

| Trigger phrase in transcript | Overlay |
|---|---|
| "William Brown" / "Will Brown" | IG popup of his profile OR wide villa shot — pick by clip energy (animated card for stat-heavy lines, villa shot for relaxed lines) |
| "comment X" / "DM me X" CTA | IG comment highlight asset, parameterised with the actual word Sam said |
| "calendly" / "fully booked" / "150 calls" / "my calls" | sam_calendly_fully_booked.mov |
| Named brand (Stripe, Hilton, Tommy, Hugo Boss, etc.) | Logo from `brand_library/logos/<brand>_com_logo.png` |
| Person name (Hormozi, Naval, Rockefeller, Tony Robbins, etc.) | Photo from `brand_library/people/` |
| End-of-clip (last 2s) | `handle_sameyeam_secrets.mov` lower-third |

Cadence target: **one overlay every 8–15 seconds** (matches the 14 viral shorts). Stack the picks into an `overlays[]` array in the per-clip EDL.

If a trigger fires but no matching asset exists in the brand library, **DO NOT INVENT ONE** — flag it to the user and ask if they want to skip or build a new template (real-reference-first methodology — see `references/brand_library.md`).

**See `references/brand_library.md` for the full picker logic, asset catalogue, and the rules for adding NEW templates.**

### Step 5 — Captions (Sam Hormozi style)

Sam's caption style is locked from the 14 viral shorts. Source-of-truth: `helpers/burn_captions.py` (replicates `build_short.py` exactly).

```
Font:        caption_black from brand_assets.json at 140pt
Position:    centred horizontally, y = 0.62 * H
Style:       White fill (#FFFFFF) + 8px black stroke (Hormozi-style)
Trigger:     One word per caption, on key beats (NOT every word)
Window:      1.5s per word with 0.15s pop-in + 0.15s pop-out via alpha fade
Rendering:   PIL → PNG overlay → ffmpeg overlay filter (drawtext is unreliable on macOS Homebrew ffmpeg)
```

> **Font swap (Sam's feedback):** Sam said the captions "are not my fonts / not my
> style" and sent a new set. `burn_captions.py` reads the font from
> `brand_assets.json` → `fonts.caption_black` — so the swap is a one-line config
> change once the new font files are dropped in `_assets/fonts/`. Montserrat-Black is
> the OLD default he rejected. Point `caption_black` at the heaviest weight of the new
> family. (The geometry — 140pt, 8px stroke, y=0.62 — stays; only the typeface changes
> unless Sam wants the size/weight retuned for the new font's metrics.)

The caption picker reads the clip transcript and chooses which words to emphasise. Default heuristic:
- Numbers (`$30K`, `150`, `4K`, `500K`)
- Brand/person names (`STRIPE`, `WILLIAM`, `HORMOZI`)
- Imperative verbs at the start of a clause (`STOP`, `DON'T`, `LEARN`)
- The hook's first 3 words
- The payoff's last word

Aim for **8–14 emphasised words per 30-45s clip** — sparse enough to land, dense enough to drive engagement.

### Step 6 — Music (final step)

> **No end card.** Sam asked for the Subscribe end card to be removed — clips end on
> the payoff. The final clip is just the music-mixed cut; nothing is appended.

**Music** (`helpers/pick_music.py`) — Sam said the old beds sounded like **elevator
music**. Two fixes: (a) prompts are now modern/motivational with a subtle beat (not
corporate-ambient), and (b) **Suno** is the preferred generator. Provider order:
1. **Suno** (default when `SUNO_API_KEY` is set) — produced, modern beds.
   - Classify clip mood (proof / origin / contrarian / how-to / case-study)
   - Generate via the configured Suno provider (sunoapi.org v1 shape by default),
     poll, download, trim to length. See `references/music_prompts.md` for setup.
2. **ElevenLabs** — bespoke per-clip if Suno isn't configured or fails (`api.elevenlabs.io/v1/music`).
3. Fallback: if both gen paths fail, pull from `<repo>/music/`:
   - `Show the How 2.mp3` — confident / proof / tutorial
   - `Show the How Suno.mp3` — same vibe, alternate
   - `Varation 1 strings.mp3` — emotive / origin / story
   - `Varation 2 strings.mp3` — emotive / restrained
4. Mix at **-16dB** under Sam's voice (matches build_short.py default), faded over the
   tightened clip length.

## End-to-end orchestration

`orchestrator.py` is the entry point. It runs all 6 steps:

```bash
python3 -m sam_clips_engine.orchestrator \
  --input "/path/to/sam_podcast.mp4" \
  --work-dir "<your working folder>/<topic>" \
  --num-clips 12 \
  --target-length 35
```

For YouTube URL: `--input "https://youtube.com/watch?v=..."`.

The orchestrator:
1. Calls each helper in sequence
2. Spawns parallel sub-agents per clip for steps 3–5 (cut, b-roll, captions are independent across clips)
3. Reports progress + a summary CSV with `clip_id, runtime, hook_preview, beat, overlays_used`
4. Outputs N finished `.mp4` files to `<work_dir>/finished/`

Output naming: `01_<short_slug>.mp4`, `02_<short_slug>.mp4`, etc.

## Hard rules (inherited from video-use — non-negotiable)

These come from video-use SKILL.md. Read its full Hard Rules section, but the highlights:

1. **Subtitles LAST** in the filter chain — overlays first, captions last
2. **Per-segment extract → lossless concat** — never single-pass filtergraph when overlays present
3. **30ms audio fades** at every segment boundary — prevents pops
4. **Overlays use `setpts=PTS-STARTPTS+T/TB`** — shifts overlay frame 0 to window start
5. **Snap cuts to word boundaries** from Scribe transcript — never mid-word
6. **Pad every cut edge** — 50ms front / 80ms back default
7. **Word-level Scribe only** — never Whisper, never SRT/phrase mode
8. **Cache transcripts** — never re-transcribe a source

Sam-specific additions:
9. **Reference-first for new b-roll templates** — never invent a UI element; capture the real thing first (see `references/brand_library.md`)
10. **One overlay per 8-15s** in the body — matches the 14 viral shorts' established cadence
11. **No end card** — Sam removed it. Clips end on the payoff; nothing is appended.
12. **Music at -16dB under voice** — never louder, never absent
13. **Silence-strip every clip** — multi-range EDL via `tighten_cut.py`. Never ship a single-range cut full of dead air (that was the old bug). Snap to whole words; never cut mid-word.
14. **Re-listen with Scribe** — `verify_cut.py` confirms the last word isn't clipped. Conservative single retry (+0.3s tail max) so it never bleeds the next sentence in. Don't disable verify on the final pass.
15. **Remap timings after silence removal** — captions/overlays are computed in source time, then remapped to the compressed output timeline. Never burn source-time captions onto a tightened clip.

## Adding new brand templates

The brand library has 3 active templates: `sam_ig_popup`, `handle_sameyeam_secrets`, `sam_calendly_fully_booked`. Each was built from a **real reference screenshot** of the actual UI being mimicked. This is the discipline.

To add a new template (e.g., Stripe payment notification):
1. Get a real reference — screenshot of the actual app/UI in question (Sam's own Stripe push, ManyChat dashboard, etc.). Headless Playwright pulls public pages cleanly.
2. Sample exact colours from the screenshot via PIL `getpixel()`
3. Identify the platform's actual font (Helvetica/SF Pro for iOS, Inter for web tools, etc.) — **NOT Sam's brand fonts** (Bellefair/Montserrat are for Sam-branded wrap assets only)
4. Build a parameterised renderer following the `build_ig_popup.py` / `build_sam_calendly.py` patterns in `brand_library/`
5. Add to `brand_library/manifest.json` with trigger phrases
6. Document the reference source in the manifest entry

**Never invent UI from memory** — the 39 rejected concepts in `brand_library/_rejected/` were all built that way and none of them worked.

## Files in this skill

```
sam-clips-engine/
├── SKILL.md                       ← this file
├── brand_assets.json              ← paths to brand_library, music, fonts + cut/music config
├── orchestrator.py                ← entry point — runs the 6 steps
├── helpers/
│   ├── pick_moments.py            ← Step 2: viral moment candidate generator
│   ├── tighten_cut.py             ← Step 3: silence-strip + word-snap → multi-range EDL + time remap
│   ├── verify_cut.py              ← Step 3: re-transcribe end-protection (Sam's re-listen)
│   ├── pick_broll.py              ← Step 4: brand-library b-roll picker
│   ├── pick_caption_words.py      ← Step 5: choose which words to emphasise
│   ├── burn_captions.py           ← Step 5: Sam Hormozi caption overlays
│   └── pick_music.py              ← Step 6: Suno → ElevenLabs → library (final step, no end card)
├── references/
│   ├── sam_audience.md            ← Audience + hook patterns + script quality bar + cuts field
│   ├── sam_viral_patterns.md      ← The 14 shipped shorts — what worked
│   ├── brand_library.md           ← Asset catalogue + picker logic + how to add new
│   └── music_prompts.md           ← Suno/ElevenLabs mood → prompt seed mapping
└── scripts/
    └── install.sh                 ← One-shot install (deps + paths check)
```

## Memory + persistence

Like video-use, this skill writes a `project.md` to the work-dir each session. Sam can read it to see what was decided and why.

Append the standard video-use session entry plus a Sam-specific block:
```markdown
## Session N — YYYY-MM-DD
**Source:** <input file/URL>
**Clips shipped:** N (top N from M candidates)
**Total runtime saved:** X minutes (source) → Y minutes (clips total)
**B-roll usage:** which templates fired (frequency)
**Music:** ElevenLabs (N) | Library (N) | breakdown
**Outstanding:** flagged moments worth a manual look
```

## When NOT to use this skill

- **Single-clip surgical edits.** Use video-use directly. This skill's overhead is the 6-step pipeline; for a one-off cut, that's wasted.
- **Non-Sam content.** This is Sam-tuned (audience, captions, brand). For Harry Verity reels, use `hv-instagram-reels`. For Lownie Clips, use the precision-shorts-cutter family.
- **Long-form (3min+).** This ships 30-45s vertical. For long-form compilations, use `lownie-long-form` or `anthropic-skills:precision-longform-cutter`.

## Anti-patterns specific to Sam

- **Inventing brand library assets** — see Rule 9 above
- **Using Anton or Hormozi-orange in captions** — Sam's brand captions are white + black stroke (matches Hormozi-style but on Sam's content). Anton was the OLD experiment that got rejected.
- **Multi-word captions** — Sam's emphasis style is single-word pop. Multi-word captions break the rhythm.
- **Music louder than -16dB** — already tested; voice loses presence above that
- **Adding an end card** — Sam removed it. Don't re-add a Subscribe/outro card.
- **Cutting on silence-strip too hard** — `--max-gap` too low makes Sam sound robotic. 0.28s keeps natural breath; only go lower if he asks for tighter.
- **Re-transcribing the SOURCE every run** — the source Scribe transcript caches; reuse it. (The short per-clip re-listen in verify_cut is separate and cheap — that's fine to run.)
