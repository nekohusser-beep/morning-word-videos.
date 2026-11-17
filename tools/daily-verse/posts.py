import json, glob, os
out = []
for f in sorted(glob.glob('eps/[mn]-*.json')):
    e = json.load(open(f)); kind = os.path.basename(f)[0]; d = os.path.basename(f)[2:-5]
    ref = e.get('ref') or ('Lamentations 3:22-23' if kind == 'm' else 'Psalms 4:8'); r = ref.replace('Psalms ', 'Psalm ')
    kjv = e.get('kjv') or ' '.join(l['big'] for l in e['lines'] if l.get('small','').endswith('(KJV)') or 'LORD' in l['big'])
    i = int(d[-2:])
    if kind == 'm':
        title = (f"Morning Prayer for Today | {r} KJV" if i % 2 else f"Good Morning Bible Verse | {r} KJV")
        hook = e['lines'][0]['say']; line = [l['say'] for l in e['lines'] if l['big'] == l['say']][0] if any(l['big'] == l['say'] for l in e['lines']) else ''
        desc = f"{hook}\n\n\"{kjv}\" {r} (KJV)\n\n{line}\n\nHave a blessed day. Type amen, and send this to somebody starting their day.\n\nNarration: AI-generated voice. The Word is real.\n\n#MorningPrayer #BibleVerse #KJV #BlessedPrayers #shorts"
        file = f'Blessed-Morning-{d}.mp4'; at = f'{d}T05:00:00-05:00'
    else:
        title = (f"Night Prayer Before Sleep | {r} KJV" if i % 2 else f"Night Prayer Today | {r} KJV")
        hook = e['lines'][0]['say']; rng = e.get('audio_range', '1–31'); link = e.get('audio_bible', 'https://www.youtube.com/watch?v=BFwsZGyPw70')
        desc = f"{hook}\n\n\"{kjv}\" {r} (KJV)\n\nFall asleep to the Word: Psalms {rng}, KJV, read slowly: {link}\n\nType amen, and send this to someone who can't sleep.\n\nNarration: AI-generated voice. The Word is real.\n\n#NightPrayer #BibleVersesForSleep #KJV #BlessedPrayers #shorts"
        file = f'Rest-In-The-Word-{d}.mp4'; at = f'{d}T19:30:00-05:00'
    out.append({'date': d, 'kind': kind, 'at': at, 'file': file, 'title': title, 'desc': desc, 'queued': False})
json.dump(out, open('posts.json', 'w'), indent=1, ensure_ascii=False); print(len(out)); print(out[0]['title']); print(out[0]['desc']); print(out[-1]['title']); print(out[-1]['desc'])
