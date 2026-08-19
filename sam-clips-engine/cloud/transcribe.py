"""Extract audio from source.mp4 and transcribe with ElevenLabs Scribe (diarized, word-level).

Single Scribe call so diarization speaker labels stay consistent across the whole
interview. Writes:
  source.words.json   -- raw word list [{text,start,end,type,speaker_id}]
  source.packed.txt   -- readable [mm:ss] SPEAKER: text, grouped into turns
"""
import os, sys, json, subprocess
import requests
import imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r2_helper as R
R.load_r2_env()

FF = imageio_ffmpeg.get_ffmpeg_exe()
SRC = os.path.join(HERE, "source.mp4")
MP3 = os.path.join(HERE, "source.mp3")
WORDS = os.path.join(HERE, "source.words.json")
PACKED = os.path.join(HERE, "source.packed.txt")


def extract():
    if os.path.exists(MP3) and os.path.getsize(MP3) > 0:
        print(f"[ff] reuse {MP3} ({os.path.getsize(MP3)/1e6:.1f}MB)", flush=True)
        return
    print("[ff] extracting mono 16k mp3...", flush=True)
    p = subprocess.run([FF, "-y", "-i", SRC, "-vn", "-ac", "1", "-ar", "16000",
                        "-b:a", "48k", MP3], capture_output=True, text=True)
    # parse duration from stderr
    for line in p.stderr.splitlines():
        if "Duration:" in line:
            print("[ff]", line.strip(), flush=True)
            break
    if p.returncode != 0:
        print(p.stderr[-1500:]); sys.exit("ffmpeg failed")
    print(f"[ff] mp3 {os.path.getsize(MP3)/1e6:.1f}MB", flush=True)


def scribe():
    key = os.environ["ELEVENLABS_API_KEY"]
    print("[scribe] uploading (single diarized call)...", flush=True)
    with open(MP3, "rb") as fh:
        r = requests.post(
            "https://api.elevenlabs.io/v1/speech-to-text",
            headers={"xi-api-key": key},
            data={"model_id": "scribe_v1", "timestamps_granularity": "word",
                  "diarize": "true"},
            files={"file": (os.path.basename(MP3), fh, "audio/mpeg")},
            timeout=3000,
        )
    if r.status_code != 200:
        sys.exit(f"[scribe] {r.status_code}: {r.text[:800]}")
    j = r.json()
    words = [{"text": w.get("text", ""), "start": w.get("start"),
              "end": w.get("end"), "type": w.get("type", "word"),
              "speaker_id": w.get("speaker_id")} for w in j.get("words", [])]
    json.dump({"text": j.get("text", ""), "words": words}, open(WORDS, "w"))
    spoken = [w for w in words if w["type"] == "word"]
    dur = spoken[-1]["end"] if spoken else 0
    print(f"[scribe] {len(spoken)} words, dur ~{dur/60:.1f}min", flush=True)
    return words


def pack(words):
    def ts(s):
        s = int(s or 0); return f"{s//60:02d}:{s%60:02d}"
    turns, cur = [], None
    for w in words:
        if w["type"] != "word":
            continue
        spk = w.get("speaker_id") or "?"
        if cur is None or cur["spk"] != spk:
            cur = {"spk": spk, "start": w["start"], "words": []}
            turns.append(cur)
        cur["words"].append(w["text"])
    lines = []
    for t in turns:
        txt = " ".join(t["words"]).replace("  ", " ").strip()
        lines.append(f"[{ts(t['start'])}] {t['spk']}: {txt}")
    open(PACKED, "w").write("\n".join(lines))
    print(f"[pack] {len(turns)} turns -> {PACKED}", flush=True)


if __name__ == "__main__":
    extract()
    words = scribe()
    pack(words)
    print("DONE", flush=True)
