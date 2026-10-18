#!/usr/bin/env python3
"""Morning Word stitcher: clips + script -> ONE captioned MP4 at the Derrick stitching standard.

Modes
  transcribe  words.json from every clip's audio (faster-whisper, word timestamps)
  gate        compare words.json to the script; write STATUS.txt; exit 3 on a failed clip
  build       cut, punch-in, mix, -14 LUFS, burn captions; write the final MP4 + extras

Standard (memory /topics/derrick-stitching-standard.md):
  trim to speech (~150 ms lead, ~250 ms tail), ~400 ms breath between clips (~750 ms after
  amen / a flagged line), hard cuts with alternating ~110% punch-in, 20 ms audio fades at
  every edge, one loudness pass (-14 LUFS), captions in short phrases (4 words or fewer).

Inputs
  clips/clipNN.mp4          numbered; sorted numerically so they never stitch out of order
  audio/clipNN.wav          optional processed audio (voice-converted / enhanced); same timing as the clip
  script.json               {"lines":[{"text":"...","display":"optional caption text","pause":0.4}, ...]}
                            line i belongs to the i-th clip
"""
import argparse, difflib, json, math, os, re, subprocess, sys
import numpy as np

FPS = 30
SR = 48000
LEAD, TAIL = 0.15, 0.25
GAP, GAP_LONG = 0.40, 0.75
PUNCH = 1.10
W_, H_ = 720, 1280
FAIL_EXIT = 3


def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        print("CMD FAILED:\n", cmd, "\n", r.stderr[-3000:])
        sys.exit(1)
    return r.stdout


def dur(path):
    return float(run(f'ffprobe -v error -show_entries format=duration -of csv=p=0 "{path}"'))


def clip_files(clips_dir):
    items = []
    for f in os.listdir(clips_dir):
        m = re.fullmatch(r"clip0*(\d+)\.mp4", f, re.I)
        if m:
            items.append((int(m.group(1)), os.path.join(clips_dir, f)))
    items.sort()
    return items


def load_script(path):
    lines = json.load(open(path))["lines"]
    for ln in lines:
        ln.setdefault("display", ln["text"])
    return lines


def audio_source(clip_path, audio_dir):
    stem = os.path.splitext(os.path.basename(clip_path))[0]
    if audio_dir:
        for ext in ("wav", "flac", "mp3"):
            p = os.path.join(audio_dir, f"{stem}.{ext}")
            if os.path.exists(p):
                return p
    return clip_path


# ---------------------------------------------------------------- transcribe
def cmd_transcribe(a):
    from faster_whisper import WhisperModel
    model = WhisperModel("small.en", device="cpu", compute_type="int8")
    out = {}
    for n, clip in clip_files(a.clips):
        src = audio_source(clip, a.audio)
        segs, _ = model.transcribe(src, word_timestamps=True, vad_filter=False)
        segs = list(segs)
        words = [{"text": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
                 for s in segs for w in (s.words or [])]
        heard = " ".join(s.text.strip() for s in segs).strip()
        out[str(n)] = {"words": words, "text": heard or " ".join(w["text"] for w in words)}
        print(f"clip {n}: {out[str(n)]['text']}")
    json.dump(out, open(a.words, "w"))


# ---------------------------------------------------------------- gate
def norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower().replace("’", "'"))


def tokens(text):
    return [t for t in (norm(x) for x in text.split()) if t]


def check_clip(expected_text, words, heard=""):
    """Returns (level, message). level: ok | warn | fail."""
    exp = tokens(expected_text)
    got = [t for t in (norm(w["text"]) for w in words) if t]
    if not got:
        if heard.strip():
            return "fail", f"no word timings came back (heard: '{heard.strip()[:80]}')"
        return "fail", "no speech found in this clip"
    ratio = difflib.SequenceMatcher(None, exp, got).ratio()
    first_ok = exp[0] in got[:2]
    last_ok = exp[-1] in got[-2:]
    if not first_ok:
        return "fail", f"first word missing (expected '{exp[0]}', heard '{' '.join(got[:3])}')"
    if not last_ok:
        return "fail", f"last word missing (expected '{exp[-1]}', heard '...{' '.join(got[-3:])}')"
    if ratio < 0.72:
        missing = [t for t in exp if t not in got][:4]
        return "fail", f"wrong words (match {ratio:.0%}; missing: {' '.join(missing) or 'none'})"
    if ratio < 0.88:
        missing = [t for t in exp if t not in got][:4]
        return "warn", f"check by ear (match {ratio:.0%}; missing: {' '.join(missing) or 'none'})"
    return "ok", f"match {ratio:.0%}"


def cmd_gate(a):
    lines = load_script(a.script)
    clips = clip_files(a.clips)
    words = json.load(open(a.words))
    status, fails, warns = [], [], []
    if len(clips) != len(lines):
        fails.append(f"Count: {len(clips)} clips attached but the script has {len(lines)} lines. "
                     f"Attach exactly one clip per line (clip01.mp4, clip02.mp4, ...).")
    for i, (n, _) in enumerate(clips):
        if i >= len(lines):
            break
        entry = words.get(str(n), {})
        level, msg = check_clip(lines[i]["text"], entry.get("words", []), entry.get("text", ""))
        label = f"Clip {n:02d}"
        status.append(f"{label}: {level.upper()} - {msg}")
        if level == "fail":
            fails.append(f"{label}: {msg}. Regenerate this one only.")
        elif level == "warn":
            warns.append(f"{label}: {msg}")
    head = "FAILED" if fails else ("PASSED WITH CHECKS" if warns else "PASSED")
    out = [f"GATE {head}"]
    out += fails + warns
    out += ["", "Per clip:"] + status
    open(a.status, "w").write("\n".join(out) + "\n")
    print("\n".join(out))
    if fails and not a.force:
        sys.exit(FAIL_EXIT)


# ---------------------------------------------------------------- build helpers
def speech_bounds(words, clip_dur):
    ws = [w for w in words if norm(w["text"])]
    if not ws:
        return 0.0, min(clip_dur, 6.0)
    a = max(0.0, ws[0]["start"] - LEAD)
    b = min(clip_dur - 0.05, ws[-1]["end"] + TAIL)
    return a, max(b, a + 0.5)


def gap_after(line, idx, last):
    if last:
        return 0.0
    if "pause" in line:
        return float(line["pause"])
    if re.search(r"\bamen\W*$", line["text"].strip(), re.I):
        return GAP_LONG
    return GAP


def load_pcm(path, ss, to):
    c = (f'ffmpeg -v error -ss {ss:.3f} -to {to:.3f} -i "{path}" -vn -ac 1 -ar {SR} '
         f'-af "highpass=f=80" -f f32le -')
    return np.frombuffer(subprocess.run(c, shell=True, capture_output=True).stdout, np.float32).astype(np.float64)


def speech_rms(x):
    fr = 480
    n = len(x) // fr
    if n == 0:
        return 1e-6
    e = np.sqrt((x[:n * fr].reshape(n, fr) ** 2).mean(1) + 1e-12)
    act = e > e.max() * 10 ** (-22 / 20)
    return float(np.sqrt((x[:n * fr].reshape(n, fr)[act] ** 2).mean()))


def phrases_for(display):
    """Short caption phrases: split at punctuation, then at most 4 words / 20 chars each."""
    words = display.split()
    phrases, cur = [], []
    for w in words:
        cur.append(w)
        if w[-1] in ".?!;:,":
            phrases.append(cur)
            cur = []
    if cur:
        phrases.append(cur)
    merged, carry = [], []
    for ph in phrases:
        ph = carry + ph
        carry = []
        if len(ph) == 1 and ph[0][-1] == ",":
            carry = ph
            continue
        merged.append(ph)
    if carry:
        merged.append(carry)
    parts = []
    for ph in merged:
        n_ = len(ph)
        c_ = math.ceil(n_ / 4)
        while True:
            sizes = [n_ // c_ + (1 if q < n_ % c_ else 0) for q in range(c_)]
            out_, q0 = [], 0
            for sz in sizes:
                out_.append(ph[q0:q0 + sz])
                q0 += sz
            if c_ >= n_ or max(len(" ".join(x)) for x in out_) <= 20:
                break
            c_ += 1
        parts += out_
    return [" ".join(p) for p in parts]


def ts(x, sep=","):
    h = int(x // 3600)
    m_ = int(x % 3600 // 60)
    s_ = x % 60
    return f"{h:02d}:{m_:02d}:{s_:06.3f}".replace(".", sep)


def ats(x):
    h = int(x // 3600)
    m_ = int(x % 3600 // 60)
    s_ = x % 60
    return f"{h:d}:{m_:02d}:{s_:05.2f}"


def find_font(fonts_dir, names):
    for d in [fonts_dir, "/usr/share/fonts/truetype/google-fonts", "/usr/share/fonts/truetype/dejavu"]:
        if not d:
            continue
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return d, p
    return None, None


# ---------------------------------------------------------------- build
def cmd_build(a):
    lines = load_script(a.script)
    clips = clip_files(a.clips)
    words_all = json.load(open(a.words))
    n_use = min(len(lines), len(clips))
    os.makedirs(a.out, exist_ok=True)
    tmp = os.path.join(a.out, "seg")
    os.makedirs(tmp, exist_ok=True)

    fonts_dir, font_bold = find_font(a.fonts, ["Poppins-Bold.ttf", "DejaVuSans-Bold.ttf"])
    _, font_med = find_font(a.fonts, ["Poppins-Medium.ttf", "DejaVuSans.ttf"])
    font_name = "Poppins" if font_bold and "Poppins" in font_bold else "DejaVu Sans"

    plan = []   # per clip: dict(n, path, words, a, b, gap, T)
    t = 0.0
    for i in range(n_use):
        n, path = clips[i]
        words = words_all.get(str(n), {}).get("words", [])
        cd = dur(path)
        sa, sb = speech_bounds(words, cd)
        gap = gap_after(lines[i], i, i == n_use - 1)
        plan.append(dict(i=i, n=n, path=path, words=words, a=sa, b=sb, gap=gap, T=t,
                         src=audio_source(path, a.audio)))
        t += (sb - sa) + gap
    total = t

    # ---- video: one segment per clip (speech + gap held on the last frame), alternating punch-in
    enc = "-an -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r 30"
    seg_files = []
    for p in plan:
        sc = 1.0 if p["i"] % 2 == 0 else PUNCH
        n_frames = int(round((p["b"] - p["a"] + p["gap"]) * FPS))
        hold = p["gap"] + 0.3
        vf = (f"fps=30,scale={int(W_ * sc / 2) * 2}:{int(H_ * sc / 2) * 2}:flags=lanczos,"
              f"crop={W_}:{H_}:(iw-{W_})/2:(ih-{H_})*0.32,"
              f"tpad=stop_duration={hold:.3f}:stop_mode=clone,"
              f"trim=end_frame={n_frames},setpts=PTS-STARTPTS,format=yuv420p,setsar=1")
        out = os.path.join(tmp, f"s{p['i']:02d}.mp4")
        run(f'ffmpeg -v error -y -ss {p["a"]:.3f} -t {p["b"] - p["a"] + 0.2:.3f} -i "{p["path"]}" '
            f'-vf "{vf}" -frames:v {n_frames} {enc} "{out}"')
        seg_files.append(out)
    listing = os.path.join(tmp, "list.txt")
    open(listing, "w").write("".join(f"file '{os.path.abspath(f)}'\n" for f in seg_files))
    video = os.path.join(tmp, "video.mp4")
    run(f'ffmpeg -v error -y -f concat -safe 0 -i "{listing}" -c copy "{video}"')

    # ---- audio: level every line to the same speech level, 20 ms fades, quiet room tone, -14 LUFS
    N = int(total * SR) + SR
    mix = np.zeros(N)
    rms = []
    pcm = []
    for p in plan:
        x = load_pcm(p["src"], p["a"], p["b"])
        pcm.append(x)
        rms.append(speech_rms(x))
    target = float(np.median(rms))
    fi = int(0.020 * SR)
    for p, x, r in zip(plan, pcm, rms):
        x = x * (target / max(r, 1e-6))
        k = min(fi, len(x) // 2)
        x[:k] *= np.linspace(0, 1, k)
        x[-k:] *= np.linspace(1, 0, k)
        pos = int(round(p["T"] * SR))
        mix[pos:pos + len(x)] += x[: max(0, N - pos)]
    rng = np.random.default_rng(7)
    noise = rng.standard_normal(N)
    spec = np.fft.rfft(noise)
    f = np.fft.rfftfreq(N, 1 / SR)
    f[0] = 1
    spec *= 1 / np.sqrt(f) * (f > 60) * (f < 6000)
    noise = np.fft.irfft(spec, N)
    noise *= 10 ** (-60 / 20) / (np.sqrt((noise ** 2).mean()) + 1e-12)
    mix += noise
    full = mix[: int(total * SR)]
    pk = np.abs(full).max()
    if pk > 0.95:
        full *= 0.95 / pk
    raw = os.path.join(tmp, "audio.f32")
    np.stack([full, full], 1).astype(np.float32).tofile(raw)
    meas = subprocess.run(f'ffmpeg -hide_banner -nostats -f f32le -ar {SR} -ac 2 -i "{raw}" -af ebur128 -f null -',
                          shell=True, capture_output=True, text=True).stderr
    lufs = float([l for l in meas.splitlines() if l.strip().startswith("I:")][-1].split()[1])
    gain = -14.0 - lufs
    wav = os.path.join(tmp, "audio.wav")
    run(f'ffmpeg -v error -y -f f32le -ar {SR} -ac 2 -i "{raw}" '
        f'-af "volume={gain:.2f}dB,alimiter=limit=0.87:attack=3:release=60:level=disabled" '
        f'-ar {SR} -c:a pcm_s16le "{wav}"')

    # ---- captions (short phrases, timed from the recognised words)
    cues = []
    for p in plan:
        ph = phrases_for(lines[p["i"]]["display"])
        ws = [w for w in p["words"] if norm(w["text"])]
        if not ph or not ws:
            continue
        total_words = sum(len(x.split()) for x in ph)
        m = len(ws)
        idx = 0
        for k, text in enumerate(ph):
            nw = len(text.split())
            wa = int(round(idx * m / total_words))
            wb = max(wa + 1, int(round((idx + nw) * m / total_words)))
            wa = min(wa, m - 1)
            wb = min(wb, m)
            st = max(p["a"], ws[wa]["start"]) if k else p["a"] + LEAD * 0.5
            en = ws[wb - 1]["end"] if wb < m else p["b"] - TAIL * 0.5
            cues.append([p["T"] + st - p["a"], p["T"] + en - p["a"], text])
            idx += nw
    for q in range(len(cues) - 1):
        nxt = cues[q + 1][0]
        cues[q][1] = nxt - 0.03 if nxt - cues[q][1] < 0.7 else cues[q][1] + 0.15
        cues[q][1] = max(cues[q][1], cues[q][0] + 0.3)
    for q in range(len(cues) - 1):
        if cues[q][1] > cues[q + 1][0] - 0.02:
            cues[q][1] = cues[q + 1][0] - 0.02
    srt = os.path.join(a.out, f"{a.name}.srt")
    with open(srt, "w") as fh:
        for i, (s_, e_, tx) in enumerate(cues, 1):
            fh.write(f"{i}\n{ts(s_)} --> {ts(e_)}\n{tx}\n\n")
    ass = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 720\nPlayResY: 1280\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n"
           "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
           "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
           "MarginL, MarginR, MarginV, Encoding\n"
           f"Style: Cap,{font_name},52,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,4.2,0,2,40,40,205,1\n\n"
           "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    for s_, e_, tx in cues:
        ass += f"Dialogue: 0,{ats(s_)},{ats(e_)},Cap,,0,0,0,,{tx}\n"
    ass_path = os.path.join(tmp, "caps.ass")
    open(ass_path, "w").write(ass)

    # ---- name tag on the first and the last line (same look as the approved episode)
    def tag(t0, t1):
        al = f"if(lt(t,{t0}),0,if(lt(t,{t0}+0.12),(t-{t0})/0.12,if(lt(t,{t1}-0.12),1,if(lt(t,{t1}),({t1}-t)/0.12,0))))"
        en = f"between(t,{t0},{t1})"
        s = (f"drawbox=x=40:y=868:w=330:h=96:color=black@0.55:t=fill:enable='{en}',"
             f"drawbox=x=40:y=868:w=6:h=96:color=0xE0B040@0.95:t=fill:enable='{en}'")
        if font_bold and font_med:
            s += (f",drawtext=fontfile={font_bold}:text='Derrick Hughes':fontsize=32:fontcolor=white:x=62:y=880:alpha='{al}':enable='{en}',"
                  f"drawtext=fontfile={font_med}:text='Blessed Prayers':fontsize=22:fontcolor=0xE0B040:x=62:y=926:alpha='{al}':enable='{en}'")
        return s
    first, last = plan[0], plan[-1]
    tags = [tag(round(first["T"] + 0.3, 2), round(first["T"] + (first["b"] - first["a"]), 2))]
    if len(plan) > 1:
        tags.append(tag(round(last["T"] + 0.1, 2), round(last["T"] + (last["b"] - last["a"]) + 0.3, 2)))
    tagchain = ",".join(tags) if a.nametag else "null"

    final = os.path.join(a.out, f"{a.name}.mp4")
    nocap = os.path.join(a.out, f"{a.name}_nocaptions.mp4")
    fd = f":fontsdir={fonts_dir}" if fonts_dir else ""
    run(f'ffmpeg -v error -y -i "{video}" -i "{wav}" -map 0:v -map 1:a -vf "{tagchain}" -c:v libx264 -preset medium -crf 21 '
        f'-maxrate 1800k -bufsize 3600k -pix_fmt yuv420p -c:a aac -b:a 160k -ar {SR} -shortest -movflags +faststart "{nocap}"')
    run(f'ffmpeg -v error -y -i "{nocap}" -vf "ass={ass_path}{fd}" -c:v libx264 -preset medium -crf 22 '
        f'-maxrate 1500k -bufsize 3000k -pix_fmt yuv420p -c:a copy -movflags +faststart "{final}"')
    rep = dict(total=round(total, 2), lufs_before=lufs, gain_db=round(gain, 2), clips=n_use,
               mb=round(os.path.getsize(final) / 1e6, 2),
               timeline=[dict(clip=p["n"], T=round(p["T"], 2), a=round(p["a"], 2), b=round(p["b"], 2),
                              gap=p["gap"]) for p in plan])
    json.dump(rep, open(os.path.join(a.out, "report.json"), "w"), indent=1)
    print(f"BUILT {final}  {total:.1f}s  {rep['mb']} MB  LUFS {lufs:.1f} -> -14")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["transcribe", "gate", "build"])
    ap.add_argument("--clips", default="clips")
    ap.add_argument("--audio", default="")
    ap.add_argument("--script", default="script.json")
    ap.add_argument("--words", default="words.json")
    ap.add_argument("--status", default="STATUS.txt")
    ap.add_argument("--out", default="out")
    ap.add_argument("--name", default="Morning_Word")
    ap.add_argument("--fonts", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--nametag", action="store_true", default=True)
    args = ap.parse_args()
    {"transcribe": cmd_transcribe, "gate": cmd_gate, "build": cmd_build}[args.mode](args)
