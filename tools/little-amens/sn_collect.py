"""Collect SyncNet results (one entry per face track) into res/sync.json, plus each track's face box so tracks can be told apart."""
import glob, json, os, pickle, re
out = {}
for f in sorted(glob.glob('res/*.sync.log')):
    cid = os.path.basename(f)[:-9]
    t = open(f, errors='ignore').read()
    offs = re.findall(r'AV offset:\s*(-?\d+)', t); dist = re.findall(r'Min dist:\s*([\d.]+)', t); conf = re.findall(r'Confidence:\s*([\d.]+)', t)
    tracks = []
    try:
        tr = pickle.load(open(f'work/pywork/{cid}/tracks.pckl', 'rb'))
        for x in tr:
            p = x['proc_track']; tracks.append(dict(frames=[int(x['track']['frame'][0]), int(x['track']['frame'][-1])], x=round(float(sum(p['x']) / len(p['x']))), y=round(float(sum(p['y']) / len(p['y']))), s=round(float(sum(p['s']) / len(p['s'])))))
    except Exception as e:
        tracks = [dict(err=str(e))]
    out[cid] = [dict(offset=int(o), dist=float(d), conf=float(c), **(tracks[i] if i < len(tracks) else {})) for i, (o, d, c) in enumerate(zip(offs, dist, conf))]
json.dump(out, open('res/sync.json', 'w'), indent=1)
