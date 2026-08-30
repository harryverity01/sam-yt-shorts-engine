# Sam Clips Engine — cloud pipeline (proven 2026-06-27)

This is the **working cloud implementation** used to ship the 15-clip Danielle Lukins
batch. It runs entirely in a cloud Claude Code session (no Seagate, no local
`video-use`). Copy `cloud/*.py` into a per-job work dir, edit the two per-interview
config scripts, and run in order. **Reuse this — don't rebuild it.**

## Why cloud differs from the local skill
- **No Seagate / no `video-use`** — the cut + reframe + grade are done directly with
  ffmpeg (`render_base.py`). Captions/b-roll/composite are bespoke (below).
- **ffmpeg** via `pip install imageio-ffmpeg` (no system ffmpeg). `imageio_ffmpeg.get_ffmpeg_exe()`.
- **Chromium CANNOT navigate the egress proxy** (`ERR_CONNECTION_CLOSED`). So:
  - Real screenshots come from a **server-side screenshot service** — microlink
    (`mlshot.py`). `curl`/`requests` work; the browser does not.
  - Playwright is used ONLY **locally** (`page.set_content`) to render the edge-boil
    cards — never to navigate to a URL.
- **Secrets** via Infisical universal-auth (`r2_helper.py`): project
  `7ba7c8cc-b283-4830-bd04-2d94f48377c1`, env `dev` — keys `R2_*`,
  `ELEVENLABS_API_KEY`, `BRANDFETCH_API_KEY`, `PEXELS_API_KEY`, `TELEGRAM_*`.
- **Assets** (source video, music, finished clips) live in R2 bucket `verity-video`.

## Flow (run in this order from the work dir)
1. **`r2_helper.py`** — `load_r2_env()` pulls creds from Infisical; `r2_client()`,
   `list_all(prefix)`. Source interview is on R2 under `Sam Ey/…`.
2. **`transcribe.py`** — extract mono 16k mp3, then ElevenLabs Scribe **word-level,
   diarized, in ONE call** (so `speaker_*` labels stay consistent). → `source.words.json`.
   **Identify Sam by CONTENT, not the speaker label.** Build "Sam-dominant windows"
   (Sam ≥75% of words, short guest interjections allowed) → pick tight-hook ideas →
   **come back to the user with the ideas first**, then the as-cut transcripts, for approval.
3. **`cut_build.py`** *(per-interview)* — for each approved clip: `start`/`end` phrase
   anchors (+ optional drop ranges, keep-guest ranges, stitched keep-spans) → a faithful
   EDL: Sam-only, umms/false-starts/repeats stripped, silence-stripped to whole-word
   runs. Writes `plan.json` (ranges + every kept word's OUT-time, used for caption sync).
4. **`render_base.py`** — per-segment **input-seek** extract (fast) → vertical reframe
   (crop on the speaker; for a locked 2-shot it's a fixed crop) + Sam grade + 30ms audio
   fades → lossless concat → `bases/base_NN.mp4`.
5. **Assets** — `source_assets.py` (Brandfetch logos + Pexels stock) and `mlshot.py`
   (microlink REAL screenshots: news articles, product/app pages, the person's actual
   photo). To get a named person's face: search Google → open a page that shows their
   photo → screenshot THAT page. Crop each screenshot to its key region (`*_crop.png`).
6. **`broll_plan2.py` + `edgeboil.py`** *(plan is per-interview)* — define 2–3 beats per
   clip, each a REAL photo or REAL screenshot, **timed to the spoken word** (use the word
   out-times from `plan.json`). `edgeboil.py` renders each beat as a kraft card with a
   "boil" jitter, **translucent yellow highlighter** over the key part (NOT a red circle),
   handwritten Caveat label, optional stamp, grain/vignette. Renders via Playwright
   `set_content`, JPEG frames, ONE browser for all beats (fast). → `broll/NN/spec.json`.
   - **"AI in my DMs" clips:** recreate the DM conversation with `dmphone.py` (dark IG DM,
     Sam's real avatar) instead of a screenshot — the one sanctioned exception to "real only".
7. **`cap_bellefair.py`** — captions: **2 words per screen, white Bellefair on an opaque
   BLACK BOX**, centred low, timed to Sam's speech (boxed 2-word = the default). →
   `caps/NN/bellefair.ass`. (`cap_ass.py` = the retired Archivo-Black yellow karaoke.)
8. **`composite2.py`** — base → b-roll overlays (under) → caption ASS (**last**), with
   captions **cut wherever they'd sit over b-roll or a DM** (they only show over Sam's
   talking-head). **Sam voice only, NO music**. → `finals/NN_*.mp4`.
9. **`ig_hook.py` / `ig_batch.py`** *(hook lines per-interview)* — Bellefair title card
   that slides up at the BOTTOM for ~2.2s (captions suppressed underneath + over b-roll;
   clear of the face); then captions + b-roll resume. → `finals_ig/NN_*_ig.mp4`.
10. **Deliver** — upload to R2 `sam-clip-tests/<source>/...`; send to the user
    (SendUserFile / Telegram `chat_id 1861792172`).

## Locked look specs
- **Reframe** (locked 2-shot, Sam on the left): `crop=540:960:96:40,scale=1080:1920`
  (re-dial per shoot — extract a frame and eyeball). **Sam drifts across a 2hr shoot**, so
  `render_base.py` has a per-clip `CROP_OVERRIDE={id:"crop=..."}` — if he's off-centre or
  edging out of frame on a clip, nudge that clip's x-offset (↑x moves him left) to match
  your best-framed clip, and verify with a frame. (Danielle #11 needed x 96→135.)
- **NO red stamps.** `edgeboil.py` hard-ignores any beat `stamp` (Sam's locked rule) — a
  beat's only marks are the yellow highlight + Caveat label.
- **End on a complete word/button.** Extend a clip's end anchor past a trailing fragment
  (e.g. "…right to be—") to the next whole beat (Sam's "Yeah.") so it doesn't read as cut off.
- **Sam grade:** `curves=red='0/0 0.5/0.53 1/1':blue='0/0 0.5/0.45 1/1',eq=saturation=0.95:contrast=1.03:brightness=0.01`
- **Captions (LOCKED 2026-07-07):** 2 words/screen, white **Bellefair** ~112px on an
  **opaque black box** (`BorderStyle 3`), centred low `y≈1450`, timed to speech
  (`cap_bellefair.py`, boxed 2-word default). Cut under the hook + over ANY b-roll.
  Archivo-Black yellow karaoke (`cap_ass.py`) is retired.
- **DM recreation** (`dmphone.py`): dark IG DM, Sam's real avatar, gradient bubbles,
  yellow highlight **outline** on the key bubble, NO fake status bar, labels off the DM.
- **Highlighter:** translucent yellow `rgba(255,221,0,0.5)`, sweep-reveal + boil jitter.
  Photos get **no** annotation (clean) — label only.
- **Bellefair hook:** ~98px black on a white rounded card, slides up to ~70px from the
  bottom, held ~2.2s; captions suppressed for that window; 2 lines, statement-style.
- **Fonts** (fetched at runtime, Google Fonts via jsDelivr): Bellefair (captions + hook),
  Inter (DM bubbles), Caveat (handwritten labels). Archivo Black = retired caption font.
- **Edge-boil card:** kraft gradient bg, white-bordered screenshot card, slow Ken-Burns,
  film grain + vignette, ~4 reseeds/sec jitter (`#annog` transform — NOT the SVG
  displacement boil, which smears thin strokes into rainbow noise in this Chromium).

## Reusable engine vs per-interview config
- **Reusable engine:** `r2_helper.py`, `mlshot.py`, `transcribe.py`, `render_base.py`,
  `edgeboil.py`, `dmphone.py` (DM recreation), `cap_bellefair.py` (captions),
  `composite2.py`, `ig_hook.py`, `source_assets.py`. (`cap_ass.py` retired.)
- **Edit each interview:** `cut_build.py` (clip windows/anchors), `broll_plan2.py`
  (beat plan + timings, incl. `dm()` beats), `ig_batch.py` (hook lines).
- **DM avatar (runtime, not committed):** `dmphone.py` reads `broll_src/sam_avatar.jpg` —
  crop a frontal Sam frame from the source into it before rendering DMs (keep the vault
  markdown-only; don't commit the JPEG).

## Gotchas
- News sites with ad/cookie walls (Rolling Stone) screenshot as the wall — use CNBC,
  CBS, or a Google-results page instead. Always eyeball the screenshot before using it.
- microlink free tier ≈ 50 shots/day. Instagram/LinkedIn profiles are login-walled.
- ElevenLabs Scribe in ONE call keeps diarisation labels consistent; chunking resets them.
- The SVG `feDisplacementMap` "boil" rainbow-smears large thin strokes in the bundled
  Chromium — use the per-frame `#annog` jitter instead (already wired in `edgeboil.py`).

## v2 additions (2026-08-28, Karel + Melvin batch)

- `voxcard.py` — vox decoder cards AND hand-drawn gfx beats (kinds: article, shot
  with `croph` site pans, photo, blank, gfx: chart/cross/clock/funnel/stack).
  Same 1080x1920 mp4 output contract as edgeboil.py.
- `build_cut.py` + `render_base2.py` — guest-dominant two-speaker EDL and per-side crop.
- `bars.py` — prison-bar drop/lift transition with real SFX events.
- `hbr_page.py` — recreate a blocked site's article page from its real HTML + real
  logo SVG; the pattern for any page microlink cannot capture.
- `composite3.py` — video stack + per-clip music bed (16dB under, -16 LUFS speech)
  + SFX, hook card on every cut, 420s per-clip timeout.

Full sourcing rules: SKILL.md items 12-18. Zero generic stock, ever.
