import sys, re, subprocess, json, difflib, os
import numpy as np
import sherpa_onnx

SP = os.environ.get('NAOMI_QA_DIR', os.path.dirname(os.path.abspath(__file__)))
os.chdir(SP)  # asr/ model folder lives here; see README.md
clip, script_txt, ref = sys.argv[1], sys.argv[2], sys.argv[3]
tag = os.path.basename(clip)[:-4]

def pcm(f, sr=16000):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)

def f0_stats(a, sr=16000):
    fr = 1024; hop = 512; vals = []
    lo = int(sr / 400); hi = int(sr / 70)
    for i in range(0, len(a) - fr, hop):
        x = a[i:i + fr]
        if np.sqrt(np.mean(x ** 2)) < 0.02:
            continue
        x = x - x.mean()
        ac = np.correlate(x, x, 'full')[fr - 1:]
        if ac[0] <= 0:
            continue
        seg = ac[lo:hi]
        k = np.argmax(seg) + lo
        if ac[k] / ac[0] > 0.45:
            vals.append(sr / k)
    return (float(np.median(vals)), float(np.percentile(vals, 10)), float(np.percentile(vals, 90)), len(vals)) if vals else None

def asr(a, sr=16000):
    d = 'asr/sherpa-onnx-whisper-small.en'
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f'{d}/small.en-encoder.int8.onnx', decoder=f'{d}/small.en-decoder.int8.onnx', tokens=f'{d}/small.en-tokens.txt', language='en', task='transcribe', num_threads=2)
    s = rec.create_stream(); s.accept_waveform(sr, a); rec.decode_stream(s)
    return s.result.text.strip()

def norm(t):
    return re.findall(r"[a-z']+", t.lower().replace('-', ' '))

a = pcm(clip); r = pcm(ref)
heard = asr(a)
want = open(script_txt).read()
hw, ww = norm(heard), norm(want)
sm = difflib.SequenceMatcher(None, ww, hw)
print('CLIP', clip)
print('WANT :', ' '.join(ww))
print('HEARD:', ' '.join(hw))
print('word match ratio: %.3f' % sm.ratio())
for tg, i1, i2, j1, j2 in sm.get_opcodes():
    if tg != 'equal':
        print('  DIFF', tg, ww[i1:i2], '->', hw[j1:j2])

print('duration: %.2f s' % (len(a) / 16000))
print('f0 clip (median,p10,p90,n):', f0_stats(a))
print('f0 ref  (median,p10,p90,n):', f0_stats(r))

# energy envelope: speech span, internal gaps, tail
fr = 800
env = np.array([np.sqrt(np.mean(a[i:i + fr] ** 2)) for i in range(0, len(a) - fr, fr)])
thr = max(env.max() * 0.06, 0.004)
voiced = env > thr
idx = np.where(voiced)[0]
if len(idx):
    first, last = idx[0] * 0.05, (idx[-1] + 1) * 0.05
    print('speech first %.2f s, last %.2f s, tail after last voiced %.2f s' % (first, last, len(a) / 16000 - last))
    gaps = []; run = 0
    for i in range(idx[0], idx[-1] + 1):
        if not voiced[i]:
            run += 1
        else:
            if run * 0.05 >= 0.5:
                gaps.append((round((i - run) * 0.05, 2), round(run * 0.05, 2)))
            run = 0
    print('internal gaps >=0.5 s (start, len):', gaps)
    tail = a[int(last * 16000):]
    if len(tail) > 1600:
        print('tail RMS dBFS: %.1f' % (20 * np.log10(np.sqrt(np.mean(tail ** 2)) + 1e-9)))

out = subprocess.run(['ffmpeg', '-v', 'info', '-nostats', '-i', clip, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
m = re.findall(r'I:\s+(-?[\d.]+) LUFS', out); p = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', out)
print('LUFS:', m[-1] if m else None, 'true peak:', p[-1] if p else None)
fz = subprocess.run(['ffmpeg', '-v', 'info', '-nostats', '-i', clip, '-vf', 'freezedetect=n=-55dB:d=1.5,blackdetect=d=0.2', '-an', '-f', 'null', '-'], capture_output=True, text=True).stderr
print('freeze/black:', [l.strip() for l in fz.splitlines() if 'freeze_start' in l or 'black_start' in l] or 'none')

dur = len(a) / 16000
for t in (0.5, dur / 2, dur - 0.5):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.2f}', '-i', clip, '-frames:v', '1', '-vf', 'scale=640:-1', f'qa_{tag}_{t:.1f}.png'])
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '3', '-i', ref, '-frames:v', '1', '-vf', 'scale=640:-1', f'qa_{tag}_ref.png'])
print('frames saved: qa_%s_*.png' % tag)
