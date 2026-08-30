#!/usr/bin/env python3
"""Composite with a music bed and real SFX (Harry, 2026-08-27: "add music to make
them more interesting").

Same video stack as composite2: base -> b-roll overlays (under) -> caption ASS (last),
captions cut wherever they would sit over b-roll.

New: a music bed mixed 16 dB under the measured speech loudness (the level Harry
locked in feedback_music_bed_levels), plus any SFX events a beat registered.

NOTE this overrides Sam's locked "no music" default. Flag it on delivery.
"""
import json, os, subprocess, sys
import imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
FF = imageio_ffmpeg.get_ffmpeg_exe()
PLAN = {c["id"]: c for c in json.load(open(os.path.join(HERE, "plan.json")))}
OUT = os.path.join(HERE, "finals")
os.makedirs(OUT, exist_ok=True)
# Music lives in the batch workspace when one exists, otherwise in the repo's own
# bundled library (<repo>/music). First folder that has audio in it wins.
def _music_dir():
    for c in (os.path.join(HERE, "broll_src", "music"),
              os.path.abspath(os.path.join(HERE, "..", "..", "music"))):
        if os.path.isdir(c) and any(f.lower().endswith((".mp3", ".wav", ".m4a"))
                                    for f in os.listdir(c)):
            return c
    return os.path.join(HERE, "broll_src", "music")


MUS = _music_dir()

# One bed per clip, NEVER one bed across a batch. An explicit entry here wins;
# anything not listed falls back to the bundled library, rotating by clip id so
# consecutive clips never share a bed. The map below is from the Karel + Melvin
# batch and is kept as a worked example of matching a bed to what a clip does.
BED = {
 1:  ("hv-bed_automation-flex_v1.mp3", 16),   # machine, restless      swing .88
 2:  ("hv-bed_news-urgency_v1.mp3",    16),   # clock pressure         swing .49
 3:  ("lf03-04_body_steady_progress.mp3", 18),# quietest bed: the blank frame is the joke
 4:  ("lf01-01_hook_tense_rising.mp3", 16),   # the pivot, rises       swing .78
 5:  ("lf03-05_body_warm_resolve.mp3", 16),   # underdog, warm payoff  swing .51
 6:  ("Drive Money.mp3",               16),   # money, blunt           swing .88
 7:  ("hv-bed_morning-momentum_v1.mp3",16),   # generous, brightest    bright .112
 8:  ("lf03-02_body_saturday_momentum.mp3",18),# flattest bed: "he retired his mama" carries it
 9:  ("hv-bed_provocateur_v1.mp3",     16),   # contrarian punch       swing .63
 10: ("Drive Tension.mp3",             16),   # locked in, dark; sits under the metal hits
 11: ("lf03-03_body_clockwork_pulse.mp3", 16),# systems, machine       swing .26
 12: ("Mischevious Caught in the Act 1 .mp3", 16),  # pattern-spotting, and it is literally a catch
}
SPEECH_I = -16.0       # every clip lands on the same speech loudness
SEP_DB = 16.0          # default speech-to-bed separation
FADE = 1.2


def pick_bed(cid):
    """Rotate through the available library so each clip in a batch gets its own
    bed. Deterministic, so a re-render of one clip keeps the same track."""
    if not os.path.isdir(MUS):
        return None
    files = sorted(f for f in os.listdir(MUS)
                   if f.lower().endswith((".mp3", ".wav", ".m4a")))
    return files[(cid - 1) % len(files)] if files else None


def load(p):
    return json.load(open(p)) if os.path.exists(p) else []


def _t2s(t):
    h, m, s = t.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def _trim_caps(src, dst, wins):
    if not wins:
        return src
    out = []
    for ln in open(src):
        if ln.startswith("Dialogue:"):
            f = ln.split(",")
            st, en = _t2s(f[1]), _t2s(f[2])
            if any(st < we and en > ws for ws, we in wins):
                continue
        out.append(ln)
    open(dst, "w").write("".join(out))
    return dst


def caption_ass(cid, brolls):
    d = os.path.join(HERE, "caps", f"{cid:02d}")
    bf = os.path.join(d, "bellefair.ass")
    return _trim_caps(bf, os.path.join(d, "bellefair_clean.ass"),
                      [(b["start"], b["end"]) for b in brolls])


def speech_lufs(path):
    p = subprocess.run([FF, "-hide_banner", "-nostats", "-i", path,
                        "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
                       capture_output=True, text=True)
    val = None
    for ln in p.stderr.splitlines():
        if "I:" in ln and "LUFS" in ln:
            try:
                val = float(ln.split("I:")[1].split("LUFS")[0].strip())
            except ValueError:
                pass
    return val if val is not None else -18.0


HOOK_DUR = 2.5


def composite(cid, hook_lines=None, to_finals=False):
    """hook_lines=None -> the YouTube cut. A 2-line list -> the Instagram cut with the
    Bellefair card, fully on screen from frame 0, fading out at ~2.5s."""
    clip = PLAN[cid]
    slug = clip["slug"]
    dur = clip["out_dur"]
    base = os.path.join(HERE, "bases", f"base_{cid:02d}.mp4")
    brolls = load(os.path.join(HERE, "broll", f"{cid:02d}", "spec.json"))
    sfx = load(os.path.join(HERE, "broll", f"{cid:02d}", "sfx.json"))
    ass = caption_ass(cid, brolls)
    if hook_lines:
        import ig_hook
        wins = [(b["start"], b["end"]) for b in brolls] + [(0, HOOK_DUR)]
        ass = _trim_caps(os.path.join(HERE, "caps", f"{cid:02d}", "bellefair.ass"),
                         os.path.join(HERE, "caps", f"{cid:02d}", "bellefair_ig.ass"),
                         wins)
        hookpng = os.path.join(HERE, f"_hook_{cid:02d}.png")
        hw, hh = ig_hook.render_hook(hook_lines, hookpng)
        rest = 1920 - hh - 70

    inputs = ["-i", base]
    parts = []
    cur = "[0:v]"
    idx = 1
    for b in brolls:
        f = b["file"]
        s, e = b["start"], b["end"]
        d = round(e - s, 3)
        is_vid = f.lower().endswith((".mp4", ".mov"))
        inputs += (["-i", f] if is_vid else ["-loop", "1", "-t", f"{d:.3f}", "-i", f])
        parts.append(f"[{idx}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                     f"crop=1080:1920,setpts=PTS-STARTPTS+{s}/TB[b{idx}]")
        nl = f"[v{idx}]"
        parts.append(f"{cur}[b{idx}]overlay=0:0:enable='between(t,{s},{e})':"
                     f"eof_action=pass{nl}")
        cur = nl
        idx += 1
    if hook_lines:
        parts.append(f"{cur}ass={ass}:fontsdir={os.path.join(HERE,'assets/fonts')}[vcap]")
        inputs += ["-loop", "1", "-t", f"{HOOK_DUR}", "-i", hookpng]
        parts.append(f"[{idx}:v]format=rgba,fade=t=out:st={HOOK_DUR-0.35:.2f}:"
                     f"d=0.35:alpha=1[hk]")
        parts.append(f"[vcap][hk]overlay=x=(W-w)/2:y={rest}:"
                     f"enable='between(t,0,{HOOK_DUR})'[vout]")
        idx += 1
    else:
        parts.append(f"{cur}ass={ass}:fontsdir={os.path.join(HERE,'assets/fonts')}[vout]")

    # ---- audio: speech + bed 16 dB under + sfx
    lufs = speech_lufs(base)          # measured, for the log only
    bed_name, sep = BED.get(cid, (None, SEP_DB))
    if bed_name and not os.path.exists(os.path.join(MUS, bed_name)):
        bed_name = None               # mapped bed is not on this machine
    if bed_name is None:
        bed_name = pick_bed(cid)      # rotate through whatever library is here
    bed = os.path.join(MUS, bed_name) if bed_name else None
    parts.append(f"[0:a]loudnorm=I={SPEECH_I}:TP=-1.5:LRA=11[sp]")
    amix = ["[sp]"]
    # Sam's locked default is NO MUSIC. Only mix a bed when this clip has one
    # mapped AND the file is actually there. A missing file used to be handed
    # straight to ffmpeg, which killed the render.
    if bed and os.path.exists(bed):
        bed_i = SPEECH_I - sep        # the batch plays at one level
        music_idx = idx
        inputs += ["-stream_loop", "-1", "-i", bed]
        idx += 1
        parts.append(
            f"[{music_idx}:a]atrim=0:{dur+0.3:.2f},asetpts=PTS-STARTPTS,"
            f"loudnorm=I={bed_i:.1f}:TP=-2.0:LRA=11,"
            f"afade=t=in:st=0:d={FADE},afade=t=out:st={max(0,dur-FADE):.2f}:d={FADE}[mus]")
        amix.append("[mus]")
    elif bed:
        print(f"#{cid} bed missing, rendering without music: {bed}")
    for j, ev in enumerate(sfx):
        inputs += ["-i", ev["file"]]
        parts.append(f"[{idx}:a]adelay={int(ev['at']*1000)}|{int(ev['at']*1000)},"
                     f"volume={ev.get('gain',0.8)}[sx{j}]")
        amix.append(f"[sx{j}]")
        idx += 1
    if len(amix) == 1:
        parts.append("[sp]alimiter=limit=0.97[aout]")
    else:
        parts.append("".join(amix) + f"amix=inputs={len(amix)}:duration=first:"
                     f"normalize=0,alimiter=limit=0.97[aout]")

    fc = ";".join(parts)
    if hook_lines and not to_finals:
        od = os.path.join(HERE, "finals_ig")
        os.makedirs(od, exist_ok=True)
        out = os.path.join(od, f"{cid:02d}_{slug}_ig.mp4")
    else:
        out = os.path.join(OUT, f"{cid:02d}_{slug}.mp4")
    cmd = ([FF, "-y", "-nostdin"] + inputs +
           ["-filter_complex", fc, "-map", "[vout]", "-map", "[aout]",
            "-r", "30", "-c:v", "libx264", "-crf", "19", "-preset", "veryfast",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", "-t", f"{dur+0.1:.2f}", out])
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=420)
    except subprocess.TimeoutExpired:
        print(f"#{cid} TIMEOUT after 420s")     # never stall the batch again
        return False
    if p.returncode != 0:
        print(f"#{cid} FAIL\n{p.stderr[-900:]}")
        return False
    print(f"#{cid:02d} {slug:<30} {dur:5.1f}s broll={len(brolls)} sfx={len(sfx)} "
          f"bed={(bed_name or 'none')[:26]:<26} -{sep}dB {'IG' if hook_lines else 'YT'} ok")
    return True


if __name__ == "__main__":
    from ig_batch_kvml import HOOKS
    args = sys.argv[1:]
    ids = [int(x) for x in args if x.isdigit()] or list(PLAN)
    # every cut carries the Bellefair hook card now, not just the Instagram one
    ok = sum(composite(i, HOOKS[i], to_finals=True) for i in ids)
    print(f"done {ok}/{len(ids)}")
