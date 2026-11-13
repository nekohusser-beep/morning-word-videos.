"""Pull every upload of a channel + transcripts via innertube (no key). Usage: tx.py @handle outdir [tabs]"""
import json, sys, os, re, time, urllib.request, concurrent.futures as cf
H = sys.argv[1].lstrip('@'); OUT = sys.argv[2]; TABS = (sys.argv[3] if len(sys.argv) > 3 else 'videos,shorts,streams').split(',')
os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36', 'Accept-Language': 'en-US,en'}
def get(u, data=None, hdr=None):
    for a in range(4):
        try:
            r = urllib.request.Request(u, data=json.dumps(data).encode() if data else None, headers={**UA, **(hdr or {}), **({'content-type': 'application/json'} if data else {})})
            return urllib.request.urlopen(r, timeout=30).read().decode('utf-8', 'replace')
        except Exception as e:
            time.sleep(2 + a * 3); err = e
    raise err
def walk(o, out, tab, st):
    if isinstance(o, dict):
        if 'lockupViewModel' in o:
            L = o['lockupViewModel']; md = (L.get('metadata') or {}).get('lockupMetadataViewModel') or {}
            rows = [p.get('text', {}).get('content') for r in ((md.get('metadata') or {}).get('contentMetadataViewModel') or {}).get('metadataRows', []) for p in r.get('metadataParts', [])]
            out.append(dict(id=L.get('contentId'), t=(md.get('title') or {}).get('content'), v=next((x for x in rows if x and 'view' in x), None), age=next((x for x in rows if x and 'ago' in x), None), tab=tab)); return
        if 'shortsLockupViewModel' in o:
            S = o['shortsLockupViewModel']; om = S.get('overlayMetadata') or {}
            vid = (((S.get('onTap') or {}).get('innertubeCommand') or {}).get('reelWatchEndpoint') or {}).get('videoId') or (S.get('entityId') or '')[-11:]
            out.append(dict(id=vid, t=(om.get('primaryText') or {}).get('content'), v=(om.get('secondaryText') or {}).get('content'), tab=tab)); return
        if 'continuationCommand' in o and not st.get('tok'): st['tok'] = o['continuationCommand']['token']
        for v in o.values(): walk(v, out, tab, st)
    elif isinstance(o, list):
        for v in o: walk(v, out, tab, st)
items = []
for tab in TABS:
    h = get(f'https://www.youtube.com/@{H}/{tab}')
    ver = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', h).group(1)
    d = json.loads(h.split('var ytInitialData = ')[1].split(';</script>')[0])
    out = []; st = {}; walk(d, out, tab, st)
    while st.get('tok'):
        t = st.pop('tok'); r = json.loads(get('https://www.youtube.com/youtubei/v1/browse?prettyPrint=false', {'context': {'client': {'clientName': 'WEB', 'clientVersion': ver, 'hl': 'en', 'gl': 'US'}}, 'continuation': t}))
        walk(r, out, tab, st)
    print(tab, len(out), flush=True); items += out
seen = set(); items = [x for x in items if x['id'] and not (x['id'] in seen or seen.add(x['id']))]
json.dump(items, open(f'{OUT}/list.json', 'w'))
def tx(it):
    j = json.loads(get('https://www.youtube.com/youtubei/v1/player?prettyPrint=false', {'context': {'client': {'clientName': 'ANDROID', 'clientVersion': '20.10.38', 'androidSdkVersion': 30, 'hl': 'en', 'gl': 'US'}}, 'videoId': it['id']}))
    vd = j.get('videoDetails') or {}; mf = (j.get('microformat') or {}).get('playerMicroformatRenderer') or {}
    tk = ((j.get('captions') or {}).get('playerCaptionsTracklistRenderer') or {}).get('captionTracks') or []
    t = next((x for x in tk if x.get('languageCode') == 'en'), tk[0] if tk else None); text = ''
    if t:
        x = get(re.sub(r'&fmt=[^&]+', '', t['baseUrl']) + '&fmt=json3')
        try: text = re.sub(r'\s+', ' ', ' '.join(''.join(s.get('utf8', '') for s in e['segs']) for e in json.loads(x).get('events', []) if e.get('segs')))
        except Exception: pass
    return {**it, 'status': (j.get('playabilityStatus') or {}).get('status'), 'views': vd.get('viewCount'), 'len': vd.get('lengthSeconds'), 'kw': vd.get('keywords'), 'date': mf.get('publishDate'), 'desc': vd.get('shortDescription'), 'text': text}
def safe(it):
    try: return tx(it)
    except Exception as e: return {**it, 'status': 'ERR '+str(e)[:80], 'text': ''}
ok = 0
with open(f'{OUT}/tx.jsonl', 'w') as f, cf.ThreadPoolExecutor(4) as ex:
    for i, r in enumerate(ex.map(safe, items)):
        f.write(json.dumps(r) + '\n'); ok += bool(r['text'])
        if i % 100 == 0: print(i, 'with text', ok, r.get('status'), flush=True)
print('TOTAL', len(items), 'with text', ok)
