import numpy as np, json, subprocess, os, sys, time, re, traceback
from PIL import Image, ImageDraw, ImageFont
W = '/kaggle/working'
FPS = 16
R = {'step_s': {}}
os.chdir(W)


def sh(c):
    r = subprocess.run(c, shell=True, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr)


def step(name, t0):
    R['step_s'][name] = round(time.time() - t0, 1)
    json.dump(R, open(W + '/post8.json', 'w'), indent=1)


def dur(p):
    return float(sh('ffprobe -v error -show_entries format=duration -of csv=p=0 ' + p)[1].strip())


# ---- 3. histogram match every frame to the still ----
t0 = time.time()
fr = np.load(W + '/narr_frames.npy')
n, H, Wd, _ = fr.shape
R['frames'] = int(n); R['hw'] = [int(H), int(Wd)]
still = np.array(Image.open(W + '/still.png').convert('RGB'))
from skimage.exposure import match_histograms
hm = np.stack([np.clip(np.rint(match_histograms(f, still, channel_axis=-1)), 0, 255).astype(np.uint8) for f in fr])


def sweater(a):
    return a[:, 480:700, 80:320, :].mean(axis=(1, 2)).mean(1)


for nm, arr in (('raw', fr), ('hm', hm)):
    b = sweater(arr)
    wf = arr.mean(axis=(1, 2, 3))
    R['drift_' + nm] = {'sweater_first_to_last_pct': round(float((b[-1] / b[0] - 1) * 100), 2),
                        'sweater_worst_vs_first_pct': round(float(((b / b[0] - 1) * 100)[np.abs(b / b[0] - 1).argmax()]), 2),
                        'wholeframe_first_to_last_pct': round(float((wf[-1] / wf[0] - 1) * 100), 2)}
import imageio
imageio.mimsave(W + '/hm_silent.mp4', list(hm), fps=FPS, codec='libx264', macro_block_size=None,
                ffmpeg_params=['-crf', '14', '-preset', 'veryfast', '-pix_fmt', 'yuv420p'])
del fr, hm
step('3_histogram_match', t0)

narr_len = float(open(W + '/narr_src.txt').read().split()[-1])
TRIM = round(narr_len + 0.7, 2)
R['narration_s'] = narr_len; R['trim_s'] = TRIM

# ---- 4. interpolate to 30 fps ----
t0 = time.time()
rc, o = sh('ffmpeg -y -loglevel error -i hm_silent.mp4 -t %s -vf "minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p -an interpolated.mp4' % TRIM)
R['interp_rc'] = rc; R['interp_err'] = o[-300:]
if rc != 0:
    rc, o = sh('ffmpeg -y -loglevel error -i hm_silent.mp4 -t %s -vf "minterpolate=fps=30:mi_mode=blend" -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p -an interpolated.mp4' % TRIM)
    R['interp_fallback_blend_rc'] = rc
# add the narration (original 24 kHz Chatterbox wav), 20 ms fades at the edges
fo = round(TRIM - 0.02, 3)
rc, o = sh('ffmpeg -y -loglevel error -i interpolated.mp4 -i tts_raw.wav -map 0:v:0 -map 1:a:0 -t %s -af "afade=t=in:d=0.02,afade=t=out:st=%s:d=0.02,apad" -c:v copy -c:a aac -b:a 160k -ar 48000 -shortest interp_av.mp4' % (TRIM, fo))
R['mux_rc'] = rc; R['mux_err'] = o[-300:]
step('4_interpolate_and_mux', t0)

# ---- 5. captions: Faster-Whisper on narration -> SRT -> burn in ----
t0 = time.time()
rc, o = sh('pip install -q faster-whisper 2>&1 | tail -1')
from faster_whisper import WhisperModel
words = []
try:
    wm = WhisperModel('base.en', device='cpu', compute_type='int8')
    segs, info = wm.transcribe(W + '/tts_raw.wav', word_timestamps=True, language='en')
    for s in segs:
        for w in s.words:
            words.append((w.word.strip(), float(w.start), float(w.end)))
    R['whisper_model'] = 'base.en cpu int8'
except Exception:
    R['whisper_error'] = traceback.format_exc()[-400:]
R['whisper_words'] = len(words)
R['whisper_text'] = ' '.join(w[0] for w in words)
cues = []
cur = []
for w in words:
    cur.append(w)
    txt = ' '.join(x[0] for x in cur)
    if re.search(r'[.;:!?,]$', w[0]) and len(cur) >= 2 or len(txt) >= 22 or len(cur) >= 5:
        cues.append(cur); cur = []
if cur:
    cues.append(cur)


def ts(x):
    h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
    return ('%02d:%02d:%06.3f' % (h, m, s)).replace('.', ',')


lines = []
for i, c in enumerate(cues):
    a = c[0][1]
    b = c[-1][2]
    if i + 1 < len(cues) and cues[i + 1][0][1] - b < 0.35:
        b = cues[i + 1][0][1] - 0.02
    else:
        b += 0.15
    t = ' '.join(x[0] for x in c)
    if len(t) > 24 and ' ' in t:
        sp = [j for j, ch in enumerate(t) if ch == ' ']
        k = min(sp, key=lambda j: abs(j - len(t) / 2))
        t = t[:k] + '\n' + t[k + 1:]
    lines.append('%d\n%s --> %s\n%s\n' % (i + 1, ts(a), ts(b), t))
open(W + '/captions.srt', 'w').write('\n'.join(lines))
R['cues'] = len(cues)
# speech onset from loudness vs first cue start
import librosa
y, sr = librosa.load(W + '/tts_raw.wav', sr=16000)
rms = librosa.feature.rms(y=y, frame_length=400, hop_length=160)[0]
on = float(np.argmax(rms > 0.2 * rms.max()) * 160 / sr)
R['speech_onset_s'] = round(on, 3)
R['first_cue_start_s'] = round(cues[0][0][1], 3) if cues else None
R['caption_vs_audio_onset_ms'] = round((cues[0][0][1] - on) * 1000) if cues else None
style = "FontName=DejaVu Sans,Bold=1,FontSize=10,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginV=40,MarginL=14,MarginR=14"
burn_ok = False
for ff in ['ffmpeg', None]:
    if ff is None:
        try:
            import imageio_ffmpeg
            ff = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            break
    rc, o = sh('%s -y -loglevel error -i interp_av.mp4 -vf "subtitles=captions.srt:force_style=\'%s\'" -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -c:a copy captioned.mp4' % (ff, style))
    R['burn_try_' + os.path.basename(ff)] = [rc, o[-200:]]
    if rc == 0 and os.path.exists('captioned.mp4'):
        burn_ok = True
        R['burn_method'] = 'ffmpeg subtitles filter (' + ff + ')'
        break
if not burn_ok:
    # fallback: draw the captions ourselves with PIL
    rd = imageio.get_reader('interp_av.mp4')
    wr = imageio.get_writer('cap_silent.mp4', fps=30, codec='libx264', macro_block_size=None,
                            ffmpeg_params=['-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p'])
    fp = [p for p in ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'] if os.path.exists(p)]
    font = ImageFont.truetype(fp[0], 30) if fp else ImageFont.load_default()
    spans = [(c[0][1], c[-1][2] + 0.15, ' '.join(x[0] for x in c)) for c in cues]
    for i, fm in enumerate(rd):
        tt = i / 30.0
        txt = next((s[2] for s in spans if s[0] <= tt <= s[1]), None)
        if txt:
            im = Image.fromarray(fm)
            d = ImageDraw.Draw(im)
            bb = d.textbbox((0, 0), txt, font=font)
            x = (im.width - (bb[2] - bb[0])) // 2
            yy = im.height - 130
            d.text((x, yy), txt, font=font, fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
            fm = np.array(im)
        wr.append_data(fm)
    wr.close()
    sh('ffmpeg -y -loglevel error -i cap_silent.mp4 -i interp_av.mp4 -map 0:v:0 -map 1:a:0 -c:v copy -c:a copy -shortest captioned.mp4')
    R['burn_method'] = 'PIL overlay fallback'
step('5_captions', t0)

# ---- 6. loudnorm to -14 LUFS (two-pass so it lands on target) ----
t0 = time.time()
rc, o = sh('ffmpeg -hide_banner -i captioned.mp4 -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1')
m = re.search(r'\{[^{}]*"input_i"[^{}]*\}', o, re.S)
if m:
    j = json.loads(m.group(0))
    af = 'loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true' % (
        j['input_i'], j['input_tp'], j['input_lra'], j['input_thresh'], j['target_offset'])
    R['loudnorm_pass1'] = j
else:
    af = 'loudnorm=I=-14:TP=-1.5:LRA=11'
rc, o = sh('ffmpeg -y -loglevel error -i captioned.mp4 -af "%s" -ar 48000 -c:v copy -c:a aac -b:a 160k final_normalized.mp4' % af)
R['loudnorm_rc'] = rc
rc, o = sh('ffmpeg -hide_banner -i final_normalized.mp4 -af ebur128=peak=true -f null - 2>&1 | tail -14')
mm = re.search(r'I:\s+(-?[\d.]+) LUFS', o)
R['final_loudness_lufs'] = float(mm.group(1)) if mm else o[-200:]
pk = re.search(r'Peak:\s+(-?[\d.]+) dBFS', o)
R['final_true_peak_dbfs'] = float(pk.group(1)) if pk else None
step('6_loudnorm', t0)
rc, o = sh('ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of json final_normalized.mp4')
R['final_video'] = json.loads(o)['streams'][0]
R['final_duration_s'] = round(dur('final_normalized.mp4'), 2)
R['final_bytes'] = os.path.getsize('final_normalized.mp4')
json.dump(R, open(W + '/post8.json', 'w'), indent=1)
print(json.dumps(R, indent=1))
