#!/usr/bin/env python3
"""Build Verse Shorts: KJV text -> Kokoro narration -> rain/voice mix -> HyperFrames project folder.

  python3 tools/verse-shorts/build.py <id> [<id> ...]     (ids from verses.json; run from repo root)

For each id it writes tools/shorts/<id>/ (index.html, assets/, fonts/, hyperframes.json) ready for
`hyperframes render`. Needs kokoro_onnx models in cwd (kokoro-v1.0.onnx, voices-v1.0.bin) and ffmpeg.
"""
import json, os, re, shutil, subprocess, sys, urllib.request
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "shorts", "psalm-4-8")
VOICE, SPEED, SR = "af_nicole", 0.82, 24000
CTA = {
    "calm": ("FOR NIGHTS THE MIND WON'T REST",
             "The whole Book of Psalms,<br />read slow for sleep.<br />8 hours &middot; ocean waves &middot; black screen<br />On the Blessed Prayers channel.",
             "The whole Book of Psalms, read slow for sleep, is on the Blessed Prayers channel."),
    "morning": ("START THE DAY IN THE WORD",
                "Start every morning in the Word.<br />The full Bible reading<br />is on the Blessed Prayers channel.",
                "Start every morning in the Word. The full Bible reading is on the Blessed Prayers channel."),
}


def kjv(book, ch, vs):
    u = f"https://raw.githubusercontent.com/aruljohn/Bible-kjv/master/{book}.json"
    d = json.load(urllib.request.urlopen(u, timeout=60))
    c = next(x for x in d["chapters"] if int(x["chapter"]) == ch)
    txt = []
    for v in vs:
        t = next(x["text"] for x in c["verses"] if int(x["verse"]) == v)
        txt.append(t.strip())
    return " ".join(txt)


def chunks(text):
    """Split into spoken phrases at sentence / colon / semicolon breaks; merge tiny ones; wrap long ones at commas."""
    parts = [p.strip() for p in re.findall(r"[^.:;?!]+[.:;?!]?", text) if p.strip()]
    out = []
    for p in parts:
        if out and len(out[-1]) < 28:
            out[-1] += " " + p
        else:
            out.append(p)
    final = []
    for p in out:
        while len(p) > 110 and "," in p[40:-30]:
            i = p.index(",", len(p) // 2 - 25 if "," in p[len(p) // 2 - 25:] else 40) + 1
            final.append(p[:i].strip()); p = p[i:].strip()
        final.append(p)
    return final


def font_size(text):
    n = len(text)
    for fs in range(92, 50, -2):
        cpl = 900 / (0.43 * fs)
        lines = -(-n // int(cpl)) + 1
        if lines * fs * 1.2 <= 740:
            return fs
    return 50


def run(cmd):
    subprocess.run(cmd, check=True)


def main(ids):
    verses = {v["id"]: v for v in json.load(open(os.path.join(HERE, "verses.json")))}
    k = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
    sil = lambda s: np.zeros(int(SR * s), dtype=np.float32)
    say = lambda t: k.create(t, voice=VOICE, speed=SPEED, lang="en-us")[0].astype(np.float32)
    tpl = open(os.path.join(HERE, "template.html")).read()
    for vid in ids:
        v = verses[vid]
        text = kjv(v["book"], v["ch"], v["v"])
        eyebrow, cta_html, cta_say = CTA[v["set"]]
        parts = [sil(1.5)]; t = 1.5; lines = []
        for ch_ in chunks(text):
            a = say(ch_); d = len(a) / SR
            show = ch_ if not lines else ch_
            lines.append({"text": show, "start": round(t, 2), "end": round(t + d, 2)})
            parts += [a, sil(0.9)]; t += d + 0.9
        lines[0]["text"] = "“" + lines[0]["text"]
        lines[-1]["text"] = lines[-1]["text"] + "”"
        verse_end = t
        parts.append(sil(0.5)); t += 0.5
        ref_t = t
        a = say(v["say"]); parts += [a, sil(0.9)]; t += len(a) / SR + 0.9
        cta_t = t
        a = say(cta_say); parts += [a, sil(3.0)]; t += len(a) / SR + 3.0
        dur = round(t, 1)
        out = os.path.join("tools", "shorts", vid)
        shutil.rmtree(out, ignore_errors=True)
        os.makedirs(os.path.join(out, "assets")); shutil.copytree(os.path.join(SRC, "fonts"), os.path.join(out, "fonts"))
        shutil.copy(os.path.join(SRC, "hyperframes.json"), out); shutil.copy(os.path.join(SRC, "meta.json"), out)
        shutil.copy(os.path.join(SRC, "assets", "gsap.min.js"), os.path.join(out, "assets"))
        voice = np.concatenate(parts)
        sf.write(f"{out}/assets/voice.wav", voice, SR)
        # rain bed (soft pink noise) under the voice, loudness-matched, gentle fade at the end
        fc = ("[0:a]aresample=44100[v];"
              f"[1:a]highpass=f=350,lowpass=f=6500,volume=0.11,tremolo=f=0.12:d=0.25[r];"
              "[v][r]amix=inputs=2:duration=first:normalize=0,"
              f"loudnorm=I=-14:TP=-1.5:LRA=7,afade=t=out:st={dur-2:.1f}:d=2")
        run(["ffmpeg", "-v", "error", "-y", "-i", f"{out}/assets/voice.wav",
             "-f", "lavfi", "-i", f"anoisesrc=d={dur+1}:c=pink:r=44100:a=0.5",
             "-filter_complex", fc, "-t", str(dur), "-ac", "2", "-c:a", "aac", "-b:a", "192k", f"{out}/assets/mix.m4a"])
        os.remove(f"{out}/assets/voice.wav")
        bg = v.get("bg")
        if bg:
            shutil.copy(os.path.join("ref", "broll", bg + ".png"), f"{out}/assets/bg.png")
        else:  # 1x1 transparent placeholder, hidden by CSS
            open(f"{out}/assets/bg.png", "wb").write(bytes.fromhex(
                "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d4944415478da6360000002000001e221bc330000000049454e44ae426082"))
        html = (tpl.replace("__DUR__", str(dur)).replace("__EYEBROW__", eyebrow).replace("__REF__", v["ref"])
               .replace("__CTA__", cta_html).replace("__LINES__", json.dumps(lines)).replace("__FS__", str(font_size(text)))
               .replace("__RAIN__", "false" if bg else "true").replace("__BGDISPLAY__", "block" if bg else "none")
               .replace("__REF_T__", str(round(ref_t, 2))).replace("__CTA_T__", str(round(cta_t, 2)))
               .replace("__FADE_T__", str(round(dur - 2.2, 2))).replace("__VERSE_END__", str(round(verse_end, 2))))
        open(f"{out}/index.html", "w").write(html)
        json.dump({"id": vid, "ref": v["ref"], "text": text, "duration": dur, "lines": lines}, open(f"{out}/info.json", "w"), indent=1)
        print(f"built {vid}: {dur}s fs={font_size(text)} :: {text[:60]}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
