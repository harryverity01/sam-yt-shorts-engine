# Music Prompts for Sam Clips

Used by `pick_music.py`. **Provider order: Suno → ElevenLabs → library.**

> **Why this changed:** Sam said the old beds "sound like elevator music." The old
> seeds were corporate/ambient ("thoughtful boardroom", "no prominent drums"). Sam's
> shorts are Hormozi-style — they need forward motion. New direction: **modern,
> motivational, subtle beat, warm — just no vocals** so it sits under his voice.

## Universal prompt rules (new)

- **instrumental, no vocals** — vocals fight Sam's voice
- **subtle / tasteful beat is GOOD** — light boom-bap or lo-fi hip-hop drums give
  momentum (the opposite of elevator music). Just not so loud it competes.
- **"sits under a spoken voiceover"** — frames the mix for the model
- **modern / lo-fi production** — not orchestral, not corporate-ambient

## Mood → prompt seed mapping (de-elevator-ed)

| Mood | When it fires | Prompt seed |
|---|---|---|
| **proof** | Specific result ($X, Y leads, Z%) | `modern motivational lo-fi hip-hop, warm Rhodes keys, crisp subtle boom-bap beat, confident forward momentum` |
| **origin** | Backstory ("when I started", "years ago") | `cinematic lo-fi, soft piano motif + warm sub bass, hopeful, moving forward, light tasteful drums` |
| **contrarian** | Pushes back on a truism | `tense modern trap-lite, muted plucks + ticking hats, intelligent and a little edgy, restrained` |
| **how-to** | Step-by-step / system | `clean modern lo-fi beat, bright plucks over warm pads, focused and motivational, light percussion` |
| **case-study** | Client win narrative | `uplifting lo-fi hip-hop, rising arpeggio + warm sub-bass, social-positive build, tasteful beat` |

All seeds auto-append `instrumental, no vocals, sits under a voiceover`. `pick_music.py`
auto-classifies from the transcript; override with `--mood`.

## Suno setup

Suno has no official public API — `pick_music.py` targets the common **sunoapi.org v1**
shape (`/api/v1/generate` → poll `/api/v1/generate/record-info` → download). To use it:

- Put the key in `SUNO_API_KEY` (env) **or** drop it in the folder pointed to by
  `music.suno_secret` in `brand_assets.json` (first file in that dir = the key).
- Different provider? Override `music.suno_base` / `suno_generate_path` /
  `suno_poll_path` / `suno_model` in `brand_assets.json`, or `SUNO_API_BASE` / `SUNO_MODEL` in env.
- No key set → it silently falls through to ElevenLabs, then the library. Nothing breaks.

## Library fallback

If ElevenLabs quota is exhausted or API fails, `pick_music.py` falls back to one of Sam's 4 library tracks:

| File | Best for |
|---|---|
| `Show the How 2.mp3` | confident / proof / tutorial / how-to |
| `Show the How Suno.mp3` | same vibe, alternate version |
| `Varation 1 strings.mp3` | emotive / origin / story / cinematic |
| `Varation 2 strings.mp3` | emotive / restrained / thoughtful |

Mood→library mapping is in `brand_assets.json` `music_tracks[].moods`.

## Mix levels (locked from build_short.py)

- **Music**: -16dB under voice (DON'T go louder)
- **Voice**: 0dB reference
- **Music fade in**: 0.5s
- **Music fade out**: 0.5s before clip end

If the music feels too quiet, the source is probably too soft — boost the voice with `-af loudnorm`, don't push the music up.
