# ElevenLabs Music Prompts for Sam Clips

Used by `pick_music.py` to generate per-clip bespoke music.

## Universal prompt rules

Every prompt MUST end with:

```
no vocals, no prominent drums, designed to sit under a YouTube voiceover, lofi production polish
```

- **no vocals** — they fight Sam's voice
- **no prominent drums** — keeps space in the mix for the spoken word
- **designed to sit under a YouTube voiceover** — frames the model
- **lofi production polish** — production quality cue, prevents synthetic/sterile output

## Mood → prompt seed mapping

| Mood | When it fires | Prompt seed |
|---|---|---|
| **proof** | Clip is about a specific result Sam achieved ($X, Y leads, Z%) | `warm electric piano + soft sub bass, optimistic build, confident cinematic tech` |
| **origin** | Sam tells a backstory ("when I started", "years ago", "remember when") | `soft pad swell, single piano motif, nostalgic warmth, hopeful` |
| **contrarian** | Sam pushes back on industry truisms ("everyone says X, actually Y") | `low pulse + ticking, slight tension, intelligent restrained, cinematic tech` |
| **how-to** | Step-by-step / system explanation | `thoughtful boardroom, strings pad + light pulse, restrained intelligent` |
| **case-study** | Client win narrative | `rising arpeggio + sub-bass drop, social-media-positive, hopeful build to subtle drop` |

`pick_music.py` auto-classifies based on keyword counts in the transcript. Override with `--mood` if the auto-pick is wrong.

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
