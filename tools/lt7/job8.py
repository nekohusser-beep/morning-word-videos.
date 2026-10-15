import subprocess, os, time, shutil, sys, json

W = '/kaggle/working'
L = W + '/job8.log'


def say(m):
    open(L, 'a').write(time.strftime('%H:%M:%S ') + m + '\n')


def sh(c, **k):
    r = subprocess.run(c, shell=True, capture_output=True, **k)
    return r.returncode, (r.stdout + r.stderr).decode('utf8', 'replace')


os.chdir(W)
open(L, 'w').close()
T0 = time.time()
say('job8 start')
say('df: ' + sh('df -h /kaggle/working /kaggle/temp 2>&1 | tail -3')[1].replace('\n', ' | '))

rc, o = sh("pip install -q peft==0.15.1 librosa ftfy einops scipy 'transformers==4.52.3' 'huggingface_hub<1.0' "
           "omegaconf easydict 'diffusers==0.31.0' imageio imageio-ffmpeg regex safetensors sentencepiece "
           "opencv-python-headless pyyaml")
say('pip rc=%d %s' % (rc, o[-300:].replace('\n', ' ')))

# xfuser stub (sp_size=1), with all_gather on the sp group
sd = W + '/stubs/xfuser/core/distributed'
os.makedirs(sd, exist_ok=True)
open(W + '/stubs/xfuser/__init__.py', 'w').write('')
open(W + '/stubs/xfuser/core/__init__.py', 'w').write('')
open(sd + '/__init__.py', 'w').write('''class _G:
    def all_gather(self,x,dim=0,**k): return x
    def broadcast(self,x,*a,**k): return x
    def __getattr__(self,n): return lambda *a,**k: (a[0] if a else None)
def get_sequence_parallel_rank(): return 0
def get_sequence_parallel_world_size(): return 1
def get_sp_group(): return _G()
def initialize_model_parallel(**k): pass
def init_distributed_environment(**k): pass
''')

# inputs (fresh sessions are empty): Derrick's still + voice from the repo, cut the 4.9 s slice
RAW = 'https://raw.githubusercontent.com/nekohusser-beep/morning-word-videos./main/ref/'
if not os.path.exists(W + '/still.png'):
    say('still: %s' % sh('curl -sSL -o %s/still.png %sderrick-gray-still.png' % (W, RAW))[0])
if not os.path.exists(W + '/voice.mp3'):
    say('voice: %s' % sh('curl -sSL -o %s/voice.mp3 %sderrick_voice_sample.mp3' % (W, RAW))[0])
if not os.path.exists(W + '/clipA.wav'):
    say('clipA: %s' % sh('ffmpeg -y -loglevel error -ss 3 -t 4.9 -i %s/voice.mp3 -ar 16000 -ac 1 %s/clipA.wav' % (W, W))[1][-200:])
say('inputs: ' + sh('ls -l %s/still.png %s/voice.mp3 %s/clipA.wav' % (W, W, W))[1].replace('\n', ' | '))

# download root: most free space among candidates
best, bestfree = W + '/dl', 0
for c in ['/kaggle/temp', '/tmp', W]:
    try:
        os.makedirs(c, exist_ok=True)
        fr = shutil.disk_usage(c).free
        say('free %s = %.1f GB' % (c, fr / 1e9))
        if fr > bestfree:
            best, bestfree = c, fr
    except Exception as e:
        say('no %s %s' % (c, e))
DL = best + '/dl'
os.makedirs(DL, exist_ok=True)
say('download root ' + DL)

LT = W + '/LiveTalk'
if not os.path.isdir(LT):
    say('clone LiveTalk: %s' % sh('git clone --depth 1 https://github.com/GAIR-NLP/LiveTalk.git ' + LT)[0])
os.chdir(LT)
if not os.path.isdir(LT + '/OmniAvatar'):
    say('clone OmniAvatar: %s' % sh('git clone --depth 1 https://github.com/Omni-Avatar/OmniAvatar.git')[0])
rc, o = sh('bash scripts/add_patch.sh')
say('add_patch rc=%d' % rc)

# checkpoints
PC = LT + '/pretrained_checkpoints'
os.makedirs(PC, exist_ok=True)
OA = W + '/OmniAvatar/pretrained_models'


def link(dst, src):
    if os.path.islink(dst):
        os.remove(dst)
    if not os.path.exists(dst):
        os.symlink(src, dst)


from huggingface_hub import snapshot_download

wan_ok = all(os.path.exists(OA + '/Wan2.1-T2V-1.3B/' + f) for f in
             ['models_t5_umt5-xxl-enc-bf16.pth', 'Wan2.1_VAE.pth', 'google/umt5-xxl'])
t = time.time()
if wan_ok:
    link(PC + '/Wan2.1-T2V-1.3B', OA + '/Wan2.1-T2V-1.3B')
    say('Wan base reused from cache')
else:
    d = snapshot_download('Wan-AI/Wan2.1-T2V-1.3B', local_dir=DL + '/Wan2.1-T2V-1.3B', allow_patterns=['models_t5_umt5-xxl-enc-bf16.pth', 'Wan2.1_VAE.pth', 'google/*', 'config.json'])
    link(PC + '/Wan2.1-T2V-1.3B', d)
    say('Wan base DOWNLOADED %.0fs: %s' % (time.time() - t, os.listdir(d)))
w2v_ok = os.path.exists(OA + '/wav2vec2-base-960h/config.json')
if w2v_ok:
    link(PC + '/wav2vec2', OA + '/wav2vec2-base-960h')
    say('wav2vec reused from cache')
else:
    d = snapshot_download('facebook/wav2vec2-base-960h', local_dir=DL + '/wav2vec2', allow_patterns=['*.json', '*.bin', '*.safetensors', '*.txt'])
    link(PC + '/wav2vec2', d)
    say('wav2vec downloaded')
t = time.time()
try:
    from huggingface_hub import HfApi
    info = HfApi().model_info('GAIR/LiveTalk-1.3B-V0.1', files_metadata=True)
    say('LiveTalk files: ' + ', '.join('%s=%.2fGB' % (s.rfilename, (s.size or 0) / 1e9) for s in info.siblings))
except Exception as e:
    say('model_info failed ' + repr(e)[:200])
d = snapshot_download('GAIR/LiveTalk-1.3B-V0.1', local_dir=DL + '/LiveTalk-1.3B-V0.1')
link(PC + '/LiveTalk-1.3B-V0.1', d)
T_DL = time.time() - t
say('LiveTalk checkpoint ready in %.0fs: %s' % (T_DL, os.listdir(d)))

# config
cfg = open('configs/causal_inference.yaml').read()
rep = {'dtype: "bf16"': 'dtype: "fp16"',
       'image_path: examples/inference/example1.jpg': 'image_path: %s/still.png' % W,
       'audio_path: examples/inference/example1.wav': 'audio_path: %s/clipA.wav' % W,
       'prompt: "A realistic video of a person speaking directly to the camera. The individual maintains steady eye contact with clear, expressive facial features. Their facial expressions are naturally animated and emotionally engaging, with precise lip movements perfectly synchronized to their speech."':
           'prompt: "A man speaks calmly to camera, gentle head movement, natural expression. The camera remains steady."',
       'image_sizes_720: [[512,512]]': 'image_sizes_720: [[400,720],[720,720],[720,400]]'}
for a, b in rep.items():
    if a not in cfg:
        say('CONFIG KEY NOT FOUND: ' + a[:40])
    cfg = cfg.replace(a, b)
open('configs/t4.yaml', 'w').write(cfg)
say('config written; still=%s clipA=%s' % (os.path.exists(W + '/still.png'), os.path.exists(W + '/clipA.wav')))
shutil.copy(W + '/runner7.py', LT + '/runner7.py')
sh('curl -sSL -o %s/script8.txt https://raw.githubusercontent.com/nekohusser-beep/morning-word-videos./main/tools/lt7/script8.txt' % W)

TEXT = open(W + '/script8.txt').read().strip()
open(W + '/narr_text.txt', 'w').write(TEXT)
say('ref10: %s' % sh('ffmpeg -y -loglevel error -ss 0 -t 10 -i %s/voice.mp3 -ar 24000 -ac 1 %s/ref10.wav' % (W, W))[1][-200:])
shutil.copy(W + '/tts.py', W + '/tts.py.bak')
rc, o = sh('python %s/tts_stage8.py' % W)
say('tts_stage rc=%d %s' % (rc, o[-300:].replace('\n', ' | ')))
src = 'tts_raw.wav' if open(W + '/tts_ok.txt').read().strip() == '1' else 'FALLBACK'
if src == 'FALLBACK':
    say('CHATTERBOX FAILED -> fallback: real 10 s of the existing voice sample (not the script line)')
    sh('ffmpeg -y -loglevel error -ss 0 -t 10 -i %s/voice.mp3 -ar 16000 -ac 1 %s/tts_raw16.wav' % (W, W))
else:
    sh('ffmpeg -y -loglevel error -i %s/tts_raw.wav -ar 16000 -ac 1 %s/tts_raw16.wav' % (W, W))
dur_a = float(sh('ffprobe -v error -show_entries format=duration -of csv=p=0 %s/tts_raw16.wav' % W)[1].strip())
import math
dur = 5
while dur < dur_a + 0.8 and dur < 35:
    dur += 3
say('narration %.2f s (source %s) -> video_duration %d' % (dur_a, src, dur))
open(W + '/narr_dur.txt', 'w').write(str(dur))
open(W + '/narr_src.txt', 'w').write(src + ' %.2f' % dur_a)
sh('ffmpeg -y -loglevel error -i %s/tts_raw16.wav -af apad -t %d -ar 16000 -ac 1 %s/narr.wav' % (W, dur, W))
say('narr.wav: ' + sh('ls -l %s/narr.wav' % W)[1].strip())
say('narration stage done')
env = dict(os.environ)
env['CUDA_VISIBLE_DEVICES'] = '0'
env['PYTHONPATH'] = W + '/stubs:' + LT + ':' + LT + '/OmniAvatar'
env['TOKENIZERS_PARALLELISM'] = 'false'
say('RUN START (setup took %.0fs)' % (time.time() - T0))
t = time.time()
with open(W + '/run7.log', 'w') as f:
    p = subprocess.run([sys.executable, '-u', 'runner7.py'], cwd=LT, env=env, stdout=f, stderr=subprocess.STDOUT)
say('RUN END rc=%d wall=%.2f min' % (p.returncode, (time.time() - t) / 60))
rc, o = sh("pip install -q scikit-image scipy matplotlib 2>&1 | tail -1; (pip install -q mediapipe==0.10.21 2>&1 || pip install -q mediapipe 2>&1) | tail -2")
say('post deps rc=%d %s' % (rc, o[-200:].replace('\n', ' ')))
say('POST START')
P = subprocess.run([sys.executable, '-u', W + '/post8.py'], cwd=W, capture_output=True)
say('POST rc=%d %s' % (P.returncode, (P.stdout + P.stderr).decode('utf8', 'replace')[-600:].replace('\n', ' | ')))
say('job8 done total %.1f min; download %.0fs' % ((time.time() - T0) / 60, T_DL))
say('PUSH START')
P2 = subprocess.run([sys.executable, '-u', W + '/push8.py'], cwd=W, capture_output=True)
say('PUSH rc=%d %s' % (P2.returncode, (P2.stdout + P2.stderr).decode('utf8', 'replace')[-500:].replace('\n', ' | ')))
say('job8 all done')
