# "Analog / filmed photo" treatment — technique breakdown (Chris Moran reel 2)

Source: https://www.instagram.com/reel/DZFqNzwAqVa/ — Chris Moran (@chrismoran__), 26s, 16.4k likes.
Caption: "How documentary photos get that analog / filmed look". Extracted 2026-06-12.
Companion to TECHNIQUE.md (edge boil). This is how Vox makes still photos feel like FILMED physical objects, not flat JPEGs.

## Full voiceover transcript

> Vox photos never look flat. Here's how. It's just three layers. The first is fringe blur. Soften the edges of your frame while keeping your subject sharp. Second, film dust. I got this layer from Texture Labs. The subtle dust makes it feel like a film scan. Third, vignetting. Use it to guide the viewer's eye to your subject. I also like to add some slow zooms to make it feel like a physical photo is being filmed. These subtle treatments show up all the time in documentaries, and Vox uses them a lot to create depth.

## The recipe (exact, from his AE screens)

Layer stack shown (top→bottom): `Zoom (Scale keyframes) → Vignette → Film Dust (Screen blend) → Map → Lens Blur → photo → Frame`.

1. **Fringe blur** — edges of the FRAME go soft, subject stays sharp. Done with **Compound Blur**: Maximum Blur **6.0**, Blur Layer = a luminance **map** (radial gradient: dark over subject = sharp, light at frame edges = blurred), "If Layer Sizes Differ: Stretch Map". This fakes a lens' field curvature / scanned-print softness.
2. **Film dust** — a real dust scan layer (his source: **Texture Labs**, texturelabs.org, free film-dust scans) set to **Screen** blend, subtle. Sells "film scan", adds living texture to dark areas.
3. **Vignette** — darkened corners, used deliberately to steer the eye to the subject (not just mood).
4. **Slow zoom** — gentle Scale keyframes so it feels like a rostrum camera is filming a physical print.

## Web/CSS equivalent for our stage.html pipeline

Apply to every photo card in edge-boil reels:

- **Fringe blur**: stack a blurred clone of the image over the sharp one, masked to the edges:
  `filter: blur(6px); -webkit-mask-image: radial-gradient(ellipse 60% 55% at 50% 45%, transparent 40%, black 78%); mask-image: …same…` (tune the ellipse to sit over the subject).
- **Film dust**: SVG feTurbulence (baseFrequency ~0.35, numOctaves 2) → feColorMatrix to threshold into sparse white specks → `mix-blend-mode: screen; opacity:0.25`, and **step the seed at ~6-8/sec** (dust must flicker frame-to-frame like a real scan — static dust reads as dirt on the screen). Alternative: download 2-3 real Texture Labs dust scans and cycle them.
- **Vignette**: per-photo-card radial-gradient overlay (stronger than the global stage vignette), ellipse centred on the subject.
- **Slow zoom**: already in the pipeline (Ken Burns per beat) — keep it ~1.0→1.06 over the beat.
- Order on the card: photo → fringe-blur clone → dust (screen) → vignette.

## Where this slots in

- Beat-4-style photo moments in edge-boil reels (e.g. the Mark I Perceptron card) get all four layers.
- Also applies to Higgsfield clips: ask for the grain/flicker in the prompt, then add fringe blur + vignette + dust at composite time for consistency with untreated stills.
