#!/usr/bin/env python3
"""Build one Psalm-91-look verse card (1080x1920, 30 fps, H.264 + AAC).

Look comes from Lumi's recipe (from-lumi_psalm91-build-recipe.txt, L-066, Nov 1 2026):
  - sharp 1080x800 band (y=560..1360) over a blurred, darkened copy of the same picture
  - ONE text layer per text: gold title, cream verse captions, gold Subscribe end card, all burned with ASS only (C-012 fix)
  - DejaVu Sans Bold: Default 52 cream #FFF0E6, Title 72 gold #FFE696, End 64 gold; outline 4, shadow 2, margins as in the recipe
Narration: locked Voice 6 unit wavs (tools/verse-voice), one wav per caption line + one for the reference.

usage: build_card.py CARD_NO CLIP.mp4 VOICE_DIR OUT.mp4 [--workdir DIR] [--fgx PIXELS]
"""
import argparse, json, os, subprocess, sys, wave
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 44100
LEAD, GAP, REF_GAP, END_GAP, END_LEN = 1.0, 0.45, 0.85, 0.7, 3.3
TITLE_LEN = 2.4
MAXSLOW = 1.8


def run(cmd):
    print("+", " ".join(cmd if isinstance(cmd, list) else [cmd]), flush=True)
    subprocess.run(cmd, check=True)


def probe_dur(p):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p])
    return float(out.decode().strip())


def ts(t):
    h = int(t // 3600); m = int((t % 3600) // 60); s = t - h * 3600 - m * 60
    return f"{h}:{m:02d}:{s:05.2f}"


def ass_escape(s):
    return s.replace("\\", "\\\\").replace("{", "(").replace("}", ")")


def pad_bed(path, dur, kind, seed):
    """Soft synthesized warm pad (original, royalty free). Stereo, 44.1k."""
    rng = np.random.default_rng(seed)
    n = int(SR * (dur + 0.5)); t = np.arange(n) / SR
    notes = {"morning": [146.83, 220.00, 293.66, 369.99, 440.00],   # D3 A3 D4 F#4 A4
             "calm": [110.00, 164.81, 220.00, 277.18, 329.63]}[kind]  # A2 E3 A3 C#4 E4
    L = np.zeros(n); R = np.zeros(n)
    for i, f in enumerate(notes):
        for det, pan in ((-0.0035, 0.35), (0.0035, 0.65)):
            ff = f * (1 + det)
            lfo = 0.55 + 0.45 * np.sin(2 * np.pi * (0.05 + 0.013 * i) * t + rng.uniform(0, 6.28))
            w = np.sin(2 * np.pi * ff * t) + 0.25 * np.sin(2 * np.pi * 2 * ff * t) + 0.08 * np.sin(2 * np.pi * 3 * ff * t)
            w = w * lfo / (1 + 0.3 * i)
            L += w * (1 - pan); R += w * pan
    a = np.stack([L, R], 1)
    a /= np.abs(a).max() + 1e-9
    a *= 0.5
    fi, fo = int(SR * 1.2), int(SR * 1.5)
    env = np.ones(n); env[:fi] = np.linspace(0, 1, fi); env[-fo:] = np.linspace(1, 0, fo)
    sf.write(path, (a * env[:, None]).astype(np.float32), SR)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("card", type=int); ap.add_argument("clip"); ap.add_argument("voice_dir"); ap.add_argument("out")
    ap.add_argument("--workdir", default=None); ap.add_argument("--fgx", type=int, default=0, help="shift of the sharp band crop, pixels")
    ap.add_argument("--clip2", default=None, help="optional second clip, crossfaded after the first")
    a = ap.parse_args()
    cards = {c["card"]: c for c in json.load(open(os.path.join(HERE, "cards.json")))}
    c = cards[a.card]
    wd = a.workdir or f"/tmp/p91card{a.card}"; os.makedirs(wd, exist_ok=True)

    # ---- voice timeline ----
    t = LEAD; segs = []; clips = []
    for j, line in enumerate(c["lines"]):
        w, sr = sf.read(os.path.join(a.voice_dir, f"u{a.card*10+j:03d}.wav"), dtype="float32")
        if w.ndim > 1: w = w.mean(1)
        d = len(w) / sr
        segs.append((t, t + d, line)); clips.append((t, w, sr)); t += d + GAP
    t = t - GAP + REF_GAP
    w, sr = sf.read(os.path.join(a.voice_dir, f"u{a.card*10+9:03d}.wav"), dtype="float32")
    if w.ndim > 1: w = w.mean(1)
    ref_start, ref_end = t, t + len(w) / sr
    clips.append((t, w, sr))
    end_start = ref_end + END_GAP
    total = end_start + END_LEN
    print(f"card {a.card}: narration ends {ref_end:.2f}s, total {total:.2f}s", flush=True)

    # ---- audio: voice (mono -> stereo) + soft pad, one loudnorm pass ----
    import scipy.signal as ss
    n = int(SR * total) + SR
    voice = np.zeros(n, dtype=np.float32)
    for st, w, sr in clips:
        if sr != SR:
            w = ss.resample_poly(w, SR, sr).astype(np.float32)
        w = w / (np.abs(w).max() + 1e-9) * 0.9
        i0 = int(st * SR); voice[i0:i0 + len(w)] += w[: max(0, n - i0)]
    padp = os.path.join(wd, "pad.wav"); pad_bed(padp, total, c["set"], a.card)
    pad, _ = sf.read(padp, dtype="float32")
    mix = np.zeros((n, 2), dtype=np.float32)
    mix[:, 0] += voice; mix[:, 1] += voice
    m = min(n, len(pad)); mix[:m] += pad[:m] * 0.07   # pad about 23 dB under the voice
    mixp = os.path.join(wd, "mix.wav"); sf.write(mixp, mix[: int(SR * total)], SR)

    # ---- motion: slow the clip to fit (max 1.35x), ping-pong if it still falls short ----
    def prep(path, k):
        d = probe_dur(path)
        slow = min(MAXSLOW, max(1.0, total / d))
        out = os.path.join(wd, f"m{k}.mp4")
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-map", "0:v:0", "-an",
             "-vf", f"setpts={slow:.4f}*PTS,framerate=fps=30,scale=1920:-2:flags=lanczos,format=yuv420p",
             "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "16", out])
        return out, d * slow
    m1, d1 = prep(a.clip, 1)
    seg = m1; segd = d1
    if a.clip2:
        m2, d2 = prep(a.clip2, 2)
        xf = 0.7
        both = os.path.join(wd, "both.mp4")
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", m1, "-i", m2, "-filter_complex",
             f"[0:v][1:v]xfade=transition=fade:duration={xf}:offset={d1 - xf:.3f},format=yuv420p[v]", "-map", "[v]",
             "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "16", both])
        seg = both; segd = d1 + d2 - xf
    motion = os.path.join(wd, "motion.mp4")
    if segd >= total:
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", seg, "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "fast", "-crf", "16", motion])
    else:  # forward + reverse until long enough
        rev = os.path.join(wd, "rev.mp4")
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", seg, "-vf", "reverse", "-c:v", "libx264", "-preset", "fast", "-crf", "16", rev])
        lst = os.path.join(wd, "pp.txt")
        reps = int(total // segd) + 2
        with open(lst, "w") as f:
            for r in range(reps):
                f.write(f"file '{seg if r % 2 == 0 else rev}'\n")
        run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-t", f"{total:.3f}",
             "-c:v", "libx264", "-preset", "fast", "-crf", "16", motion])

    # ---- captions: ONE ASS file, the only text layer ----
    A = ["[Script Info]", f"Title: {c['ref']}", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 0", "",
         "[V4+ Styles]",
         "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
         "Style: Default,DejaVu Sans,52,&H00E6F0FF,&H000000FF,&H80000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,50,50,220,1",
         "Style: Title,DejaVu Sans,72,&H0096E6FF,&H000000FF,&H80000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,50,50,900,1",
         "Style: End,DejaVu Sans,64,&H0096E6FF,&H000000FF,&H80000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,50,50,900,1",
         "Style: Ref,DejaVu Sans,56,&H0096E6FF,&H000000FF,&H80000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,50,50,220,1",
         "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    A.append(f"Dialogue: 0,{ts(0)},{ts(TITLE_LEN)},Title,,0,0,0,,{{\\fad(250,300)}}{ass_escape(c['ref'])}\\N{ass_escape(c['title2'])}")
    for k, (s, e, line) in enumerate(segs):
        end = segs[k + 1][0] if k + 1 < len(segs) else ref_start
        A.append(f"Dialogue: 0,{ts(max(s - 0.1, 0))},{ts(end - 0.05)},Default,,0,0,0,,{ass_escape(line)}")
    A.append(f"Dialogue: 0,{ts(ref_start - 0.1)},{ts(end_start - 0.05)},Ref,,0,0,0,,{ass_escape(c['ref'].title().replace('Lord','LORD'))}")
    A.append(f"Dialogue: 0,{ts(end_start)},{ts(total)},End,,0,0,0,,{{\\fad(500,0)}}Subscribe\\NBlessed Prayers")
    assp = os.path.join(wd, "captions.ass"); open(assp, "w").write("\n".join(A) + "\n")

    # ---- final: band over blurred copy, ASS, audio ----
    fg_x = f"(iw-1080)/2+{a.fgx}"
    fc = (f"[0:v]split[a][b];"
          f"[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=40:2,eq=brightness=-0.15[bg];"
          f"[b]scale=-2:800,crop=1080:800:{fg_x}:0[fg];"
          f"[bg][fg]overlay=0:560,ass={assp},format=yuv420p[v];"
          f"[1:a]afade=t=in:st=0:d=0.8,afade=t=out:st={total-1.2:.2f}:d=1.2,loudnorm=I=-15.5:TP=-1.5:LRA=11[aud]")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", motion, "-i", mixp, "-filter_complex", fc, "-map", "[v]", "-map", "[aud]",
         "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", "30",
         "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2", "-movflags", "+faststart", a.out])
    print("wrote", a.out, round(os.path.getsize(a.out) / 1e6, 1), "MB", flush=True)
    json.dump(dict(card=a.card, total=total, ref_start=ref_start, ref_end=ref_end, end_start=end_start), open(os.path.join(wd, "timeline.json"), "w"))


if __name__ == "__main__":
    main()
