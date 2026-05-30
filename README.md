# Sam YT Shorts Engine

End-to-end clips engine for **Sam Eye Am** (@sameyeam.secrets). Drop in a long-form interview or podcast, get back finished 30-45s vertical Shorts ready to upload — viral moment selection, precision cuts, branded captions, b-roll overlays, and ElevenLabs music.

Runs inside Claude Code as a skill.

## What's in this repo

```
sam-yt-shorts-engine/
├── sam-clips-engine/           ← the Claude Code skill (SKILL.md, orchestrator, helpers, refs)
├── brand_library/              ← logos, person photos, motion graphic concepts, build scripts
├── music/                      ← 4 fallback music tracks
├── fonts/                      ← Montserrat (captions) + Bellefair (brand serif)
└── install.sh                  ← one-shot install + sanity check
```

## Quick start

### 1. Prerequisites

- macOS or Linux with **ffmpeg** + **ffprobe** + **yt-dlp** on PATH
- **Python 3.11+** with PIL/Pillow
- **Claude Code** installed with active subscription
- **video-use** skill installed at `~/.claude/skills/video-use/` (the cutting foundation — install separately from its own repo)
- **ELEVENLABS_API_KEY** in env or at `~/.claude/skills/video-use/.env` (for Scribe transcription + per-clip music generation)

### 2. Install

```bash
git clone https://github.com/harryverity01/sam-yt-shorts-engine.git
cd sam-yt-shorts-engine
./install.sh
```

The installer:
- Symlinks `sam-clips-engine/` to `~/.claude/skills/sam-clips-engine/` so Claude Code discovers it
- Verifies ffmpeg, yt-dlp, video-use, ElevenLabs key
- Checks all asset paths resolve

### 3. Use

Open Claude Code in any directory and say something like:

> *"Use sam-clips-engine to build 12 clips from `/path/to/my-podcast.mp4`, work-dir `~/Desktop/podcast-shorts`"*

Or for a YouTube URL:

> *"Sam shorts from this YouTube video: https://youtu.be/..."*

Claude will trigger the skill, run the 6-step pipeline, pause at the viral-ranking step for you to confirm picks, then ship finished `.mp4`s to `<work-dir>/finished/`.

## The pipeline

Each clip goes through:

1. **Ingest** — yt-dlp or local file → source.mp4 + sync verification
2. **Transcribe** — ElevenLabs Scribe word-level (cached — runs once per source)
3. **Pack** — phrase-level transcript → `takes_packed.md` for Claude to read
4. **Rank viral moments** — Claude scores candidate windows on the Sam-tuned rubric (hook strength, specific claims, audience fit, etc.) and picks the top N
5. **Per-clip build**:
   - Precision cut at word boundaries with 50ms front / 80ms back padding + Sam color grade
   - B-roll overlays from `brand_library/` (1 every 8–15s — IG popup, Calendly card, brand logos, person photos)
   - Hormozi-style word-by-word captions (Montserrat Black 140pt, white fill + 8px black stroke)
   - Music: ElevenLabs per-clip bespoke (mood-classified from transcript) OR library fallback
6. **Output** — `finished/01_<slug>.mp4`, `finished/02_<slug>.mp4`, … (no end card — Sam doesn't want one)

## Brand library

5 active overlay concepts:

| Concept | Trigger | Notes |
|---|---|---|
| `sam_ig_popup.mov` | "@sameyeam", "my Instagram", "follow me" | Pixel-faithful IG profile recreation, 4s slide-in |
| `handle_sameyeam_secrets.mov` | end of every clip | Default handle lower-third plug |
| `sam_calendly_fully_booked.mov` | "fully booked", "150 calls", "Calendly" | Real Calendly page recreation w/ "FULLY BOOKED" stamp |
| `ig_comment_<keyword>.mov` | "comment X" CTA | **Runtime-rendered** — keyword swaps per use (TRAINING/CLIENTS/AI/...) |
| `broll/william_brown_villa.mp4` | "William Brown" in lower-energy clips | Wide villa shot (cropped 9:16 from interview footage) |

Concept graphics are **lossless QuickTime Animation (qtrle) .mov with alpha** — 8-bit RGB+alpha, which is the native fidelity the graphics are rendered at (PIL RGBA), so nothing is lost from source. ~6x smaller than ProRes 4444, rock-solid alpha that composites reliably (VP9/webm alpha does NOT — it renders transparent areas black, so we don't use it).

## Adding new b-roll templates

The rule is **real reference first** — never invent a UI element from memory. Every active concept was built from a real screenshot.

To add a new template:

1. Get a real reference screenshot (Sam's own version where possible)
2. Sample exact colours via PIL `getpixel()`
3. Identify the platform's actual font (Helvetica/SF Pro for iOS, Inter for web tools — **NOT** Sam's brand fonts for UI mimicry)
4. Build a parameterised renderer following the `build_ig_popup.py` / `build_sam_calendly.py` patterns
5. Add to `brand_library/manifest.json` with trigger phrases
6. Update `sam-clips-engine/helpers/pick_broll.py` RULES with a regex pattern

See `sam-clips-engine/references/brand_library.md` for the full methodology.

## Hard rules (production correctness)

Inherited from the [video-use](https://github.com/anthropics/video-use) skill — non-negotiable:

1. Subtitles applied LAST in the filter chain
2. Per-segment extract → lossless concat (never single-pass filtergraph with overlays)
3. 30ms audio fades at every segment boundary
4. Overlays use `setpts=PTS-STARTPTS+T/TB` (shifts overlay frame 0 to its window start)
5. Cuts snap to word boundaries from the Scribe transcript
6. Pad every cut edge — 50ms front, 80ms back
7. Word-level Scribe only — never Whisper, never SRT/phrase mode
8. Cache transcripts per source — never re-transcribe

Sam-specific:
9. **Reference-first** for new b-roll templates
10. One overlay every 8–15s in the body (matches the 14 viral shorts cadence)
11. No end card (Sam doesn't want one) — the music-mixed clip is the final output
12. Music at -16dB under voice

## Cost

- **ElevenLabs Scribe transcription** — ~$0.40 per hour of source audio (cached, runs once)
- **ElevenLabs Music generation** — included in your ElevenLabs subscription (per-clip bespoke). Falls back to library if quota tight.
- **Claude (for ranking)** — runs inside your Claude Code subscription, no additional API cost

## Related repos

- **[sam-yt-long-form](https://github.com/harryverity01/sam-yt-long-form)** — the long-form (5-10min) YouTube pipeline. Different aspect, different beats, different output.

## License

Internal use for Sam Eye Am. Built by Harry Verity.
