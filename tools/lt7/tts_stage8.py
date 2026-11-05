import subprocess, sys, os, time, json
W = '/kaggle/working'
CB = W + '/cbdeps'
def sh(c, **k):
    r = subprocess.run(c, shell=True, capture_output=True, **k)
    return r.returncode, (r.stdout + r.stderr).decode('utf8', 'replace')
def say(m):
    open(W + '/job8.log', 'a').write(time.strftime('%H:%M:%S ') + m + '\n')
os.makedirs(CB, exist_ok=True)
t = time.time()
rc, o = sh('pip install -q --no-deps --target %s chatterbox-tts "transformers==4.46.3" "tokenizers==0.20.3" "diffusers==0.29.0" s3tokenizer resemble-perth conformer pykakasi' % CB)
say('cb install rc=%d %s' % (rc, o[-300:].replace('\n', ' ')))
PIPMAP = {'perth': 'resemble-perth', 'pkg_resources': 'setuptools<81', 'yaml': 'pyyaml', 'cv2': 'opencv-python-headless', 'PIL': 'pillow'}
TEXT = open(W + '/narr_text.txt').read().strip()
env = dict(os.environ)
env['PYTHONPATH'] = CB
ok = False
for i in range(40):
    rc, o = sh('python %s/tts8.py %s/narr_text.txt %s/ref10.wav %s/tts_raw.wav' % (W, W, W, W), env=env)
    say('tts try %d rc=%d tail=%s' % (i, rc, o[-300:].replace('\n', ' | ')))
    if rc == 0 and os.path.exists(W + '/tts_raw.wav'):
        ok = True
        break
    import re
    mm = re.search(r"No module named '([^']+)'", o)
    if mm:
        root = mm.group(1).split('.')[0]
        r2, o2 = sh('pip install -q --no-deps --target %s "%s"' % (CB, PIPMAP.get(root, root)))
        say('heal %s rc=%d %s' % (root, r2, o2[-150:].replace('\n', ' ')))
        continue
    break
say('TTS ok=%s in %.0fs' % (ok, time.time() - t))
open(W + '/tts_ok.txt', 'w').write('1' if ok else '0')
