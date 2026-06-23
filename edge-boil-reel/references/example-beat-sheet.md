# Example beat sheet — "The NYT said AI was conscious — in 1958"

A worked example to pattern-match when you write your own. ~32s edge-boil reel built around a **real** historic newspaper, paired with a current headline. Use it as a shape, not a script to reshoot.

## The story (verified, real sources)

On **8 July 1958** the New York Times ran **"NEW NAVY DEVICE LEARNS BY DOING"** — coverage of Frank Rosenblatt's Perceptron press conference. The quotable line:

> "The Navy revealed the embryo of an electronic computer today that it expects will be able to **walk, talk, see, write, reproduce itself and be conscious of its existence**."

The actual machine — the Mark I Perceptron — was 400 photocells that, after ~50 training trials, could tell left-oriented shapes from right. It IS a neural network, the direct ancestor of today's models. The hype collapsed, funding died (the AI winters), and then everything in that sentence happened anyway — ~60 years late.

## Why this shape works

- **Pairs a real primary source with a current headline** — old + new, same claim, decades apart. The annotations let you literally point at the parallel.
- **Pays off with a takeaway**, not just trivia: *hype is a terrible timer but a decent compass — bet on the direction, not the deadline.*

## Beat sheet (~30s)

| Beat | Time | Visual | Annotation + text |
|---|---|---|---|
| Hook | 0–3s | Vintage NYT page scan on kraft paper, slow push-in | Big white text: "Think the AGI hype is new? Read this 1958 paper." Red circle boils on around the headline |
| 2 | 3–10s | Zoom to headline "NEW NAVY DEVICE LEARNS BY DOING" | Blue circle on "LEARNS BY DOING"; white arrow + handwritten "this is a neural network — in 1958" |
| 3 | 10–17s | Pan down to the body text | Boiling marker underline draws across "walk, talk, see, write, reproduce itself and be conscious of its existence". Stamp: "VERBATIM · 1958" |
| 4 | 17–23s | Cut to the Mark I Perceptron photo (animated, optional) | Red scribble over the machine; handwritten "it could tell left from right. that's it." |
| 5 | 23–28s | Split: 1958 headline circled blue / current headline circled red | Stamp: "68 YEARS APART" |
| Payoff | 28–32s | Pull back to a clean card | "Hype is a terrible timer. But a decent compass." + handle |

Annotation palette: blue circles, red scribbles, white arrows; trim-path draw-on + seed-stepped edge boil.

## VO script (≈90 words ≈ 32s)

| Beat | Time | VO | Visual |
|---|---|---|---|
| 1 | 0–5s | "Everyone's saying it this week. AGI is here." | This week's real headline screenshots, boiling red circle |
| 2 | 5–10s | "Right. Have a read of this. July 1958. The New York Times." | Cut to 1958 NYT page on kraft, push-in, blue circle on headline |
| 3 | 10–17s | "A Navy machine that will walk, talk, see, write… and be conscious of its existence." | Marker underline boils across the quote |
| 4 | 17–22s | "The actual machine? 400 photocells. It could tell left from right." | Red scribble over the Mark I Perceptron photo |
| 5 | 22–27s | "Funding collapsed. Everyone laughed. Then every word came true. 60 years late." | Split: 1958 circled blue / today circled red |
| 6 | 27–32s | "So the hype's usually right. It's the timing that's wrong. Bet on the direction, not the deadline." | Pull back to full page, end card |

25s cut: drop "Funding collapsed. Everyone laughed." from beat 5.

## Sourcing notes (real assets only)

- **NYT, 8 July 1958** — the genuine clipping (headline + quote paragraph) is reproduced in many Perceptron retrospectives (e.g. Cornell histories). Beats 2–3 are close-ups, so the article block is all that's on screen.
- **Mark I Perceptron photo** — Cornell University / Smithsonian images, widely reproduced and public-domain-ish; pull from Wikimedia Commons.
- **Modern headline** — screenshot the real current article page with `template/crops.py` / `template/shots.py`. Never mock one up.
