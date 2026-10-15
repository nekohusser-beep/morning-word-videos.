import subprocess, time, os, datetime, json
T0 = time.time()
os.chdir('/kaggle/working')
def sh(c, env=None):
    r = subprocess.run(c, shell=True, capture_output=True, text=True, env=env)
    return r.returncode, (r.stdout + r.stderr).strip()
R = {'kaggle_start_utc': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), 'steps': []}
URL = 'https://github.com/nekohusser-beep/morning-word-videos.'
rc, o = sh('rm -rf hw; git clone --depth 1 %s hw 2>&1 | tail -2' % URL)
R['steps'].append(['clone', rc, o[-200:]])
rc, o = sh('cd hw && git log --oneline | head -2; cat handoff_test.txt')
R['steps'].append(['pulled_file', rc, o])
stamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
sh("cd hw && printf ' — Kaggle wrote this at %s\\n' '%s' >> handoff_test.txt")
rc, o = sh('cd hw && cat handoff_test.txt')
R['steps'].append(['appended_file', rc, o])
sh('cp hw/handoff_test.txt /kaggle/working/handoff_test_out.txt')
rc, o = sh("cd hw && git -c user.name=kaggle-handoff -c user.email=kaggle@example.invalid commit -qam 'handoff test: Kaggle append' && git log --oneline | head -1")
R['steps'].append(['commit', rc, o])
tok = None
used = None
try:
    from kaggle_secrets import UserSecretsClient
    us = UserSecretsClient()
    for nm in ['GITHUB_TOKEN', 'GH_TOKEN', 'github_token', 'GITHUB_PAT', 'GH_PAT', 'github']:
        try:
            tok = us.get_secret(nm)
            used = nm
            break
        except Exception as e:
            R.setdefault('secret_errors', {})[nm] = repr(e)[:120]
except Exception as e:
    R['secrets_client_error'] = repr(e)[:200]
R['secret_found'] = used
e2 = dict(os.environ)
e2['GIT_TERMINAL_PROMPT'] = '0'
if tok:
    rc, o = sh('cd hw && git push https://x-access-token:%s@github.com/nekohusser-beep/morning-word-videos. HEAD:main 2>&1 | sed "s/%s/***/g" | tail -4' % (tok, tok), env=e2)
else:
    rc, o = sh('cd hw && git push origin HEAD:main 2>&1 | tail -4', env=e2)
R['steps'].append(['push_back', rc, o[-400:]])
R['git_ops_wall_s'] = round(time.time() - T0, 1)
R['kaggle_end_utc'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
json.dump(R, open('/kaggle/working/test2_result.json', 'w'), indent=1)
print(json.dumps(R, indent=1))
