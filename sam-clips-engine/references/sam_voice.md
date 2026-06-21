# Sam's Spoken Voice — Style Reference

> **STATUS: STUB — needs Sam's voice memos to populate.**
> This profile makes the ranker pick lines Sam himself would find interesting, and
> keeps any written copy (hooks, CTAs) sounding like him. Until it's filled in, the
> ranker falls back to the hook patterns in `sam_audience.md`.

## How to populate this file (one-time, ~10 min)

1. Collect the voice memos / past videos Sam sent. Drop them anywhere and note the path.
2. Transcribe each with Scribe (same engine the pipeline uses — never Whisper):
   ```bash
   for f in /path/to/memos/*; do
     python3 ~/.claude/skills/video-use/helpers/transcribe.py "$f" --edit-dir /tmp/sam_voice
   done
   ```
3. Read the transcripts and distill them into the sections below — replace every
   `<fill>`. Pull **real phrases Sam uses verbatim** (these are gold for hooks).
4. Delete this "How to populate" block and the STUB banner once done.

## Cadence & sentence shape
- <fill: short punchy sentences? long winding ones? where does he pause?>

## Words & phrases he actually uses (verbatim)
- <fill: signature phrases, e.g. "here's the thing", "nobody tells you this">
- <fill: words to AVOID — anything that doesn't sound like him>

## What Sam finds interesting / gets animated about
- <fill: the topics where his energy jumps — these make the best clips>

## How he opens a strong point (hook DNA)
- <fill: 5-10 real opening lines from the memos>

## How he closes / his natural CTA style
- <fill: how he tells people to take the next step, in his words>

## Tone guardrails
- <fill: e.g. confident not arrogant, mechanical not woo, warm not salesy>
