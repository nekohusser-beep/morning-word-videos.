import subprocess, os, json, datetime, time, shutil
os.chdir('/kaggle/working')
def sh(c, env=None):
    r = subprocess.run(c, shell=True, capture_output=True, text=True, env=env)
    return r.returncode, (r.stdout + r.stderr).strip()
t0 = time.time()
d = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=4)).strftime('%Y%m%d')
rc, o = sh('rm -rf hw; git clone --depth 1 https://github.com/nekohusser-beep/morning-word-videos. hw 2>&1 | tail -1')
os.makedirs('hw/episodes', exist_ok=True)
base = 'hw/episodes/test_episode_%s' % d
shutil.copy('final_normalized.mp4', base + '.mp4')
shutil.copy('captions.srt', base + '.srt')
shutil.copy('job8.log', base + '.job.log')
for f, n in (('post8.json', '.post.json'), ('lt_result7.json', '.livetalk.json')):
    if os.path.exists(f):
        shutil.copy(f, base + n)
tok = None
from kaggle_secrets import UserSecretsClient
tok = UserSecretsClient().get_secret('GITHUB_TOKEN')
sh("cd hw && git add episodes && git -c user.name=kaggle-handoff -c user.email=kaggle@example.invalid commit -qm 'test episode %s (Kaggle chain run)'" % d)
e2 = dict(os.environ); e2['GIT_TERMINAL_PROMPT'] = '0'
rc, o = sh('cd hw && git push https://x-access-token:%s@github.com/nekohusser-beep/morning-word-videos. HEAD:main 2>&1 | sed "s/%s/***/g" | tail -3' % (tok, tok), env=e2)
rc2, h = sh('cd hw && git log --oneline | head -1')
out = {'push_rc': rc, 'push_out': o[-300:], 'commit': h, 'push_wall_s': round(time.time() - t0, 1)}
json.dump(out, open('push8.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
