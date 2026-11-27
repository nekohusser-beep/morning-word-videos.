#!/usr/bin/env python3
"""Dec 18-24 2026: 7 morning + 7 night cards, same builder as batch.py. Christmas week: Dec 22-24 lean into Christmas.
Verses picked from the Nov 26 trend brief movers (Prov 16:3, James 1:5, Col 3:17, Ps 46:10, Ps 50:15, Ps 127:1)."""
import json, datetime, itertools, re, sys
sys.argv = ['x']; src = open('batch.py').read().split('MORNING = [')[0]
exec(src)  # verse(), spoken(), shown(), n2w
exec('PSALM_PART' + open('batch.py').read().split('PSALM_PART', 1)[1].split('def split_verse')[0])
exec('def split_verse' + open('batch.py').read().split('def split_verse', 1)[1].split('start = ')[0])
MORNING = [
 ('Proverbs 16:3', "Good morning. Got a lot on your plate today? Hand it over first.", "Give him the work before you start it, and your mind gets steady.", "Lord, I'm handing you everything I have to do today. Settle my thoughts. In Jesus' name, amen."),
 ('James 1:5', "Good morning. Don't know what to do about something? Ask.", "He doesn't make you feel dumb for asking. He just gives.", "Lord, I need wisdom today. I'm asking you for it. In Jesus' name, amen."),
 ('Colossians 3:17', "Good morning. Before the day gets busy, hear this.", "The small stuff counts too. Do it in his name.", "Lord, let everything I say and do today be in your name. In Jesus' name, amen."),
 ('Isaiah 43:2', "Good morning. Walking into a hard week? This is for you.", "He didn't promise you'd never go through it. He promised you wouldn't go through it alone.", "Lord, go through this with me today. Keep me from being overwhelmed. In Jesus' name, amen."),
 ('Isaiah 9:6', "Good morning. Christmas is three days out. Hear who it's about.", "Before the gifts and the noise, remember the child who came for you.", "Lord, thank you for sending your Son. Be my peace today. In Jesus' name, amen."),
 ('Luke 2:10-11', "Good morning. Holidays feel heavy this year? Hear what the angel said.", "The first Christmas news started with fear not. It still does.", "Lord, thank you for the good tidings. Give me your joy today. In Jesus' name, amen."),
 ('Matthew 1:21', "Good morning. It's Christmas Eve. Here's why the name matters.", "His name tells you what he came to do. He came to save.", "Lord Jesus, thank you for coming to save me. I'm yours today. In Jesus' name, amen."),
]
NIGHT = [
 ('Psalms 46:10', "Mind still racing tonight? Hear this.", "Still doesn't mean you quit. It means you let him be God for the night.", "Lord, I'm being still tonight. You are God, and I'm not. In Jesus' name, amen."),
 ('Psalms 50:15', "Trouble on your mind tonight? Read this before bed.", "He didn't say figure it out. He said call on me.", "Lord, I'm calling on you tonight. Deliver me, and I'll give you the glory. In Jesus' name, amen."),
 ('Psalms 127:1', "Been holding it all together by yourself? Hear this tonight.", "You can stop guarding everything. Let him keep watch tonight.", "Lord, build my house and keep watch over it tonight. In Jesus' name, amen."),
 ('Psalms 121:7', "Before you close your eyes, hear this over your house.", "All evil. Not some of it. He keeps your soul tonight.", "Lord, preserve me and my family tonight from all evil. In Jesus' name, amen."),
 ('Psalms 85:8', "Too much noise in your head tonight? Hear this.", "Turn the noise down and listen. He speaks peace to his people.", "Lord, speak peace to me tonight. I'm listening. In Jesus' name, amen."),
 ('Psalms 98:4', "Two nights before Christmas. End the day with this one.", "Joy to the World was written from this psalm. Let it be your last song tonight.", "Lord, thank you for coming into the world. Fill my heart with joy tonight. In Jesus' name, amen."),
 ('Psalms 130:5-6', "It's Christmas Eve. Waiting on something tonight? This is for you.", "The watchmen waited all night for morning. Morning always came. So did he.", "Lord, I'm waiting on you tonight. Thank you for keeping every promise. In Jesus' name, amen."),
]
MC = ['m-birds0.mp4','m-lake0.mp4','m-water1.mp4','m-forest1.mp4','m-eagle0.mp4','m-lake2.mp4','m-birds1.mp4','m-lake1.mp4','m-forest0.mp4','m-water0.mp4','m-eagle1.mp4','m-birds2.mp4']
NC = ['n-moon0.mp4','n-moon2.mp4','n-stars2.mp4','n-candle1.mp4','n-moon1.mp4','n-lake0.mp4','n-ocean1.mp4','n-stars0.mp4','n-candle0.mp4','n-ocean0.mp4','n-stars1.mp4']
start = datetime.date(2026, 12, 18)
for i, (ref, opener, line, prayer) in enumerate(MORNING):
    d = start + datetime.timedelta(days=i); t = verse(ref); parts = split_verse(t); k = (i + 29) % 12; clips = itertools.cycle(MC[k:] + MC[:k])
    L = [{'say': opener, 'big': 'Good morning.', 'small': opener.replace('Good morning. ', ''), 'clip': next(clips), 'ss': 0.5}]
    for j, p in enumerate(parts):
        last = j == len(parts) - 1
        L.append({'say': p + (' ' + spoken(ref) + '.' if last else ''), 'big': p, 'small': shown(ref) if last else '', 'clip': next(clips), 'ss': 0.5})
    L += [{'say': line, 'big': line, 'small': '', 'clip': next(clips), 'ss': 0.5},
          {'say': prayer, 'big': "In Jesus' name, amen.", 'small': '', 'clip': next(clips), 'ss': 0.5},
          {'say': "Have a blessed day. Type amen, and send this to somebody starting their day.", 'big': 'Have a blessed day.', 'small': 'Type amen, and send this to somebody starting their day', 'clip': next(clips), 'ss': 0.5}]
    json.dump({'brand': 'BLESSED MORNING', 'ref': ref, 'kjv': t, 'lines': L}, open(f'eps/m-{d}.json', 'w'), indent=1, ensure_ascii=False); print('m', d, ref, len(parts))
for i, (ref, opener, line, prayer) in enumerate(NIGHT):
    d = start + datetime.timedelta(days=i); t = verse(ref); parts = split_verse(t); k = (i + 29) % 11; clips = itertools.cycle(NC[k:] + NC[:k])
    ps = int(re.match(r'Psalms (\d+)', ref).group(1)); vid, rng = next((v, r) for top, v, r in PSALM_PART if ps <= top)
    L = [{'say': opener, 'big': opener.split('?')[0].split('.')[0], 'small': '', 'clip': next(clips), 'ss': 0.5}]
    for j, p in enumerate(parts):
        last = j == len(parts) - 1
        L.append({'say': p + (' ' + spoken(ref) + '.' if last else ''), 'big': p, 'small': shown(ref) if last else '', 'clip': next(clips), 'ss': 0.5})
    L += [{'say': line, 'big': line, 'small': '', 'clip': next(clips), 'ss': 0.5},
          {'say': prayer, 'big': "In Jesus' name, amen.", 'small': '', 'clip': next(clips), 'ss': 0.5},
          {'say': f"Want the Word playing while you sleep? Psalms {rng.replace('–',' through ')}, read slowly, is on our channel. The link is in the description.", 'big': 'Fall asleep to the Word', 'small': f'Psalms {rng}, read slowly. Link in the description.', 'clip': next(clips), 'ss': 0.5}]
    json.dump({'brand': 'REST IN THE WORD', 'speed': 0.9, 'ref': ref, 'kjv': t, 'audio_bible': f'https://www.youtube.com/watch?v={vid}', 'audio_range': rng, 'lines': L}, open(f'eps/n-{d}.json', 'w'), indent=1, ensure_ascii=False); print('n', d, ref, len(parts))
