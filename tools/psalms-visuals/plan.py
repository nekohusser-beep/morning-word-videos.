import json
FPS = 1; T = 31716 * FPS            # 31716 frames
N = 66; XF = 12 * FPS               # 60-frame crossfade
HALF = XF // 2
B0 = 60 * FPS                       # first boundary at 60 s
BEND = T - 60 * FPS                 # last scene holds until 60 s before the end, then fades to black
B = [B0 + round(i * (BEND - B0) / N) for i in range(N + 1)]
segs = []
segs.append(dict(name='s_title', kind='static', img='/home/claude/pspack/proof/frames/1_first.png', frames=B0 - HALF))
for i in range(N):
    prev = '/home/claude/pspack/proof/frames/1_first.png' if i == 0 else f'scenes/scene_{i-1:02d}.png'
    cur = f'scenes/scene_{i:02d}.png'
    segs.append(dict(name=f'x_{i:02d}', kind='xfade', a=prev, b=cur, frames=XF))
    end = B[i + 1] - HALF if i < N - 1 else BEND
    segs.append(dict(name=f's_{i:02d}', kind='static', img=cur, frames=end - (B[i] + HALF)))
segs.append(dict(name='z_fade', kind='fadeout', img=f'scenes/scene_{N-1:02d}.png', frames=60 * FPS))
tot = sum(s['frames'] for s in segs)
assert tot == T, (tot, T)
assert all(s['frames'] > 0 for s in segs)
json.dump(segs, open('segs.json', 'w'), indent=1)
print(len(segs), 'segments', tot, 'frames', tot / FPS, 's; scene hold min/max s:',
      min(s['frames'] for s in segs if s['kind'] == 'static' and s['name'] != 's_title') / FPS,
      max(s['frames'] for s in segs if s['kind'] == 'static') / FPS)
