"""Morning Word, Week 2 Day 1 (Psalm 118:24) build.
Every line is a Derrick on-camera Veo clip. Teaching lines play his audio over animated B-roll.
Video and audio are assembled separately on one timeline so speech is never crossfaded.
"""
import json, os, subprocess, sys, math
import numpy as np

W = os.path.dirname(os.path.abspath(__file__))
REPO = "/home/claude/morning-word-videos."
DAY1 = f"{REPO}/day1/morning-word-day1.mp4"
OUT = f"{W}/out"; TMP = f"{W}/seg"
os.makedirs(OUT, exist_ok=True); os.makedirs(TMP, exist_ok=True)
FPS = 30; SR = 48000
FONT_B = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
FONT_M = "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"

def run(c):
    r = subprocess.run(c, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        print("CMD FAILED:\n", c, "\n", r.stderr[-3000:]); sys.exit(1)
    return r.stdout
def dur(f): return float(run(f'ffprobe -v error -show_entries format=duration -of csv=p=0 "{f}"'))

LINES = json.load(open(f"{W}/lines.json"))
DISPLAY = dict(LINES)
tr = {k: v["words"] for k, v in json.load(open(f"{W}/tr_all.json")).items()}
import numpy as _np
def _bounds(clip):
    x = _np.frombuffer(subprocess.run(f"ffmpeg -v error -i {W}/clips/{clip}.mp4 -vn -ac 1 -ar 16000 -af highpass=f=120 -f f32le -", shell=True, capture_output=True).stdout, _np.float32)
    fr_ = 320; n_ = len(x) // fr_; e_ = 20 * _np.log10(_np.sqrt((x[:n_ * fr_].reshape(n_, fr_) ** 2).mean(1)) + 1e-9)
    act = _np.where(e_ > e_.max() - 24)[0]
    st = max(0.0, act[0] * 0.02 - 0.04)
    en = min(7.9, tr[clip][-1]["end"] + 0.10)
    return round(st, 2), round(en, 2)
CLIPMAP = {"1":"f7a44b9e","2":"057dc0c6","3":"4d04bb5e","4":"d191de96","5":"91ebeb5e","6":"b1c1a5b5","7":"be74f2f2","8":"c0204dbd","9":"1399060e","10":"9a4f14c1","11":"86ccb482","12":"abe2a722","13":"12497d20","14":"3677aa7d","15":"1272fa25","16":"9d3765f5"}
GAP = {"4": 1.0, "13": 1.0, "5": 0.75, "16": 0.0}
CLIP = {}
for k, c in CLIPMAP.items():
    s_, e_ = _bounds(c); CLIP[k] = (c, s_, e_, 0, GAP.get(k, 0.65))
VIS = {
 "1": ("cam", 1.00), "2": ("cam", 1.08), "3": ("cam", 1.00), "4": ("cam", 1.08), "5": ("cam", 1.00),
 "6": ("broll", ["br_storm"]), "7": ("broll", ["br_asleep"]), "8": ("broll", ["br_bible"]),
 "9": ("broll", ["br_rain"]), "10": ("broll", ["br_sleeper"]),
 "11": ("cam", 1.08), "12": ("cam", 1.00), "13": ("cam", 1.08), "14": ("cam", 1.00), "15": ("cam", 1.08), "16": ("cam", 1.00),
}
ORDER = [str(i) for i in range(1, 17) if i != 10]  # line 10 ("Ten hours") cut: the reading runs 8.8 hours
PRE = {}   # this piece starts mid-clip, so only a sliver of picture before its first word is usable
OPEN = 5.7333; CLOSE_LEN = 12.4667
XF = 0.36          # crossfade into / out of B-roll
CUT = 1.0 / FPS    # hard cut

# ---------------- timeline ----------------
T = {}; D = {}
t = OPEN + 0.30
for k in ORDER:
    clip, s, e, ge, gap = CLIP[k]
    T[k] = t; D[k] = e - s; t = T[k] + D[k] + gap
END_SPEECH = T["16"] + D["16"]
CLOSE_AT = END_SPEECH + 0.95
TOTAL = CLOSE_AT + CLOSE_LEN

# segments: list of dicts {kind, key, a, b}; transitions between them {center, x}
segs = [{"kind": "open"}]
for k in ORDER:
    v = VIS[k]
    if v[0] == "cam": segs.append({"kind": "cam", "key": k, "scale": v[1]})
    else:
        for j, f in enumerate(v[1]): segs.append({"kind": "broll", "key": k, "file": f, "part": j, "parts": len(v[1])})
segs.append({"kind": "close"})

def word_time(k, word):
    clip, s, e, ge, gap = CLIP[k]
    for w in tr[clip]:
        if w["text"].strip(".,;:").lower() == word: return T[k] + (w["start"] - s)
    raise KeyError(word)

trans = []
for i in range(len(segs) - 1):
    A, B = segs[i], segs[i + 1]
    if A["kind"] == "open":
        trans.append((OPEN, 0.24)); continue
    if B["kind"] == "close":
        trans.append((CLOSE_AT, 0.50)); continue
    ka, kb = A["key"], B["key"]
    if ka == kb:   # two B-roll shots inside one line (line 7: cloud -> fire)
        trans.append((word_time(ka, "and") - 0.05, XF)); continue
    endA = T[ka] + D[ka]; gap = T[kb] - endA
    sB = CLIP[kb][1]
    if A["kind"] == "cam" and B["kind"] == "cam":
        back = min(max(min(sB, PRE.get(kb, 9)) - 0.02, 0.03), gap * 0.5)      # how far before B's first word we cut
        trans.append((T[kb] - back, CUT))
    else:
        c = endA + gap / 2
        if B["kind"] == "cam":                            # never run out of real footage before his first word
            c = min(T[kb] - 0.08, max(c, T[kb] - sB + XF / 2))
        trans.append((c, XF))

def fr(x): return int(round(x * FPS))
bounds = []
for i, sg in enumerate(segs):
    a = 0.0 if i == 0 else trans[i - 1][0] - trans[i - 1][1] / 2
    b = TOTAL if i == len(segs) - 1 else trans[i][0] + trans[i][1] / 2
    sg["fa"], sg["fb"] = fr(a), fr(b)
for i in range(1, len(segs)):
    if segs[i - 1]["fb"] - segs[i]["fa"] < 1: segs[i]["fa"] = segs[i - 1]["fb"] - 1
for sg in segs:
    sg["a"], sg["b"] = sg["fa"] / FPS, sg["fb"] / FPS

# ---------------- render video segments ----------------
VF_OUT = "fps=30,format=yuv420p,setsar=1,settb=1/30"
ENC = "-an -c:v libx264 -preset medium -crf 16 -pix_fmt yuv420p -r 30"
def card(out, n_frames, sub=True):
    d = n_frames / FPS
    vf = (f"drawtext=fontfile={FONT_B}:text='Sleep with the Word':fontsize=58:fontcolor=white:x=(w-text_w)/2:y=607"
          + (f",drawtext=fontfile={FONT_M}:text='The Book of Psalms  KJV':fontsize=30:fontcolor=0xD8D8D8:x=(w-text_w)/2:y=716" if sub else ""))
    run(f'ffmpeg -v error -y -f lavfi -i color=c=black:s=720x1280:r=30:d={d:.4f} -vf "{vf},{VF_OUT}" -frames:v {n_frames} {ENC} {out}')

report = []
REUSE = os.environ.get("REUSE") == "1"
for i, sg in enumerate(segs):
    n = sg["fb"] - sg["fa"]; d = n / FPS
    out = f"{TMP}/s{i:02d}.mp4"; sg["out"] = out
    if REUSE and os.path.exists(out): continue
    if sg["kind"] == "open":
        card(out, n)
    elif sg["kind"] == "close":
        card(out, n, sub=False)
    elif sg["kind"] == "cam":
        k = sg["key"]; clip, s, e, ge, gap = CLIP[k]; src = f"{W}/clips/{clip}.mp4"
        ca = s + (sg["a"] - T[k]); cb = s + (sg["b"] - T[k])
        pad = max(0.0, -ca); ca = max(0.0, ca)
        ge = min(ge if ge else 7.9, 7.95)
        hold = max(0.0, cb - ge); cb = min(cb, ge)
        sc = sg["scale"]
        vf = f"fps=30,scale={int(720*sc/2)*2}:{int(1280*sc/2)*2}:flags=lanczos,crop=720:1280:(iw-720)/2:(ih-1280)*0.32"
        vf += f",tpad=start_duration={pad:.3f}:start_mode=clone:stop_duration={hold + 0.3:.3f}:stop_mode=clone"
        vf += f",trim=end_frame={n},setpts=PTS-STARTPTS,{VF_OUT}"
        run(f'ffmpeg -v error -y -ss {ca:.3f} -t {cb - ca + 0.25:.3f} -i {src} -vf "trim=0:{cb - ca:.3f},setpts=PTS-STARTPTS,{vf}" -frames:v {n} {ENC} {out}')
        report.append(f"cam  L{k:>2} {clip} clip[{ca:.2f}-{cb:.2f}] pad {pad:.2f} hold {hold:.2f}  tl[{sg['a']:.2f}-{sg['b']:.2f}]")
    else:
        k = sg["key"]; src = f"{W}/broll/{sg['file']}.mp4"
        avail = dur(src) - 0.25
        st = 0.10
        vf = "fps=30,scale=720:1280:flags=lanczos"
        if d > avail - st:
            fac = d / (avail - st) + 0.01
            vf = f"setpts=PTS*{fac:.4f}," + vf
        vf += f",tpad=stop_duration=0.3:stop_mode=clone,trim=end_frame={n},setpts=PTS-STARTPTS,{VF_OUT}"
        run(f'ffmpeg -v error -y -ss {st:.3f} -i {src} -vf "{vf}" -frames:v {n} {ENC} {out}')
        report.append(f"broll L{k:>2} {sg['file']} {d:.2f}s  tl[{sg['a']:.2f}-{sg['b']:.2f}]")
    got = int(run(f'ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 {out}').strip())
    if got != n: print("FRAME MISMATCH", out, got, n); sys.exit(1)
print("\n".join(report))

# ---------------- xfade chain ----------------
ins = " ".join(f"-i {sg['out']}" for sg in segs)
fc = [f"[{i}:v]settb=AVTB,fps=30,format=yuv420p[p{i}]" for i in range(len(segs))]; last = "p0"
for i in range(1, len(segs)):
    x = segs[i - 1]["fb"] - segs[i]["fa"]            # overlap in frames
    off = segs[i]["fa"] / FPS
    fc.append(f"[{last}][p{i}]xfade=transition=fade:duration={x / FPS:.5f}:offset={off:.5f}[v{i}]")
    last = f"v{i}"
# lower third: name tag on the first on-camera line and on the sign-off
def tag(a, b):
    al = f"if(lt(t,{a}),0,if(lt(t,{a}+0.12),(t-{a})/0.12,if(lt(t,{b}-0.12),1,if(lt(t,{b}),({b}-t)/0.12,0))))"
    en = f"between(t,{a},{b})"
    return (f"drawbox=x=40:y=868:w=330:h=96:color=black@0.55:t=fill:enable='{en}',"
            f"drawbox=x=40:y=868:w=6:h=96:color=0xE0B040@0.95:t=fill:enable='{en}',"
            f"drawtext=fontfile={FONT_B}:text='Derrick Hughes':fontsize=32:fontcolor=white:x=62:y=880:alpha='{al}':enable='{en}',"
            f"drawtext=fontfile={FONT_M}:text='Blessed Prayers':fontsize=22:fontcolor=0xE0B040:x=62:y=926:alpha='{al}':enable='{en}'")
t1a = T["1"] + 0.4; t1b = T["1"] + D["1"] + 0.2
t2a = T["16"] + 0.1; t2b = END_SPEECH + 0.45
fc.append(f"[{last}]{tag(round(t1a,2), round(t1b,2))},{tag(round(t2a,2), round(t2b,2))}[vout]")
open(f"{TMP}/fc.txt", "w").write(";".join(fc))
if not (REUSE and os.path.exists(f'{TMP}/video.mp4')): run(f'ffmpeg -v error -y {ins} -filter_complex_script {TMP}/fc.txt -map "[vout]" -c:v libx264 -preset medium -crf 16 -pix_fmt yuv420p -r 30 {TMP}/video.mp4')

# ---------------- audio ----------------
def load(path, ss=None, to=None, af=None):
    c = "ffmpeg -v error "
    if ss is not None: c += f"-ss {ss:.3f} -to {to:.3f} "
    c += f'-i "{path}" -vn -ac 1 -ar {SR} ' + (f'-af "{af}" ' if af else "") + "-f f32le -"
    return np.frombuffer(subprocess.run(c, shell=True, capture_output=True).stdout, np.float32).astype(np.float64)

def speech_rms(x):
    fr_ = 480; n = len(x) // fr_
    e = np.sqrt((x[:n * fr_].reshape(n, fr_) ** 2).mean(1) + 1e-12)
    act = e > e.max() * 10 ** (-22 / 20)
    return float(np.sqrt((x[:n * fr_].reshape(n, fr_)[act] ** 2).mean()))

N = int(TOTAL * SR) + SR
mix = np.zeros(N)
LEAD, TAIL = 0.08, 0.12
_d1 = load(DAY1, 12.0, 100.0)
TARGET = speech_rms(_d1)
print("Day 1 speech level %.1f dBFS" % (20 * math.log10(TARGET)))
BASE_AF = "highpass=f=85,afftdn=nr=14:nf=-42:tn=1,lowpass=f=11000"
def tilt(x):
    S_ = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2; f_ = np.fft.rfftfreq(len(x), 1 / SR)
    return 10 * np.log10(S_[(f_ > 2000) & (f_ < 6000)].sum() / S_[(f_ > 100) & (f_ < 1000)].sum())
raw_ = {}
for k in ORDER:
    clip, s, e, ge, gap = CLIP[k]
    a = max(0.0, s - LEAD); b = min(7.98, e + TAIL)
    raw_[k] = (a, b, tilt(load(f"{W}/clips/{clip}.mp4", a, b, BASE_AF)))
t_med = float(np.median([v[2] for v in raw_.values()]))
for k in ORDER:
    clip, s, e, ge, gap = CLIP[k]
    a, b, tl_ = raw_[k]
    g_sh = max(-3.0, min(3.0, 0.65 * (t_med - tl_)))        # pull each line's tone toward the episode's middle
    x = load(f"{W}/clips/{clip}.mp4", a, b, BASE_AF + f",highshelf=f=2200:g={g_sh:.2f}")
    g = TARGET / max(speech_rms(x), 1e-6)
    x = x * g
    fi = int(0.012 * SR); fo = int(0.06 * SR)
    x[:fi] *= np.linspace(0, 1, fi); x[-fo:] *= np.linspace(1, 0, fo)
    p = int(round((T[k] - (s - a)) * SR))
    mix[p:p + len(x)] += x
    print(f"audio L{k:>2} {clip} tone {tl_:6.1f} -> shelf {g_sh:+.1f} dB, gain {20*math.log10(g):+.1f} dB")
# quiet steady room tone so the gaps between lines never drop to dead air
rng = np.random.default_rng(7)
noise = rng.standard_normal(N)
spec = np.fft.rfft(noise); f = np.fft.rfftfreq(N, 1 / SR); f[0] = 1
spec *= 1 / np.sqrt(f) * (f > 60) * (f < 6000)
noise = np.fft.irfft(spec, N); noise *= 10 ** (-58 / 20) / (np.sqrt((noise ** 2).mean()) + 1e-12)
body0 = int(OPEN * SR); body1 = int((CLOSE_AT + 0.3) * SR)
env = np.zeros(N); env[body0:body1] = 1
r = int(0.4 * SR); env[body0:body0 + r] = np.linspace(0, 1, r); env[body1 - r:body1] = np.linspace(1, 0, r)
mix += noise * env
# song: opener hook and closer chorus, straight from the approved Day 1 master
op = load(DAY1, 0.0, OPEN); cl = load(DAY1, 139.3333, 151.80)
music = np.zeros(N)
music[:len(op)] += op
p = int(CLOSE_AT * SR) - int(0.20 * SR)
fi = int(0.25 * SR); cl[:fi] *= np.linspace(0, 1, fi)
music[p:p + len(cl)] += cl[: N - p]
full = (mix + music)[: int(TOTAL * SR)]
pk = np.abs(full).max()
if pk > 0.95: full *= 0.95 / pk
np.stack([full, full], 1).astype(np.float32).tofile(f"{TMP}/audio.f32")
r_ = subprocess.run(f'ffmpeg -hide_banner -nostats -f f32le -ar {SR} -ac 2 -i {TMP}/audio.f32 -af ebur128 -f null -', shell=True, capture_output=True, text=True).stderr
I_ = float([l for l in r_.splitlines() if l.strip().startswith("I:")][-1].split()[1])
gain = -14.0 - I_
print("integrated %.1f LUFS, gain %.1f dB" % (I_, gain))
run(f'ffmpeg -v error -y -f f32le -ar {SR} -ac 2 -i {TMP}/audio.f32 -af "volume={gain:.2f}dB,alimiter=limit=0.87:attack=3:release=60:level=disabled" -ar {SR} -c:a pcm_s16le {TMP}/audio.wav')

# ---------------- captions ----------------
def chunks_for(k):
    clip, s, e, ge, gap = CLIP[k]
    wh = [w for w in tr[clip] if s - 0.3 <= w["start"] < e + 0.2]
    disp = DISPLAY[k].split(); m = len(wh)
    groups = []
    rest = disp; base = 0
    n = max(1, len(rest)); mrest = m - base
    # split at punctuation first, then keep each caption to 4 words or fewer, evenly balanced
    phrases = []; cur = []
    for w in rest:
        cur.append(w)
        if w[-1] in ".?!;:,": phrases.append(cur); cur = []
    if cur: phrases.append(cur)
    merged = []; carry = []
    for ph in phrases:   # a one-word phrase ("Father,") rides with the phrase after it
        ph = carry + ph; carry = []
        if len(ph) == 1 and ph[0][-1] == ",": carry = ph; continue
        merged.append(ph)
    if carry: merged.append(carry)
    parts = []
    for ph in merged:
        n_ = len(ph); c_ = math.ceil(n_ / 4)
        while True:
            sizes = [n_ // c_ + (1 if q < n_ % c_ else 0) for q in range(c_)]
            out_ = []; q0 = 0
            for sz in sizes: out_.append(ph[q0:q0 + sz]); q0 += sz
            if c_ >= n_ or max(len(" ".join(x)) for x in out_) <= 20: break
            c_ += 1
        parts += out_
    i = 0
    for pz in parts:
        j = i + len(pz)
        wa = base + int(round(i * mrest / n)); wb = base + int(round(j * mrest / n))
        groups.append((pz, wa, max(wa + 1, wb))); i = j
    cues = []
    for words, wa, wb in groups:
        wa = min(wa, m - 1); wb = min(wb, m)
        st = wh[wa]["start"] if wa > 0 else s
        en = wh[wb - 1]["end"] if wb < m else e
        cues.append([T[k] + (st - s), T[k] + (en - s), " ".join(words)])
    for q in range(len(cues) - 1):
        nxt = cues[q + 1][0]
        cues[q][1] = nxt - 0.03 if nxt - cues[q][1] < 0.7 else cues[q][1] + 0.15
        cues[q][1] = max(cues[q][1], cues[q][0] + 0.3)
    cues[-1][1] = T[k] + D[k] + 0.25
    return cues
cues = []
for k in ORDER: cues += chunks_for(k)
for q in range(len(cues) - 1):
    if cues[q][1] > cues[q + 1][0] - 0.02: cues[q][1] = cues[q + 1][0] - 0.02
def ts(x, sep=","):
    h = int(x // 3600); m_ = int(x % 3600 // 60); s_ = x % 60
    return f"{h:02d}:{m_:02d}:{s_:06.3f}".replace(".", sep)
with open(f"{OUT}/sleep-promo-psalms.srt", "w") as f:
    for i, (a, b, txt) in enumerate(cues, 1): f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{txt}\n\n")
ass = """[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Poppins,52,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,4.2,0,2,40,40,205,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
def ats(x):
    h = int(x // 3600); m_ = int(x % 3600 // 60); s_ = x % 60
    return f"{h:d}:{m_:02d}:{s_:05.2f}"
for a, b, txt in cues: ass += f"Dialogue: 0,{ats(a)},{ats(b)},Cap,,0,0,0,,{txt}\n"
open(f"{TMP}/caps.ass", "w").write(ass)

# ---------------- outputs ----------------
NOCAP = f"{OUT}/Sleep_Promo_Psalms_nocaptions.mp4"
FINAL = f"{OUT}/Sleep_Promo_Psalms.mp4"
run(f'ffmpeg -v error -y -i {TMP}/video.mp4 -i {TMP}/audio.wav -map 0:v -map 1:a -c:v libx264 -preset medium -crf 21 -maxrate 1800k -bufsize 3600k -pix_fmt yuv420p -c:a aac -b:a 160k -ar {SR} -shortest -movflags +faststart {NOCAP}')
run(f'ffmpeg -v error -y -i {TMP}/video.mp4 -i {TMP}/audio.wav -map 0:v -map 1:a -vf "ass={TMP}/caps.ass:fontsdir=/usr/share/fonts/truetype/google-fonts" -c:v libx264 -preset medium -crf 22 -maxrate 1500k -bufsize 3000k -pix_fmt yuv420p -c:a aac -b:a 160k -ar {SR} -shortest -movflags +faststart {FINAL}')
json.dump({"T": T, "D": D, "END_SPEECH": END_SPEECH, "CLOSE_AT": CLOSE_AT, "TOTAL": TOTAL,
           "segs": [{k: v for k, v in sg.items()} for sg in segs], "cues": cues}, open(f"{TMP}/timeline.json", "w"), indent=1)
print("TOTAL %.2f  body %.2f  final %.2f MB" % (TOTAL, CLOSE_AT - OPEN, os.path.getsize(FINAL) / 1e6))
