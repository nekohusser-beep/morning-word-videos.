import subprocess, os, time, json, shutil, datetime
W = '/kaggle/working'
os.chdir(W)
L = W + '/ls.log'
T0 = time.time()
R = {'step_s': {}}
def say(m):
    open(L, 'a').write(time.strftime('%H:%M:%S ') + m + '\n')
def sh(c, env=None, t=None):
    r = subprocess.run(c, shell=True, capture_output=True, text=True, env=env, timeout=t)
    return r.returncode, (r.stdout + r.stderr)
def step(n, t0):
    R['step_s'][n] = round(time.time() - t0, 1)
    json.dump(R, open(W + '/ls_result.json', 'w'), indent=1)
open(L, 'w').close()
say('lsync job start')
RAW = 'https://raw.githubusercontent.com/nekohusser-beep/morning-word-videos./main/ref/ls/'
t = time.time()
for f in ['base_t01_32s.mp4', 'narr_test.wav']:
    rc, o = sh('curl -sSL -o %s %s%s' % (f, RAW, f))
    say('fetch %s rc=%d size=%d' % (f, rc, os.path.getsize(f)))
step('fetch', t)
# python 3.10 env via uv
t = time.time()
rc, o = sh('pip install -q uv 2>&1 | tail -1'); say('uv rc=%d %s' % (rc, o[-100:]))
rc, o = sh('uv venv --python 3.10 %s/lsenv 2>&1 | tail -3' % W); say('venv rc=%d %s' % (rc, o[-300:]))
PY = W + '/lsenv/bin/python'
if not os.path.exists(PY):
    say('NO 3.10 venv'); R['error'] = 'venv failed: ' + o[-300:]; step('venv', t); raise SystemExit
rc, o = sh('[ -d LatentSync ] || git clone --depth 1 https://github.com/bytedance/LatentSync.git 2>&1 | tail -1'); say('clone rc=%d' % rc)
step('venv_clone', t)
t = time.time()
rc, o = sh('cd LatentSync && uv pip install --python %s -r requirements.txt 2>&1 | tail -6' % PY)
say('pip requirements rc=%d tail=%s' % (rc, o[-500:].replace('\n', ' | ')))
rc, o = sh('(ldconfig -p | grep -q libGL.so.1) && echo have_libgl || (apt-get install -y -qq libgl1 2>&1 | tail -1)')
say('libgl: ' + o.strip()[-100:])
step('install', t)
t = time.time()
rc, o = sh('''%s -c "
from huggingface_hub import hf_hub_download
for f in ['whisper/tiny.pt','latentsync_unet.pt']:
    p=hf_hub_download('ByteDance/LatentSync-1.5', f, local_dir='%s/LatentSync/checkpoints'); print(p)
" 2>&1 | tail -4''' % (PY, W))
say('checkpoints rc=%d %s' % (rc, o[-300:].replace('\n', ' | ')))
step('checkpoints', t)
# GPU memory sampler
import threading
peak = [0]; stop = [False]
def samp():
    while not stop[0]:
        rc, o = sh('nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits')
        try: peak[0] = max(peak[0], max(int(x) for x in o.split()))
        except Exception: pass
        time.sleep(3)
th = threading.Thread(target=samp, daemon=True); th.start()
t = time.time()
env = dict(os.environ); env['PYTHONPATH'] = W + '/LatentSync'; env['CUDA_VISIBLE_DEVICES'] = '0'; env['MPLBACKEND'] = 'agg'
cmd = ('cd LatentSync && %s -m scripts.inference --unet_config_path configs/unet/stage2.yaml '
       '--inference_ckpt_path checkpoints/latentsync_unet.pt --inference_steps 20 --guidance_scale 1.5 '
       '--enable_deepcache --video_path %s/base_t01_32s.mp4 --audio_path %s/narr_test.wav '
       '--video_out_path %s/ls_out.mp4 > %s/ls_infer.log 2>&1') % (PY, W, W, W, W)
rc, o = sh(cmd, env=env)
stop[0] = True
R['infer_rc'] = rc; R['infer_wall_s'] = round(time.time() - t, 1); R['peak_gpu_mib'] = peak[0]
say('inference rc=%d wall=%.0fs peak=%d MiB' % (rc, time.time() - t, peak[0]))
R['infer_tail'] = open(W + '/ls_infer.log').read()[-1500:]
step('inference', t)
ok = os.path.exists(W + '/ls_out.mp4')
if ok:
    rc, o = sh('ffprobe -v error -show_entries stream=codec_type,width,height,r_frame_rate,duration -of csv=p=0 ls_out.mp4')
    R['out_probe'] = o.strip()
    # loudness-normalise to -14 LUFS (two-pass) keeping video as is
    rc, o = sh('ffmpeg -hide_banner -i ls_out.mp4 -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1')
    import re
    m = re.search(r'\{[^{}]*"input_i"[^{}]*\}', o, re.S)
    af = 'loudnorm=I=-14:TP=-1.5:LRA=11'
    if m:
        j = json.loads(m.group(0))
        af += ':measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true' % (j['input_i'], j['input_tp'], j['input_lra'], j['input_thresh'], j['target_offset'])
    sh('ffmpeg -y -loglevel error -i ls_out.mp4 -af "%s" -ar 48000 -c:v copy -c:a aac -b:a 160k ls_final.mp4' % af)
    R['final_bytes'] = os.path.getsize(W + '/ls_final.mp4') if os.path.exists(W + '/ls_final.mp4') else None
R['total_s'] = round(time.time() - T0, 1)
json.dump(R, open(W + '/ls_result.json', 'w'), indent=1)
# push
try:
    from kaggle_secrets import UserSecretsClient
    tok = UserSecretsClient().get_secret('GITHUB_TOKEN')
    sh('rm -rf hw; git clone --depth 1 https://github.com/nekohusser-beep/morning-word-videos. hw 2>&1 | tail -1')
    os.makedirs('hw/episodes', exist_ok=True)
    for src, dst in (('ls_final.mp4', 'lsync_test.mp4'), ('ls_out.mp4', 'lsync_test_raw.mp4'), ('ls_result.json', 'lsync_test.json'), ('ls.log', 'lsync_test.log'), ('ls_infer.log', 'lsync_test.infer.log')):
        if os.path.exists(src):
            shutil.copy(src, 'hw/episodes/' + dst)
    sh("cd hw && git add episodes && git -c user.name=kaggle-handoff -c user.email=kaggle@example.invalid commit -qm 'lsync test run'")
    e2 = dict(os.environ); e2['GIT_TERMINAL_PROMPT'] = '0'
    rc, o = sh('cd hw && git push https://x-access-token:%s@github.com/nekohusser-beep/morning-word-videos. HEAD:main 2>&1 | sed "s/%s/***/g" | tail -2' % (tok, tok), env=e2)
    say('push rc=%d %s' % (rc, o[-200:]))
except Exception as e:
    say('push failed ' + repr(e)[:300])
say('lsync job done %.1f min' % ((time.time() - T0) / 60))
