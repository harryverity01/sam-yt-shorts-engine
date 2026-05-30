# Brand Library Reference

The brand library lives at `/Volumes/Seagate/YouTube/Sam Ey Am/brand_library/`. It is the single source of truth for every overlay asset.

## Current state (2026-05-28)

**Active concepts** (3):
- `sam_ig_popup.mov` — Pixel-faithful @sameyeam.secrets IG profile popup. 4s slide-in + hold + fade. Use for IG/follower/profile-related beats.
- `handle_sameyeam_secrets.mov` — Orange @ icon + handle + FOLLOW pill lower-third. 3s slide-in. Default end-of-clip plug.
- `sam_calendly_fully_booked.mov` — Pixel-faithful Sam Calendly booking page. 6s with progressive booking animation + FULLY BOOKED stamp slam. Use for "fully booked" / "150 calls" / Calendly mentions.

**Logos** (48 PNGs at `logos/`): All major brands Sam name-drops — Stripe, Hilton, Tommy Hilfiger, IG, YouTube, ManyChat, ChatGPT, Claude, Calendly, etc. Always size to ~30-40% of frame width when overlaying.

**People** (11 portraits at `people/`): Hormozi, Naval, Buffett, Tony Robbins, Rockefeller, Joe Rogan, Elon, Alan Watts, Robert Greene, Danielle Lukins, Piers Morgan, Sam Eye Am himself.

**Archived** (39 rejects at `concepts/_rejected/`): Speculative concepts that didn't survive review. DO NOT use these — they're cautionary, not foundational. The lesson they encode: never invent a UI element; always start from a real reference.

## The active-template rule

The 3 active concepts share a property: **every one was built from a real reference screenshot**.
- `sam_ig_popup` — pixel-cropped from a screenshot of Sam's actual IG profile
- `handle_sameyeam_secrets` — modelled on Instagram's actual handle lower-third style
- `sam_calendly_fully_booked` — pulled from Sam's actual Calendly via headless Playwright render

The 39 rejects share the opposite property: they were built from "what I imagine the asset should look like." None of them worked.

**This is the rule for adding new templates:**

## How to add a new template

1. **Get a real reference**
   - Screenshot of the actual app/UI you're recreating
   - Sam's own version where possible (his Stripe push, his ManyChat dashboard)
   - Public marketing screenshots OK as a starting point — but flag if you're guessing
   - Headless Playwright works for public web pages (see `build_sam_calendly.py` for the pattern)

2. **Sample exact colours from the screenshot**
   ```python
   from PIL import Image
   src = Image.open("/path/to/ref.png")
   px = src.getpixel((x, y))   # rgba tuple — use this hex in your renderer
   ```

3. **Identify the platform's actual font**
   - iOS apps: Helvetica / SF Pro (`/System/Library/Fonts/SFNS.ttf` and `/System/Library/Fonts/Helvetica.ttc`)
   - Web tools: usually Inter or similar geometric sans
   - **NOT Sam's brand fonts** (Bellefair/Montserrat) — those are for Sam-branded wrap assets (handle plug, end card), NOT UI mimicry

4. **Build a parameterised renderer**
   Follow the pattern of `build_ig_popup.py` / `build_sam_calendly.py`. Single function `render_<name>(t, dur, **params)` returning a PIL canvas. Driver loops 0→dur, saves PNGs, ffmpeg → ProRes 4444 with alpha.
   Parameterise the swappable text (keyword, amount, name) — the UI chrome stays identical across uses.

5. **Add to `brand_library/manifest.json`**
   ```json
   {
     "file": "concepts/your_template.mov",
     "duration": 4.0,
     "category": "<category>",
     "trigger": "<what makes pick_broll.py fire this>",
     "build_script": "build_your_template.py",
     "source_reference": "people/_your_template_reference.png",
     "params": ["keyword", "amount"]
   }
   ```

6. **Update `pick_broll.py` RULES**
   Add a regex pattern that maps a transcript phrase to your new asset. Keep patterns specific — false positives are worse than misses.

## Examples of templates that would land

(Not yet built — opportunities)

- **`stripe_payment_notification`** — iOS Stripe push banner. Params: amount, client name. Needs a real Stripe push screenshot.
- **`imessage_client_praise`** — iMessage bubble client testimonial. Params: message, contact name, time. Needs a real iMessage screenshot.
- **`ig_comment_highlight`** — IG comment thread with one comment glowing the trigger word. Params: keyword, username. Needs a real IG comment screenshot.
- **`ig_dm_autoreply`** — IG DM auto-reply received. Params: dm body, link preview. Needs a real IG DM screenshot.

Each of these would need a real reference before building.

## The 8-15s cadence rule

Overlays land best every 8-15 seconds in a 30-45s clip. So a typical clip has 2-4 overlays:

- 0-2s: hook (no overlay — let Sam's words land first)
- ~8s: first overlay (logo / person / stat reveal)
- ~18s: second overlay (related to mid-clip beat)
- ~30s: handle lower-third (end-of-clip plug)

Don't stack overlays denser than 8s — viewers can't process them. Don't stretch past 15s without an overlay — the clip starts feeling flat.

## Why the rejected concepts failed

Looking back at the 39 archived in `concepts/_rejected/`, they failed for one of three reasons:

1. **Abstract** — `closer_to_money`, `staircase`, `vested_interest`, `responsibility` — these were trying to visualise an idea instead of mirroring a thing the viewer already recognises. Recognition beats interpretation every time.
2. **Off-brand colours** — initial DM cards used IG-pink + IG-grey when Sam's brand is orange + navy + cream. Rebuilt → cleaner. The IG popup used IG's own dark UI which was correct because it WAS the IG UI.
3. **Font mismatch** — Anton (industrial slab) doesn't match Sam's actual visual identity (Bellefair Didone serif). When we swapped to Bellefair across all 41 concepts, the ones that survived were the ones that didn't need Bellefair in the first place — they needed the platform's own font.

The lesson lives in the manifest under `library_status.note` — keep it visible.
