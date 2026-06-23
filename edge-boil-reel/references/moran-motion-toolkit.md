# Moran Motion Toolkit

> Reference bundled with `edge-boil-reel`. A versatile documentary motion-design toolkit distilled from Chris Moran (@chrismoran__): seven techniques that make motion graphics look editorial/Vox-grade, each with the After Effects original AND a cloud HTML/CSS/SVG translation (rendered headless via Playwright, not AE). Apply à la carte to any vertical reel for premium documentary polish.

Seven techniques from Chris Moran (@chrismoran__), the creator behind the edge-boil newspaper look. Together they're a coherent **documentary motion-design system**: how to make a flat HTML/CSS reel read as expensive, editorial, hand-crafted film — the Vox/NYT-video register.

**How to use this skill:** when building a reel (with `edge-boil-reel` or any other), pick the techniques that fit and apply their web translations in the stage HTML. Every technique below gives: *what it is*, the *AE original* (for reference/credibility), and **our translation** — the exact CSS/SVG to use in a Playwright-rendered `stage.html` (deterministic `seek(t)`, frame-swap for clips, render at 30fps). Copy-paste versions of all of these are in `references/moran-snippets.html`.

**Golden rule across all of them:** subtlety. Lift, don't shout. Every effect at low strength, layered. The amateur tell is one effect at full whack; the pro look is five effects at 15%.

---

## 1. Editorial layered backgrounds  ★ most versatile — use on almost everything
**What:** never sit content on flat black/white. Flat colour doesn't distract (good) but every-flat = no identity. Back the scene with 2–3 desaturated, subject-relevant images (political → Capitol/scans/architecture; AI → server racks/old computers/circuit macro), tinted so it whispers.
**AE original:** pre-comp the images, add a **Tint** effect — set blacks to **dark grey (not pure black)** and push whites **slightly** brighter so contrast stays subtle; add a little texture on top.
**Our translation:**
```css
.bg-layer{position:absolute;inset:0;background:#1a1a1a;}                 /* lifted black, never #000 */
.bg-layer img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;
  filter:grayscale(1) brightness(0.5) contrast(0.85);opacity:.5;mix-blend-mode:screen;}
.bg-tint{position:absolute;inset:0;background:linear-gradient(160deg,#242424,#141414);mix-blend-mode:multiply;opacity:.6;}
/* then a grain layer on top (see #6) + vignette */
```
Stack 2–3 `.bg-layer img` at different scales/positions, very slow drift (Ken Burns). Keep total contrast low so foreground text pops. This is THE "why Vox looks expensive" lever.

## 2. Texture integration (blend + curves, never opacity)
**What:** texture is the secret sauce — but most people slap it on and drop opacity, which muddies colour and feels stuck-on.
**AE original:** apply texture via **blend mode**; control strength with a **Curves/Levels** adjustment on the texture's luminance, NOT opacity. Then **displacement-map** the title text so it physically takes the texture's form.
**Our translation:**
```css
.tex{position:absolute;inset:0;mix-blend-mode:overlay;          /* or multiply/screen per texture */
  filter:contrast(1.15) brightness(1.05);}                      /* = curves/levels, controls strength */
.tex img{width:100%;height:100%;object-fit:cover;opacity:1;}    /* leave opacity at 1; tune via filter */
```
Title takes-the-texture (displacement): feed the texture into an SVG `feDisplacementMap` over the text (same mechanism as edge boil, larger scale, static seed). Sources: free paper/newspaper/grain textures (Texture Labs, etc.); pick intentionally "like a chef picking an ingredient".

## 3. Ink-bleed reveal (luma matte)
**What:** a design "develops"/uncovers in real time, like the Marauder's Map ink crawling across the page.
**AE original:** a **luma matte** — black-and-white ink-bleed footage masks artwork (inverted luma matte: bright overlay = artwork appears). Spreading footsteps = **Choker** animated 100→0 with **Roughen Edges** stacked on top, so it grows outward like ink.
**Our translation:** drive a CSS/SVG mask from an ink-bleed clip (frame-swap like our Higgsfield clips):
```css
.reveal{ -webkit-mask-image:url(inkframe.png); mask-image:url(inkframe.png);
  -webkit-mask-size:cover; mask-size:cover; }
```
Swap `inkframe` per frame in `seek(t)` so the mask animates; the artwork appears where the ink is bright. Roughen the mask edge with feTurbulence+feDisplacementMap (the edge-boil filter). Source a real ink-bleed overlay (Storyblocks/stock) — don't fake it.

## 4. Edge boil  (already shipped — see edge-boil-reel)
Hand-drawn annotations (circles/arrows/underlines/scribbles) that wobble like frame-by-frame animation. Trim-paths draw-on + Roughen Edges + Turbulent Displace, seed re-rolled ~4×/sec.
**Our translation:** SVG `feTurbulence`(.012)+`feDisplacementMap`(16) chained into `feTurbulence`(.06)+`feDisplacementMap`(7), `seed` = `1+floor(t*4)%7`; draw-on via `stroke-dashoffset`. Full recipe + working filter in this skill's `SKILL.md` + `references/TECHNIQUE.md`.

## 5. Analog / filmed-photo look  (already shipped — see edge-boil-reel)
Makes a still photo read as a FILMED physical print: **fringe blur** (edge-masked blur clone), **film dust** (flickering specks, seed stepped 6–8×/sec), **vignette** centred on subject, **slow zoom**. Full recipe in `edge-boil-reel` SKILL + `TECHNIQUE-PHOTOS.md`. Apply over still photos AND over Higgsfield clips for consistency.

## 6. Jitter / stop-motion (NOT wiggle)
**What:** handmade, shot-frame-by-frame, paper-cutout charm. The opposite of smooth software motion.
**AE original:** **jitter** on position/rotation/scale — SNAPS to new random values (vs wiggle, which oscillates smoothly and reads as software). A heavy **posterize-time** expression gives the same stutter. Great on cutout stickers and titles.
**Our translation:** in `seek(t)`, recompute a *stepped* pseudo-random transform and SNAP (no easing):
```js
function jitter(el,t,amp=6,rotAmp=1.5,fps=8){
  const step=Math.floor(t*fps);                  // posterize-time: hold each value 1/fps s
  const r=(s)=>{const x=Math.sin(s*999.7)*43758.5;return (x-Math.floor(x))*2-1;}; // det. rand
  el.style.transform=`translate(${r(step)*amp}px,${r(step+7)*amp}px) rotate(${r(step+3)*rotAmp}deg)`;
}
```
Use 6–10 fps. This is distinct from our smooth `slam`/`fadeUp` eases — reserve jitter for cutout/collage/sticker elements and the occasional title, not everything.

## 7. Cutting on action (editing rule, not an effect)
**What:** make hard cuts invisible by hiding them inside motion — the eye is tracking the moving thing, so the brain misses the edit. Cut on stillness = jarring.
**Our pipeline rule:** place every hard cut between scenes DURING movement — mid push-in, mid annotation draw-on, mid card-slam, mid bar-graph climb — never on a held still frame. Punch in/out within scenes (scale 1.0→1.06) to extend a scene's life and keep retention; just make sure the cut out lands while something's moving. In our deterministic stages: align beat boundaries so the outgoing beat is still animating (zoom/draw) at the cut point.

---

## Picking techniques for a reel (quick guide)
- **Any reel, baseline polish:** #1 editorial background + #6-style grain + #7 cut-on-action + slow zooms. These alone lift a flat HTML reel to "editorial".
- **Document/news/AI-history:** add #4 edge boil + #5 analog photo (the newspaper format = `edge-boil-reel`).
- **"Something is revealed/built/uncovered":** #3 ink-bleed reveal.
- **Playful / collage / personal-brand:** #6 jitter on stickers + #2 texture.
- **Always:** subtlety — every effect at low strength, stacked.

## Costs
All seven are free to apply (CSS/SVG in the Playwright render). The only paid pieces are optional source assets: Higgsfield for an animated archival clip (#5), stock ink-bleed (#3), stock textures (#2, often free). No per-render cost.
