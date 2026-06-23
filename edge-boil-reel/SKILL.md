---
name: edge-boil-reel
description: Build Vox-style annotated-document reels with "edge boil" hand-drawn animation — vintage newspaper/document cards on kraft paper, boiling marker circles/arrows/scribbles/underlines, real headline screenshots, an animated archival photo, an ElevenLabs music bed, cut to a sub-2-second visual rhythm. Runs entirely in a cloud Claude Code session off this repo — no local machine needed. Trigger phrases include "edge boil reel", "newspaper reel", "annotated newspaper short", "document annotation reel", "Vox-style reel".
---

# Edge-Boil Annotated-Document Reel

Recreates the Vox / Chris Moran look: real documents and headlines on a kraft-paper desk, with hand-drawn marker annotations that wobble ("edge boil") like frame-by-frame animation. **Runs fully in the cloud** — everything below works inside a Claude Code session against this cloned repo, with no local machine on either end. The finished `.mp4` is handed back to you in the session (see Step 8).

> **Part of the Moran motion system.** This skill is the specific *annotated-newspaper* format. For the reusable cross-reel techniques — editorial layered backgrounds, texture integration, ink-bleed reveal, jitter/stop-motion, cutting on action, plus the edge-boil and analog-photo recipes — see `references/moran-motion-toolkit.md` and the copy-paste CSS/SVG/JS in `references/moran-snippets.html`. Use those to add premium documentary polish to ANY reel, not just newspaper ones.

## The look, in one paragraph

Hard cuts every 5–7s between "scenes"; a NEW visual event every ≤2s inside each scene (card slam-in → circle draws on → arrow draws → handwritten label fades up → stamp slams). Annotations are thick round-cap strokes in marker blue `#2a36c8`, red `#e03020` / `rgba(214,40,40,.62)`, and white — they DRAW ON via stroke-dashoffset, then keep boiling forever. Slow Ken Burns push on every scene. Film grain + vignette over everything. Payoff card in Fraunces 900 with the channel handle.

## What you need (all cloud-available)

- **Python 3.11+** with Playwright + Pillow, **Chromium** for Playwright, and **ffmpeg** (via the `imageio-ffmpeg` wheel — no system install needed). `scripts/install.sh` provisions all of this; run it once per fresh container.
- **ElevenLabs API key** *(optional)* — for the music bed. Put it in the repo `.env` as `ELEVENLABS_API_KEY` (same key the rest of this repo uses; see `.env.example`). Without it, `template/gen_music.py` falls back to a bundled `../music/` track.
- **Higgsfield** *(optional)* — for the one animated archival-photo beat. Available as an MCP server in a cloud session. If it isn't connected, the reel still builds; that beat just uses a static Ken-Burns photo instead of a moving clip.

Everything else (fonts, render, encode) is free and self-contained in this repo.

## Working directory

Pick a work dir inside the repo (e.g. `edge-boil-reel/work/<project>/`) and run all the template scripts from there — they read/write relative paths (`assets/`, `fonts/`, `clipframes/`, `preview/`, `frames_out/`, `finished/`). Copy `template/stage.html` into the work dir as your starting stage and edit it per reel. Keep `work/` out of git (it holds generated frames + binaries).

## Pipeline (proven order)

1. **Story + beat sheet first.** ~6 beats for 30s. Each beat = one visual + one VO line (8–16 words). Write the beat table (time, VO, visual, annotation) before touching code. See `references/example-beat-sheet.md` for a worked example.
2. **Source REAL assets** (never forge a scan or headline):
   - Modern headlines: Playwright `h1` bounding-box crops at `device_scale_factor=2` (`template/crops.py`); full-page shots via `template/shots.py`. Both launch Chromium with `--ignore-certificate-errors` (the cloud egress proxy self-signs TLS). Edit the `JOBS` / `PAGES` list in each to this reel's real article URLs.
   - Archival photos: Wikimedia Commons `Special:FilePath` URLs (public domain), `curl -skL`.
   - Historic quotes with no scan available: typeset as a clearly-ATTRIBUTED document card (label line, e.g. "REPORTED IN THE NEW YORK TIMES · JULY 8, 1958") — documentary recreation, never a fake clipping. Paywalled archive sites are often egress-blocked from the cloud; don't burn time there.
3. **Fonts**: `python3 template/fetch_fonts.py` (Fraunces, Inter, IBM Plex Mono, Old Standard TT for vintage type, Caveat for handwriting). Writes `fonts/all.css` + `fonts/*.woff2` into the work dir; `stage.html` links `fonts/all.css`.
4. **Animated archival clip** *(optional, Higgsfield)* for the photo beat — it's the "alive" moment of the reel:
   - `media_upload` → PUT bytes → `media_confirm` (the `media_import_url` route 429s on Wikimedia).
   - Model `seedance_2_0`, 5s, 3:4, 720p std ≈ **22.5 credits**. Prompt recipe: "Archival 19XX black-and-white documentary footage… very subtle slow push-in… gentle film grain, gate weave, 16mm flicker… Preserve the exact appearance, faces, machinery and composition of the reference photograph; no warping, no added objects, no text."
   - Extract frames: `ffmpeg -vf "fps=24,scale=1000:-1"` → `clipframes/f_%03d.jpg`; the stage swaps them per-frame under the annotation layer (`HFCLIP` in `stage.html`). No Higgsfield? Leave `clipframes/` empty — the stage holds the still and Ken-Burns pushes on it.
5. **Build the stage** from `template/stage.html`. Key mechanics (don't reinvent):
   - **Edge boil** = one SVG filter: feTurbulence(baseFreq .012)+feDisplacementMap(scale 16) chained into feTurbulence(.06)+feDisplacementMap(7), `seed` stepped `1+floor(t*4)%7` — 4 reseeds/sec is the hand-drawn boil rate.
   - Deterministic `seek(t)` sets EVERYTHING from t — no CSS animations — so Playwright can render exact frames.
   - Draw-on via `getTotalLength()` + dashoffset. Slams via scale 1.55→1 with back-ease. Underlines/circles are MEASURED from the live DOM (`setUnderlines()` reads span/card rects) — never hardcode coords over text.
   - SVG noise/grain layers need explicit `width:100%;height:100%` (replaced elements don't stretch from `inset:0`).
   - The end card uses the channel handle (default `@sameyeam.secrets`) — edit it in `stage.html`.
6. **Preview → iterate → full render** (all headless Playwright, in-cloud):
   - `python3 template/render.py preview 4.2 8.3 …` → JPGs in `preview/`. Read them, fix layout, repeat.
   - `python3 template/render.py full 30 32.0` → ≈960 frames in `frames_out/` (~10 min).
7. **Music** *(optional)*: `python3 template/gen_music.py --seconds 35 --out soundtrack.mp3` generates an ElevenLabs bed (reads `ELEVENLABS_API_KEY` from `.env`/env) or copies a `../music/` fallback. Prompt recipe baked into the script: investigative-documentary tension, a percussion gimmick matched to the topic (typewriter clicks for newspapers), "steady driving rhythm around 100 BPM with a clear beat to cut visuals to", "building intensity in clear 5-second sections, rising into a final punchy resolving hit", "instrumental only, no vocals, mixed to sit under a male voiceover". Mixed at volume 0.85 with a 1.6s end fade (you record VO over it).
8. **Encode + deliver**:
   - `./template/finish.sh --frames frames_out --music soundtrack.mp3 --duration 32 --name <project>` encodes a silent master and a music version into `finished/`.
   - **Delivery is in-session**: this skill runs in the cloud, so there is no local folder to pick up from. The agent running the session hands the finished `finished/<project>-with-music.mp4` straight back to you in chat. Nothing is uploaded anywhere and no external account is required.

## Photo treatment — "analog / filmed" look

Every still-photo card gets four layers so it reads as a FILMED physical print, not a flat JPEG (full breakdown in `references/TECHNIQUE-PHOTOS.md`):
1. **Fringe blur** — blurred clone of the image masked to the frame edges (`blur(6px)` + radial-gradient mask, ellipse over the subject stays sharp).
2. **Film dust** — sparse white specks (feTurbulence baseFreq ~0.35 thresholded, `mix-blend-mode:screen`, opacity ~0.25), **seed stepped 6–8×/sec** so dust flickers like a real film scan.
3. **Vignette** — per-card radial gradient centred on the subject (stronger than the global stage vignette); it steers the eye, not just mood.
4. **Slow zoom** — keep the existing 1.0→1.06 Ken Burns.
Stack order on the card: photo → fringe-blur clone → dust (screen) → vignette. Apply the same dust/vignette pass over the Higgsfield clip for consistency.

## Rhythm rules (what made it work)

- Something NEW on screen every ≤2s; hard cut every 5–7s.
- Annotations draw in 0.6–1.2s, never pop.
- Underline the quote in 2–3 sweeps timed to VO phrases, not all at once.
- One stamp per scene max ("VERBATIM · 1958", "68 YEARS APART") — scale 2.6→1 snap.
- End on a Fraunces payoff card + handle, last beat held ~2s with no new motion except boil.

## Costs (reference)

- Higgsfield: ~22.5 credits per 5s Seedance 2.0 720p clip (one per reel is enough) — and it's optional.
- ElevenLabs music: one ~35s generation per reel — also optional (bundled `../music/` fallback).
- Everything else: free (Playwright render, ffmpeg encode).

## Files in this skill

```
edge-boil-reel/
├── SKILL.md                  ← this file
├── template/
│   ├── stage.html            ← the deterministic seek(t) stage (copy per reel, then edit)
│   ├── render.py             ← Playwright preview/full frame renderer
│   ├── fetch_fonts.py        ← downloads Fraunces/Inter/Plex Mono/Old Standard/Caveat → fonts/
│   ├── crops.py              ← headline h1 bounding-box crops (edit JOBS per reel)
│   ├── shots.py              ← full-page article screenshots (edit PAGES per reel)
│   ├── gen_music.py          ← ElevenLabs /v1/music bed (key from .env) + ../music fallback
│   └── finish.sh             ← ffmpeg encode → finished/<name>-{silent,with-music}.mp4
├── references/
│   ├── TECHNIQUE.md          ← the edge-boil technique breakdown (the look + why it works)
│   ├── TECHNIQUE-PHOTOS.md   ← analog/filmed-photo four-layer recipe
│   ├── moran-motion-toolkit.md  ← the 7 cross-reel documentary techniques
│   ├── moran-snippets.html   ← copy-paste CSS/SVG/JS for those techniques
│   └── example-beat-sheet.md ← a worked beat sheet you can pattern-match
└── scripts/
    └── install.sh            ← one-shot: Playwright + Chromium + imageio-ffmpeg + Pillow
```

## When NOT to use this skill

- **Talking-head clips from a long-form interview.** That's `sam-clips-engine`. This skill builds a *designed* annotated-document reel from a story + sourced assets, not a cut from footage.
- **Anything that needs a real video subject.** Edge-boil is documents, headlines, archival stills and annotations — no presenter.
