---
name: sam-clips-engine
description: End-to-end clips engine for Sam Eye Am (@sameyeam.secrets). Takes a long-form Sam interview/podcast (file or YouTube URL) and ships finished 30-45s vertical clips ready to upload — viral moment selection, precision cuts via Scribe word-level transcripts, Sam-brand b-roll from the brand library, Hormozi-style word-by-word captions, and ElevenLabs music (per-clip bespoke, library fallback). Use this skill whenever the user mentions Sam Eye Am, Sam Ey Am, @sameyeam, @sameyeam.secrets, clipping a Sam interview/podcast/long-form, or processing a Sam video to Shorts/Reels. Triggers on phrases like "clip this sam interview", "sam shorts from this video", "build sam clips", "process sam's podcast", "cut this for sam", "sam ey am pipeline", and any variant mentioning Sam + shorts/clips/reels/cuts. Even if the user just hands a video file or URL and mentions Sam, use this skill — it knows the full pipeline.
---

# Sam Clips Engine

End-to-end clips engine for Sam Eye Am. Takes a long-form video → ships finished 1080×1920 .mp4 clips ready to upload.

## What this is and isn't

This skill **wraps** [video-use](../video-use/SKILL.md) with Sam-specific defaults. video-use is the cutting engine — Scribe transcription, waveform-aware cuts, EDL → render.py with proper hard-rule compliance (subtitles last, per-segment extract, 30ms fades, etc). You should compose with it, not duplicate it.

What this skill adds on top:
1. **Viral moment ranker** tuned for Sam's audience (coaches, consultants, AI-curious operators)
2. **B-roll picker** that scans the clip transcript and pulls assets from Sam's brand library
3. **Hormozi-style captions** matching the exact style of the 14 viral shorts already published
4. **Music** — ElevenLabs first per-clip bespoke, falls back to Sam's 4-track music library

The music-mixed clip is the final deliverable — **no end card** (Sam doesn't want one).

Sam will use this directly. Keep all paths Sam-relative — never reference Harry / HV / Gcore / Lownie / Evacuees.

## Prerequisites

- **video-use** skill installed at `~/.claude/skills/video-use/` (foundation, do NOT duplicate)
- **ELEVENLABS_API_KEY** in env or `.env` at the video-use repo root (Scribe transcription + music generation)
- **ffmpeg + ffprobe** on PATH
- **yt-dlp** if ingesting from YouTube URL
- Sam's assets present at:
  - `/Volumes/Seagate/YouTube/Sam Ey Am/brand_library/` — manifest.json, concepts/, logos/, people/, build scripts
  - `music/` — 4 fallback music tracks

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
- **Hook strength** — first 3 words pull the viewer (specific number, contrarian claim, "I lost", "$30K in 2 days", "everyone tells you")
- **Self-contained payoff** — clip resolves without needing context from the rest of the interview
- **Specific claims** — concrete dollar amounts, dates, names, places, mechanisms (NOT abstractions like "mindset" or "value")
- **CTA opportunity** — moment leaves room for a "comment X" or "follow @sameyeam.secrets" at the end
- **Brand match** — content is about coaching / clients / AI systems / pricing / content / Sam's actual lanes (NOT off-topic personal stuff)
- **Audience fit** — coaches and consultants ages 25-45 are the target; clip lands for that demographic

Sam's audience is knowledge workers escaping drudge work — small business owners scaling with AI, consultants raising prices, content creators monetising audiences. NOT founders, NOT devs, NOT AI Twitter.

Output: `ranked_clips.json` — list of `{id, start, end, score, beat, hook_preview, reason}` where `id` references back into `candidates.json`.

Default: pick top 12 candidates. User can ask for more/fewer.

**See `references/sam_audience.md` for the full audience profile plus the patterns the 14 already-shipped viral clips had in common.**

### Step 3 — Precision cut (use video-use directly)

For each picked moment:
- Snap start/end to word boundaries from the Scribe transcript (Hard Rule 6)
- Pad: 50ms before first kept word, 80ms after last (video-use default, matches the 14 shipped Sam shorts)
- Build single-range EDL JSON per clip with the **Sam color grade** baked in (see below)
- `render.py --preview` initially; full render after self-eval passes

Sam's shorts are tight: strip pauses ≥ 400ms within the clip via additional internal cuts in the EDL ranges. video-use's editor sub-agent brief in SKILL.md covers this — invoke it via the editor pattern. Do NOT bypass video-use's cutting helpers.

**Sam color grade** (locked from the 14 shipped shorts — same look across every clip):
```
curves=red='0/0 0.5/0.53 1/1':blue='0/0 0.5/0.45 1/1',eq=saturation=0.95:contrast=1.03:brightness=0.01
```
This is a subtle warmth lift (red mids +6%, blue mids -10%) + slight contrast/saturation tweak. It matches the long-form interview look and works on any of Sam's likely shoot locations (studio, villa, hotel room, outdoor). One grade for every clip — don't alternate by section, don't pick different grades for different beats. Consistency beats cleverness.

### Step 4 — B-roll overlay picker (Sam brand library)

Run `helpers/pick_broll.py <clip_transcript.json>` to scan the clip's words and propose b-roll overlays.

**Trigger logic** (consult `/Volumes/Seagate/YouTube/Sam Ey Am/brand_library/manifest.json`):

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
Font:        Montserrat-Black at 140pt
Position:    centred horizontally, y = 0.62 * H
Style:       White fill (#FFFFFF) + 8px black stroke (Hormozi-style)
Trigger:     One word per caption, on key beats (NOT every word)
Window:      1.5s per word with 0.15s pop-in + 0.15s pop-out via alpha fade
Rendering:   PIL → PNG overlay → ffmpeg overlay filter (drawtext is unreliable on macOS Homebrew ffmpeg)
```

The caption picker reads the clip transcript and chooses which words to emphasise. Default heuristic:
- Numbers (`$30K`, `150`, `4K`, `500K`)
- Brand/person names (`STRIPE`, `WILLIAM`, `HORMOZI`)
- Imperative verbs at the start of a clause (`STOP`, `DON'T`, `LEARN`)
- The hook's first 3 words
- The payoff's last word

Aim for **8–14 emphasised words per 30-45s clip** — sparse enough to land, dense enough to drive engagement.

### Step 6 — Music

**Music** (`helpers/pick_music.py`):
1. Default: ElevenLabs music generation, one bespoke track per clip
   - Classify clip mood from transcript (proof / origin / contrarian / how-to / case-study)
   - Generate via ElevenLabs HTTP API at `api.elevenlabs.io/v1/music`
   - Universal prompt rules: `no vocals, no prominent drums, sits under YouTube VO, lofi production polish`
   - Mood -> prompt seed mapping in `references/music_prompts.md`
2. Fallback: if quota tight or ElevenLabs fails, pull from the `music/` library:
   - `Show the How 2.mp3` - confident / proof / tutorial
   - `Show the How Suno.mp3` - same vibe, alternate
   - `Varation 1 strings.mp3` - emotive / origin / story
   - `Varation 2 strings.mp3` - emotive / restrained
3. Mix at **-16dB** under Sam's voice (matches build_short.py default)

The music-mixed clip IS the final output - it's copied straight to `finished/`. **No end card** (Sam doesn't want one).

## End-to-end orchestration

`orchestrator.py` is the entry point. It runs all 6 steps:

```bash
python3 -m sam_clips_engine.orchestrator \
  --input "/path/to/sam_podcast.mp4" \
  --work-dir "/Volumes/Seagate/YouTube/Sam Ey Am/Shorts/<topic>" \
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
11. **No end card** — Sam doesn't want one; the music-mixed clip is the final output
12. **Music at -16dB under voice** — never louder, never absent

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
├── brand_assets.json              ← paths to brand_library, music
├── orchestrator.py                ← entry point — runs the 6 steps
├── helpers/
│   ├── pick_moments.py            ← Step 2: viral moment ranker
│   ├── pick_broll.py              ← Step 4: brand-library b-roll picker
│   ├── burn_captions.py           ← Step 5: Sam Hormozi caption overlays
│   └── pick_music.py              ← Step 6: ElevenLabs + library fallback
├── references/
│   ├── sam_audience.md            ← Who Sam's audience is + viral hook patterns + what the 14 shipped shorts had in common
│   ├── brand_library.md           ← Asset catalogue + picker logic + how to add new
│   └── music_prompts.md           ← ElevenLabs mood → prompt seed mapping
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
- **Adding an end card** — Sam doesn't want one. The music-mixed clip is the final output.
- **Re-transcribing every run** — Scribe transcripts cache. Reuse them. Don't burn ElevenLabs quota.
