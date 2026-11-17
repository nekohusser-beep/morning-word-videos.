"""Dump every upload of a channel with yt-dlp (no API key). Usage: dump.py @handle outdir"""
import json, subprocess, sys, os, csv
h, out = sys.argv[1].lstrip('@'), sys.argv[2]
os.makedirs(out, exist_ok=True)
def run(args):
    r = subprocess.run(['yt-dlp', '--ignore-errors', '--no-warnings'] + args, capture_output=True, text=True)
    return [json.loads(l) for l in r.stdout.splitlines() if l.strip().startswith('{')]
ids = {}
for tab in ('videos', 'shorts', 'streams'):
    for e in run(['--flat-playlist', '-j', f'https://www.youtube.com/@{h}/{tab}']):
        ids.setdefault(e['id'], dict(id=e['id'], tab=tab, title=e.get('title'), views=e.get('view_count'), duration=e.get('duration')))
print('listed', len(ids), {t: sum(1 for v in ids.values() if v['tab'] == t) for t in ('videos', 'shorts', 'streams')})
full = 0
with open(f'{out}/videos.jsonl', 'w') as f:
    for i, v in enumerate(ids.values()):
        d = run(['-j', '--skip-download', f'https://www.youtube.com/watch?v={v["id"]}'])
        if d:
            d = d[0]; full += 1
            v.update(date=d.get('upload_date'), views=d.get('view_count'), likes=d.get('like_count'), comments=d.get('comment_count'),
                     duration=d.get('duration'), tags=d.get('tags'), description=d.get('description'), chapters=[c.get('title') for c in (d.get('chapters') or [])])
        f.write(json.dumps(v) + '\n')
        if i % 25 == 0: print(i, 'done', full, 'full', flush=True)
with open(f'{out}/videos.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['date', 'tab', 'views', 'likes', 'comments', 'duration', 'title', 'id'])
    for v in sorted(ids.values(), key=lambda x: x.get('date') or '', reverse=True):
        w.writerow([v.get('date'), v['tab'], v.get('views'), v.get('likes'), v.get('comments'), v.get('duration'), v.get('title'), v['id']])
print('TOTAL', len(ids), 'full metadata', full)
