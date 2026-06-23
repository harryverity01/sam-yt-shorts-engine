# Vox-style "Edge Boil" newspaper annotation reel — technique breakdown

Source reel: https://www.instagram.com/reel/DZdCD2YNk4d/ by Chris Moran (@chrismoran__), 48s, ~5.3k likes.
Caption: "How Vox gets those subtle animated lines on their callouts. I've got a full YouTube video out on techniques like this if you wanna check it out"
Saved 2026-06-12. Key frames in `key-frames/` (1 fps extracts; full 49-frame set was in `frames/` during the session).

## What the reel looks like (the format we want to copy)

- A **real vintage newspaper front page** (he uses the NYT, 9 March 1971 — "Frazier Outpoints Ali and Keeps Title") laid on a textured kraft-brown paper background, slightly rotated, with a drop shadow.
- The camera **pushes in and pans** across the page (slow Ken Burns moves between zoom levels — full page → headline close-up → photo close-up).
- **Hand-drawn annotations animate on top**: a blue marker circle around a word in the headline, a white curved arrow pointing at a detail, red marker scribble strokes over the photo subject, underlines. They draw on (trim paths) and then **keep wobbling** ("edge boil") instead of sitting static.
- Big white sans-serif hook text over the page ("Look at this Vox animation").
- B&W archival photo moments get a colour-pop treatment (red scribble over greyscale Ali).
- Captions: small white-on-black pill captions, word-by-word.

## Why it works (his explanation, from the VO)

Old animation was drawn frame by frame, so every line differed slightly between frames — shapes naturally wiggled. "Edge boil" recreates that imperfect hand-drawn life. Take the wobble away and the annotation feels dead/digital.

## Full voiceover transcript

> Look at this Vox animation. See it? Not Muhammad Ali. The subtle moving lines making it feel alive. Take it away, and the whole thing feels a little lifeless. It's called edge boil, and it's one of the easiest ways to make your animation feel crafted. Back before modern software, artists drew everything frame by frame. Every line was slightly different, so shapes would naturally wiggle and shift from frame to frame. In After Effects, animate your lines using trim paths. Then add two effects. First, roughen edges. Set the border size to roughly half your stroke width. Then add a turbulent displace effect with an amount of 80 and a size of two. This creates that hand drawn look. Next, Alt click the random seed property and type "time times four". Instantly, the lines start to move. If you want even more movement, duplicate the turbulent displace, increase the size, and lower the amount. And now...

## The exact After Effects recipe (as shown on screen)

1. Draw the annotation as a **shape layer stroke** (ellipse around the word, pen-tool arrow, scribble path). Thick round-cap stroke; blue/red/white marker colours.
2. Animate the draw-on with **Trim Paths** (shape layer > Add > Trim Paths, keyframe End 0→100%).
3. Effect 1 — **Roughen Edges**: border ≈ **half the stroke width** (e.g. 13px stroke → border ~6).
4. Effect 2 — **Turbulent Displace**: Amount **80**, Size **2**, Complexity 1, Pinning "Pin All", Antialiasing Low. This crunches the line into a hand-drawn texture.
5. **Alt-click the Random Seed** stopwatch on Turbulent Displace and add the expression `time*4` → seed re-randomises ~4x/second = the boil. (Classic boil is 3–6 fps; 4 is his pick.)
6. Optional, more wobble: **duplicate Turbulent Displace** ("Turbulent Displace 2"), **increase Size** (he uses ~19), **lower Amount**, same `time*4` seed expression — large slow warp on top of fine boil.

## Replicating WITHOUT After Effects (our cloud stack)

For HTML+SVG builds rendered headless via Playwright (this skill's pipeline), the same look is:

- Annotation = SVG `<path>` with `stroke-linecap="round"`, thick stroke.
- Draw-on = `stroke-dasharray`/`stroke-dashoffset` animation (trim paths equivalent).
- Edge boil = SVG filter: `<feTurbulence baseFrequency="0.05" numOctaves="2" seed="X"/>` + `<feDisplacementMap scale="6-10"/>`, and **step the `seed` attribute 3–4 times per second** (not continuously — the discrete jump is what reads as hand-drawn boil). Two stacked turbulence/displacement pairs (fine + coarse) match his double Turbulent Displace.
- Newspaper: high-res scan, subtle sepia/contrast grade, kraft-paper backdrop, GSAP Ken Burns push-ins between annotation beats.

Alternative for the photo/scan beat: **Higgsfield** image-to-video can animate the push-in (upload the scan via the MCP `media_upload` → `media_confirm` route, then image-to-video); annotations composite over the resulting frames in the stage. Optional — a static Ken-Burns push works without it.

## Beat structure of his 48s reel (useful as a template)

- 0–3s hook: full newspaper + "Look at this" + arrow drawing toward the detail
- 3–8s: zoom to the proof (boiling circle/scribble), "see it? not X — the moving lines"
- 8–12s: name the technique (title card: "Edge Boil", graph-paper background covered in boiling doodles)
- 12–20s: the why (archival frame-by-frame animation clips, Mickey Mouse footage)
- 20–42s: the how (screen-recorded AE steps, each step one short caption)
- 42–48s: payoff — return to the finished newspaper animation

## Sourcing real scans

Build each reel around a **real scanned front page** or article. Good public-domain / free scan sources: Library of Congress "Chronicling America", Gateway to Oklahoma History, Wikimedia Commons. Screenshot real modern article pages with `template/shots.py` / `template/crops.py` — never mock up a fake clipping.
