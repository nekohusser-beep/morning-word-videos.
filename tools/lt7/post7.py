import numpy as np, json, subprocess, os, sys, time, traceback
from PIL import Image, ImageDraw
W = '/kaggle/working'
FPS = 16
OUT = {}
t0 = time.time()
fr = np.load(W + '/narr_frames.npy')
n, H, Wd, _ = fr.shape
OUT['frames'] = int(n); OUT['hw'] = [int(H), int(Wd)]
still = np.array(Image.open(W + '/still.png').convert('RGB'))
from skimage.exposure import match_histograms
hm = np.stack([np.clip(np.rint(match_histograms(f, still, channel_axis=-1)), 0, 255).astype(np.uint8) for f in fr])
def reg(a):
    return a[:, 480:700, 80:320, :].mean(axis=(1, 2))
def pcts(sw):
    b = sw.mean(1)
    return (b / b[0] - 1) * 100
for nm, arr in (('raw', fr), ('hm', hm)):
    sw = reg(arr)
    p = pcts(sw)
    red = (sw[:, 0] / sw[0, 0] - 1) * 100
    pick = [i for i in (0, 40, 80, 120, 160) if i < n] + [n - 1]
    OUT['drift_' + nm] = {'mean_rgb_pct_at': {str(i): round(float(p[i]), 1) for i in pick}, 'first_to_last_pct': round(float(p[-1]), 2),
                          'min_pct': round(float(p.min()), 1), 'red_first_to_last_pct': round(float(red[-1]), 2),
                          'rgb_first': [round(float(x), 1) for x in sw[0]], 'rgb_last': [round(float(x), 1) for x in sw[-1]]}
d = np.abs(np.diff(hm.astype(np.float32).mean(axis=3), axis=0)).mean(axis=(1, 2))
OUT['hm_step_mean_max'] = [round(float(d.mean()), 2), round(float(d.max()), 2)]
# deliverable: hist-matched clip with narration
import imageio
tmp = W + '/narr_hm.silent.mp4'
imageio.mimsave(tmp, list(hm), fps=FPS, codec='libx264', macro_block_size=None, ffmpeg_params=['-crf', '18', '-preset', 'veryfast', '-pix_fmt', 'yuv420p'])
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', tmp, '-i', W + '/narr.wav', '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '96k', '-shortest', W + '/narr_hm.mp4'])
OUT['t_basic_s'] = round(time.time() - t0, 1)
json.dump(OUT, open(W + '/narr_post.json', 'w'), indent=1)
try:
    import librosa
    from scipy.signal import find_peaks
    import mediapipe as mp
    y, sr = librosa.load(W + '/narr.wav', sr=16000)
    hop = 160
    rms = librosa.feature.rms(y=y, frame_length=400, hop_length=hop, center=True)[0]
    ta_ = np.arange(len(rms)) * hop / sr
    def sm(x, k):
        return np.convolve(x, np.ones(k) / k, mode='same')
    env = sm(rms, 5)
    # landmarks: solutions API (old mediapipe) -> tasks API (model download) -> OpenCV fallback
    L = [None] * n
    METHOD = 'none'
    try:
        if hasattr(mp, 'solutions'):
            fm = mp.solutions.face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True)
            for i, f in enumerate(fr):
                res = fm.process(f)
                if res.multi_face_landmarks:
                    L[i] = np.array([[p.x * Wd, p.y * H] for p in res.multi_face_landmarks[0].landmark])
            METHOD = 'mediapipe-solutions'
        else:
            import urllib.request
            mp_path = W + '/face_landmarker.task'
            if not os.path.exists(mp_path):
                urllib.request.urlretrieve('https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task', mp_path)
            from mediapipe.tasks import python as mpt
            from mediapipe.tasks.python import vision as mpv
            opts = mpv.FaceLandmarkerOptions(base_options=mpt.BaseOptions(model_asset_path=mp_path), running_mode=mpv.RunningMode.IMAGE, num_faces=1)
            det = mpv.FaceLandmarker.create_from_options(opts)
            for i, f in enumerate(fr):
                res = det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(f)))
                if res.face_landmarks:
                    L[i] = np.array([[p.x * Wd, p.y * H] for p in res.face_landmarks[0]])
            METHOD = 'mediapipe-tasks'
    except Exception:
        OUT['landmark_error'] = traceback.format_exc()[-600:]
    OUT['landmark_method'] = METHOD
    OUT['face_detected_frames'] = int(sum(x is not None for x in L))
    def dist(P, a, b):
        return float(np.linalg.norm(P[a] - P[b]))
    op = np.full(n, np.nan); r1 = np.full(n, np.nan); r2 = np.full(n, np.nan)
    FB = None
    if OUT['face_detected_frames'] < n * 0.8:
        import cv2
        casc = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        g0 = cv2.cvtColor(fr[0], cv2.COLOR_RGB2GRAY)
        fcs = casc.detectMultiScale(g0, 1.1, 5)
        if not len(fcs):
            fcs = [(int(Wd * 0.2), int(H * 0.12), int(Wd * 0.6), int(H * 0.3))]
            OUT['haar_failed_default_box'] = True
        if len(fcs):
            x, y, w_, h_ = max(fcs, key=lambda q: q[2] * q[3])
            FB = (int(x + 0.25 * w_), int(y + 0.64 * h_), int(x + 0.75 * w_), int(y + 0.92 * h_))
            OUT['fallback_mouth_box'] = FB
            gray = np.stack([cv2.cvtColor(f, cv2.COLOR_RGB2GRAY) for f in fr]).astype(np.float32)
            bx = gray[:, FB[1]:FB[3], FB[0]:FB[2]]
            thr_ = np.percentile(bx[0], 15) * 0.75
            op = (bx < thr_).mean(axis=(1, 2))
            METHOD = 'opencv-dark-fraction'
            OUT['landmark_method'] = METHOD
    for i, P in enumerate(L):
        if P is None:
            continue
        fw = dist(P, 234, 454)
        op[i] = dist(P, 13, 14) / fw
        r1[i] = dist(P, 33, 263) / fw
        r2[i] = dist(P, 10, 152) / fw
    idx = np.arange(n)
    for a in (op, r1, r2):
        bad = np.isnan(a)
        if bad.any() and (~bad).any():
            a[bad] = np.interp(idx[bad], idx[~bad], a[~bad])
    if not np.isnan(r1).all():
      OUT['identity_geometry'] = {'eye_span_over_face_w': [round(float(r1.mean()), 4), round(float(r1.std() / r1.mean() * 100), 2)],
                                'face_h_over_w': [round(float(r2.mean()), 4), round(float(r2.std() / r2.mean() * 100), 2)],
                                'note': 'mean, std in percent of mean; low std means same face geometry throughout'}
    tv = idx / FPS
    grid = np.arange(0.0, min(tv[-1], ta_[-1]), 0.01)
    a = np.interp(grid, ta_, env)
    m = np.interp(grid, tv, op)
    def z(x):
        return (x - x.mean()) / (x.std() + 1e-9)
    def xc(a_, m_):
        lags = np.arange(-40, 41)
        out = []
        for L_ in lags:
            if L_ >= 0:
                x, yv = a_[:len(a_) - L_], m_[L_:]
            else:
                x, yv = a_[-L_:], m_[:len(m_) + L_]
            out.append(float(np.corrcoef(x, yv)[0, 1]))
        out = np.array(out)
        k = int(out.argmax())
        return int(lags[k] * 10), round(float(out[k]), 3), round(float(out[40]), 3)
    OUT['xcorr_full_best_lag_ms_corr_corr0'] = xc(z(a), z(m))
    th = len(a) // 3
    OUT['xcorr_thirds'] = [xc(z(a[i * th:(i + 1) * th + 0]), z(m[i * th:(i + 1) * th])) for i in range(3)]
    OUT['note_lag'] = 'positive lag = mouth moves later than the sound. Video frame time resolution is 62.5 ms (16 fps).'
    # speech span
    spk = np.where(env > 0.1 * env.max())[0]
    OUT['speech_span_s'] = [round(float(ta_[spk[0]]), 2), round(float(ta_[spk[-1]]), 2)]
    # peaks (open vowels): strongest 5 envelope peaks >= 0.6 s apart
    pk, _ = find_peaks(env, distance=60, prominence=0.15 * env.max())
    top = sorted(pk, key=lambda k: -env[k])[:5]
    top = sorted(top)
    lo, hi = float(np.percentile(op, 5)), float(np.percentile(op, 95))
    peaks = []
    for k in top:
        t_a = ta_[k]
        sel = (grid >= t_a - 0.25) & (grid <= t_a + 0.25)
        gi = np.where(sel)[0]
        km = gi[int(np.argmax(m[gi]))]
        peaks.append({'audio_t_s': round(float(t_a), 2), 'mouth_peak_t_s': round(float(grid[km]), 2), 'offset_ms': int(round((grid[km] - t_a) * 1000)),
                      'open_rel_0to1': round(float((m[km] - lo) / (hi - lo + 1e-9)), 2)})
    OUT['vowel_peaks'] = peaks
    # onsets (plosive/word starts after >=120 ms silence)
    thr = 0.12 * env.max()
    sil = env < thr
    ons = []
    k = 12
    while k < len(env) - 30:
        if (not sil[k]) and sil[k - 12:k].all():
            ons.append(k)
            k += 40
        k += 1
    ons = ons[:5]
    onr = []
    for k in ons:
        t_a = ta_[k]
        sel = (grid >= t_a - 0.3) & (grid <= t_a + 0.45)
        gi = np.where(sel)[0]
        seg = m[gi]
        base = float(np.percentile(seg, 10)); topv = float(seg.max())
        cross = np.where(seg > base + 0.35 * (topv - base))[0]
        tm = grid[gi[cross[0]]] if len(cross) else float('nan')
        onr.append({'audio_onset_s': round(float(t_a), 2), 'mouth_open_onset_s': round(float(tm), 2), 'offset_ms': int(round((tm - t_a) * 1000)) if tm == tm else None})
    OUT['onsets'] = onr
    offs = [p['offset_ms'] for p in peaks] + [o['offset_ms'] for o in onr if o['offset_ms'] is not None]
    OUT['median_offset_ms'] = int(np.median(offs)) if offs else None
    # sheets
    def crop(i):
        P = L[min(max(i, 0), n - 1)]
        if P is None and any(x is not None for x in L):
            P = next(x for x in L if x is not None)
        if P is None:
            fb = FB or (Wd // 4, H // 3, Wd * 3 // 4, H // 2)
            return Image.fromarray(hm[min(max(i, 0), n - 1)][fb[1]:fb[3], fb[0]:fb[2]]).resize((150, 105))
        cx, cy = P[[13, 14]].mean(axis=0)
        mw = dist(P, 61, 291)
        x0, x1 = int(cx - mw * 1.0), int(cx + mw * 1.0)
        y0, y1 = int(cy - mw * 0.7), int(cy + mw * 0.7)
        x0, y0 = max(x0, 0), max(y0, 0)
        c = Image.fromarray(hm[min(max(i, 0), n - 1)][y0:y1, x0:x1]).resize((150, 105))
        return c
    def sheet(times, off0, name, ncol=5):
        rows = []
        S = Image.new('RGB', (ncol * 150, len(times) * 105), (0, 0, 0))
        dr = ImageDraw.Draw(S)
        for r_, t_ in enumerate(times):
            f0 = int(round(t_ * FPS))
            for c_ in range(ncol):
                fi = f0 + off0 + c_
                S.paste(crop(fi), (c_ * 150, r_ * 105))
                dr.text((c_ * 150 + 3, r_ * 105 + 3), '%dms' % int(round((fi / FPS - t_) * 1000)), fill=(255, 255, 0))
        S.save(W + '/' + name)
    sheet([p['audio_t_s'] for p in peaks], -2, 'narr_peaks.png')
    if ons:
        sheet([o['audio_onset_s'] for o in onr], -1, 'narr_onsets.png')
    # plot
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 3))
    ax.plot(grid, z(a), label='audio loudness')
    ax.plot(grid, z(m), label='mouth opening')
    ax.set_xlabel('s'); ax.legend(); fig.tight_layout(); fig.savefig(W + '/narr_sync.png', dpi=80)
    # identity sheet
    ids = [i for i in (0, 40, 80, 120, 160) if i < n] + [n - 1]
    S = Image.new('RGB', (len(ids) * 200, 360))
    for c_, i in enumerate(ids):
        S.paste(Image.fromarray(hm[i]).resize((200, 360)), (c_ * 200, 0))
    S.save(W + '/narr_face.png')
except Exception:
    OUT['lipsync_error'] = traceback.format_exc()[-1500:]
OUT['t_total_s'] = round(time.time() - t0, 1)
json.dump(OUT, open(W + '/narr_post.json', 'w'), indent=1)
print(json.dumps(OUT))
