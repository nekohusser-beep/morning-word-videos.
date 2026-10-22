import numpy as np, json, librosa
import mediapipe as mp
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision as mpv
from scipy.signal import butter, filtfilt
W = '/kaggle/working'
FPS = 16
fr = np.load(W + '/narr_frames.npy')
n, H, Wd, _ = fr.shape
det = mpv.FaceLandmarker.create_from_options(mpv.FaceLandmarkerOptions(base_options=mpt.BaseOptions(model_asset_path=W + '/face_landmarker.task'), running_mode=mpv.RunningMode.IMAGE, num_faces=1))
def lm(f):
    r = det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(f)))
    return np.array([[p.x * Wd, p.y * H] for p in r.face_landmarks[0]])
def d(P, a, b):
    return float(np.linalg.norm(P[a] - P[b]))
op = np.zeros(n)
ou = np.zeros(n)
for i in range(n):
    P = lm(fr[i])
    fw = d(P, 234, 454)
    op[i] = d(P, 13, 14) / fw
    ou[i] = d(P, 0, 17) / fw
y, sr = librosa.load(W + '/narr.wav', sr=16000)
rms = librosa.feature.rms(y=y, frame_length=400, hop_length=160, center=True)[0]
ta = np.arange(len(rms)) * 0.01
tv = np.arange(n) / FPS
grid = np.arange(0, min(tv[-1], ta[-1]), 0.01)
b, a = butter(3, 7 / 50.0)
def lp(x):
    return filtfilt(b, a, x)
A = lp(np.interp(grid, ta, rms))
def z(x):
    return (x - x.mean()) / (x.std() + 1e-9)
def best(x, y_, lo=-30, hi=30):
    out = []
    for L in range(lo, hi + 1):
        if L >= 0:
            u, v = x[:len(x) - L], y_[L:]
        else:
            u, v = x[-L:], y_[:len(y_) + L]
        out.append(np.corrcoef(u, v)[0, 1])
    out = np.array(out)
    k = int(out.argmax())
    return (lo + k) * 10, float(out[k])
res = {}
for nm, mo in (('inner', op), ('outer', ou)):
    M = lp(np.interp(grid, tv, mo))
    lag, c = best(z(A), z(M))
    res[nm] = {'full_best_lag_ms': lag, 'corr': round(c, 3)}
    curve = {}
    for L in range(-300, 301, 50):
        j = L // 10
        u, v = (z(A)[:len(A) - j], z(M)[j:]) if j >= 0 else (z(A)[-j:], z(M)[:len(M) + j])
        curve[str(L)] = round(float(np.corrcoef(u, v)[0, 1]), 3)
    res[nm]['curve_ms'] = curve
    wl = []
    for s in range(0, 560, 100):
        seg = slice(s, s + 400)
        lg, cc = best(z(A[seg]), z(M[seg]))
        wl.append([s / 100.0, lg, round(cc, 2)])
    res[nm]['windows_start_s_lag_ms_corr'] = wl
    rng = np.random.default_rng(0)
    null = []
    for _ in range(200):
        sh = int(rng.integers(200, 700))
        lg, cc = best(z(np.roll(A, sh)), z(M))
        null.append(cc)
    res[nm]['null_corr_mean_p95'] = [round(float(np.mean(null)), 3), round(float(np.percentile(null, 95)), 3)]
    lags = [w[1] for w in wl if w[2] > 0.3]
    res[nm]['median_lag_of_windows_corr_gt_0.3_ms'] = int(np.median(lags)) if lags else None
    res[nm]['n_windows_corr_gt_0.3'] = len(lags)
json.dump(res, open(W + '/narr_post7b.json', 'w'), indent=1)
for k, v in res.items():
    print(k, 'lag', v['full_best_lag_ms'], 'corr', v['corr'], 'null(mean,p95)', v['null_corr_mean_p95'], 'med_lag_good_windows', v['median_lag_of_windows_corr_gt_0.3_ms'], 'n_good', v['n_windows_corr_gt_0.3'])
    print(' windows', v['windows_start_s_lag_ms_corr'])
    print(' curve', v['curve_ms'])
