# Sam Ey Am Brand Library

Reusable graphics + logos + portraits for editing Sam Eye Am content.

**Status: PAUSED — 2026-05-28**

> Built 41 speculative concept graphics, only **2 survived review** (the pixel-faithful IG-UI recreations). Logos + people remain active. When a real Sam edit needs an overlay, build it from a specific reference — not from an invented concept list.

**Source:** 87-min Sam x William Brown podcast + full Sam YouTube catalog (804 videos) + Sam IG screenshot

## Quick stats

| Asset type | Count | Folder |
|---|---|---|
| Brand logos | 48 | `logos/` |
| Person portraits | 11 | `people/` |
| Active concepts | **2** | `concepts/` |
| Archived concepts | 39 | `concepts/_rejected/` |
| B-roll | 0 (planned) | `broll/` |
| Number renders | 0 (planned) | `numbers/` |

## The 2 active concepts

- **`sam_ig_popup.mov`** — Pixel-faithful recreation of @sameyeam.secrets IG profile (avatar / 143K followers / verified / Follow button). 4s slide-in. Helvetica (IG UI font).
- **`handle_sameyeam_secrets.mov`** — Orange-@ IG handle lower-third. Reusable across any Short. 3s slide-in.

## Layout

```
brand_library/
├── manifest.json              ← single source of truth (every asset + trigger keywords)
├── README.md                  ← this file
├── build_concepts.py          ← first 10 concepts (core)
├── build_concepts_part2.py    ← next 20 concepts (expanded)
├── build_concepts_part3.py    ← latest 14 (current Sam hooks + DM cards + handle)
├── logos/                     ← 47 brand PNGs from Brandfetch
├── people/                    ← 10 portrait JPGs/PNGs (Wikipedia + YouTube avatars)
├── concepts/                  ← 44 transparent .mov clips (1080×1920, ProRes 4444 alpha)
│   └── _previews/             ← static stills for browsing
├── broll/                     ← reserved for catalogued Sam b-roll
├── numbers/                   ← reserved for counter renders
├── sam_content/               ← reserved for raw source clips
└── _tmp_concepts/             ← scratch (safe to delete)
```

## Workflow

1. **Cut the interview** down to its punch lines in CapCut.
2. **Scan the transcript** for trigger keywords from `manifest.json` (each concept lists when to use it).
3. **Drop the matching .mov** on an overlay track at the trigger timestamp. Alpha is preserved — no green-screen step needed.
4. **Pair with logos** when Sam names a brand (e.g. Stripe stat → `concepts/stripe_fees.mov` + `logos/stripe_com_logo.png`).
5. **End with a DM card** — `concepts/comment_*.mov` for the CTA.
6. **Lower-third the handle** — `concepts/handle_sameyeam_secrets.mov` for the IG plug.

## Brand specs

- **Resolution:** 1080×1920 (9:16)
- **FPS:** 25
- **Codec:** ProRes 4444 (alpha-preserved)
- **Palette:** Sam-orange `#FF8C3C` primary, navy `#0C0E16` accent, cream `#F5F0E6` text
- **Headline font:** Anton (italic skew -0.14, orange drop shadow)
- **Body font:** Montserrat Black / Regular

## Regenerating

```bash
cd "/Volumes/Seagate/YouTube/Sam Ey Am/brand_library"
python3 build_concepts.py        # renders the 10 core
python3 build_concepts_part2.py  # renders the next 20
python3 build_concepts_part3.py  # renders the latest 14
```

Each script reuses helpers from `build_concepts.py` (envelope, draw_anton_with_shadow, palette, fonts) so style stays consistent.

## Open backlog

- `broll/` — catalog Sam's existing b-roll (festival, villa, studio) with descriptions for transcript-matching
- `numbers/` — pre-render 0–100 / 0–10K / 0–1M counter sweeps for plug-and-play stat reveals
- Re-fetch Tony Robbins / Hormozi / etc. portraits at higher resolution if any feel low-res in production
