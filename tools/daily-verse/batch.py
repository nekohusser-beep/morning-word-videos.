#!/usr/bin/env python3
"""Make 29 morning + 29 night episode JSONs (Nov 19 - Dec 17 2026) with word-exact KJV from aruljohn/Bible-kjv."""
import json, os, re, urllib.request, datetime, itertools
KJV = '/home/claude/kjv'
def book(b):
    p = f'{KJV}/{b}.json'
    if not os.path.exists(p):
        urllib.request.urlretrieve(f'https://raw.githubusercontent.com/aruljohn/Bible-kjv/master/{b.replace(" ","")}.json', p)
    return json.load(open(p))
def verse(ref):
    m = re.match(r'(.+) (\d+):(\d+)(?:-(\d+))?$', ref); b, c, v1, v2 = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4) or m.group(3))
    ch = [x for x in book(b)['chapters'] if int(x['chapter']) == c][0]
    return ' '.join(x['text'] for x in ch['verses'] if v1 <= int(x['verse']) <= v2)
NUM = {1:'one',2:'two',3:'three',4:'four',5:'five',6:'six',7:'seven',8:'eight',9:'nine',10:'ten',11:'eleven',12:'twelve',13:'thirteen',14:'fourteen',15:'fifteen',16:'sixteen',17:'seventeen',18:'eighteen',19:'nineteen',20:'twenty',30:'thirty',40:'forty',50:'fifty',60:'sixty',70:'seventy',80:'eighty',90:'ninety'}
def n2w(n):
    if n in NUM: return NUM[n]
    if n < 100: return NUM[n//10*10] + ' ' + NUM[n%10]
    return NUM[n//100] + ' ' + ('hundred' if n%100==0 else n2w(n%100))
def spoken(ref):
    m = re.match(r'(.+) (\d+):(\d+)(?:-(\d+))?$', ref); b, c, v1, v2 = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
    if b == 'Psalms': b = 'Psalm'
    return f"{b} {n2w(c)}, verse {n2w(v1)}" if not v2 else f"{b} {n2w(c)}, verses {n2w(v1)} " + ("and " if int(v2) == v1 + 1 else "through ") + n2w(int(v2))
def shown(ref): return ref.replace('Psalms ', 'Psalm ') + ' (KJV)'

MORNING = [  # ref, opener, one personal line, prayer, closer target
 ('Psalms 5:3', "Good morning. Before you check one thing on that phone, hear this.", "David talked to God first and looked up after. Try it that way today.", "Lord, you get my first words this morning. Lead the rest of the day. In Jesus' name, amen."),
 ('Psalms 143:8', "Good morning. Not sure which way to go today? Start here.", "He doesn't hand you the whole map. He shows you the next step.", "Lord, show me the way I should walk today, and I'll walk it. In Jesus' name, amen."),
 ('Psalms 118:24', "Good morning. This one is short. Carry it with you.", "If he made today, nothing in it is going to surprise him.", "Lord, thank you for today. Help me be glad in it, even the hard parts. In Jesus' name, amen."),
 ('Isaiah 40:31', "Good morning. Running on empty already? Hear this.", "Eagles don't flap their way up. The wind carries them.", "Lord, I'm tired before I start. Renew my strength today. In Jesus' name, amen."),
 ('Philippians 4:13', "Good morning. Got a shift you don't feel ready for? This is for you.", "Paul wrote that from a jail cell. The strength showed up after he moved.", "Lord, I can't carry today on my own. Strengthen me through it. In Jesus' name, amen."),
 ('Joshua 1:9', "Good morning. If you're walking into something hard today, hear this.", "He didn't tell Joshua it would be easy. He told him who was going with him.", "Lord, go with me today, and take the fear out of my steps. In Jesus' name, amen."),
 ('Psalms 46:1', "Good morning. Whatever trouble is waiting today, hear this first.", "Not a help once things calm down. A present help, right in the middle of it.", "Lord, be my refuge and my strength today. I'm leaning on you. In Jesus' name, amen."),
 ('Proverbs 3:5-6', "Good morning. Overthinking already? Read this one slowly.", "You don't have to figure it all out before breakfast. Trust him with the part you can't see.", "Lord, I'm trusting you with what I don't understand. Direct my path today. In Jesus' name, amen."),
 ('Isaiah 41:10', "Good morning. If you woke up worried, this is for you.", "He said he'd hold you up. That means you don't have to hold it all together.", "Lord, hold me up today with your hand. Take this fear. In Jesus' name, amen."),
 ('Psalms 90:14', "Good morning. Ask for this before the day starts.", "Satisfied early means you don't spend the whole day chasing something to fill you.", "Lord, fill me with your mercy this morning, so I can be glad all day. In Jesus' name, amen."),
 ('Psalms 59:16', "Good morning. Start the day singing, even if it's just in your head.", "He was your refuge last night. He'll be the same today.", "Lord, I'll sing of your mercy this morning. Thank you for keeping me. In Jesus' name, amen."),
 ('Matthew 6:33', "Good morning. Bills on your mind already? Hear what Jesus said.", "Put him first and let him handle the list.", "Lord, I'm putting you first today. Take care of the rest. In Jesus' name, amen."),
 ('Psalms 37:5', "Good morning. Got plans today? Hand them over first.", "Committing it means you stop carrying it around in your pocket all day.", "Lord, I commit my way to you today. Bring it to pass your way. In Jesus' name, amen."),
 ('Psalms 121:1-2', "Good morning. Look up for a second. This is where help comes from.", "Your help isn't coming from the boss, the bank, or the news. It's coming from him.", "Lord, my help comes from you. Keep my eyes on you today. In Jesus' name, amen."),
 ('Psalms 23:1', "Good morning. Start the day with this one.", "A sheep doesn't plan the route. It follows the shepherd.", "Lord, be my shepherd today. I'll follow where you lead. In Jesus' name, amen."),
 ('Zephaniah 3:17', "Good morning. You might need to hear this one today.", "God rejoices over you with singing. Think about that on the drive in.", "Lord, thank you for being with me and rejoicing over me. Quiet my heart today. In Jesus' name, amen."),
 ('Psalms 30:5', "Good morning. If last night was a long night, hear this.", "The night doesn't get the last word. Morning does.", "Lord, thank you for bringing joy in the morning. I'm trusting you with today. In Jesus' name, amen."),
 ('Psalms 19:14', "Good morning. Pray this one before you say anything to anybody.", "Your words today will either build somebody up or tear them down. Let him pick them.", "Lord, let my words and my thoughts please you today. In Jesus' name, amen."),
 ('2 Corinthians 5:17', "Good morning. Yesterday is behind you. Hear this.", "In Christ, you're not who you used to be. Walk like it today.", "Lord, thank you for making me new. Help me live like it today. In Jesus' name, amen."),
 ('Colossians 3:23', "Good morning. Heading to work? Take this with you.", "Whatever's on your schedule today, do it like he's the one you're working for. Because he is.", "Lord, let my work today be done for you. Give me strength to do it right. In Jesus' name, amen."),
 ('Psalms 27:1', "Good morning. Afraid of something today? Read this first.", "When he's your light, the dark parts of the day don't get to run you.", "Lord, you are my light and my strength. I won't be afraid today. In Jesus' name, amen."),
 ('Nehemiah 8:10', "Good morning. Feeling weak already? This is for you.", "Your strength today doesn't come from coffee. It comes from his joy.", "Lord, let your joy be my strength today. In Jesus' name, amen."),
 ('Psalms 16:8', "Good morning. Keep this one in front of you all day.", "If he's at your right hand, you're not walking into anything alone.", "Lord, I'm setting you before me today. Keep me steady. In Jesus' name, amen."),
 ('Isaiah 26:3', "Good morning. Mind racing already? Hear this.", "Peace isn't the absence of problems. It's keeping your mind on him while you've got them.", "Lord, keep my mind on you today, and keep me in your peace. In Jesus' name, amen."),
 ('Psalms 32:8', "Good morning. Got a decision to make today? Hear this.", "He doesn't just point. He watches you the whole way.", "Lord, teach me and guide me today. I'm listening. In Jesus' name, amen."),
 ('Psalms 92:1-2', "Good morning. Start with thank you. Here's why.", "Mercy in the morning, faithfulness at night. He covers both ends of the day.", "Lord, it's good to thank you. Thank you for your mercy this morning. In Jesus' name, amen."),
 ('Mark 1:35', "Good morning. Even Jesus started his day like this.", "If he needed time alone with the Father before the crowds showed up, so do we.", "Lord, meet me here this morning before the day gets loud. In Jesus' name, amen."),
 ('Jeremiah 29:11', "Good morning. If your plans fell apart, hear this.", "God wasn't surprised by any of it. He's still got an expected end in mind for you.", "Lord, thank you for your thoughts of peace toward me. I trust your plan today. In Jesus' name, amen."),
 ('Romans 15:13', "Good morning. Running low on hope? Paul prayed this over people just like you.", "The joy and peace come in believing, not from how the week's been going.", "Lord, fill me with joy and peace today, and let me abound in hope. In Jesus' name, amen."),
]
NIGHT = [
 ('Psalms 3:5', "Before you close your eyes tonight, hear this.", "David slept with enemies outside, and woke up because God held him through the night.", "Lord, I lay me down tonight. Sustain me till morning. In Jesus' name, amen."),
 ('Psalms 4:4', "Lying awake tonight with a lot on your mind? Hear this.", "Talk to him about it on your bed, then let it be still.", "Lord, I'm handing you what's on my heart tonight. Make me still. In Jesus' name, amen."),
 ('Psalms 16:7', "Before you go to sleep, hear this.", "Even while you sleep, he's still working on you.", "Lord, counsel me tonight, even while I rest. In Jesus' name, amen."),
 ('Psalms 23:1-2', "Wind down with this one tonight.", "He makes you lie down. Sometimes rest is an order, not an option.", "Lord, lead me beside still waters tonight. Give me rest. In Jesus' name, amen."),
 ('Psalms 31:24', "Tired and discouraged tonight? This is for you.", "Courage doesn't always look loud. Sometimes it's just hoping one more night.", "Lord, strengthen my heart tonight. My hope is in you. In Jesus' name, amen."),
 ('Psalms 34:4', "Afraid of something tonight? Read this before bed.", "David asked, God heard, and the fear had to leave.", "Lord, I'm seeking you tonight. Deliver me from my fears. In Jesus' name, amen."),
 ('Psalms 37:7', "Before you lay it all down tonight, hear this.", "You don't have to fix it tonight. Rest, and wait on him.", "Lord, I'm resting in you tonight. I'll wait on you. In Jesus' name, amen."),
 ('Psalms 42:8', "End the day with this one.", "Mercy in the daytime, a song in the night. He covers you both ways.", "Lord, thank you for your song in the night. Keep me tonight. In Jesus' name, amen."),
 ('Psalms 55:22', "Carrying something heavy to bed tonight? Put it down.", "Cast it, don't carry it. He said he'd hold you up.", "Lord, I'm casting this burden on you tonight. Sustain me. In Jesus' name, amen."),
 ('Psalms 56:3', "Can't shake the fear tonight? Say this one with David.", "He didn't say if I'm afraid. He said what time. Fear comes. Trust answers it.", "Lord, when I'm afraid, I'll trust in you. Tonight too. In Jesus' name, amen."),
 ('Psalms 57:1', "Before you sleep, hear this.", "Hide under his wings until whatever's going on passes by.", "Lord, cover me tonight under the shadow of your wings. In Jesus' name, amen."),
 ('Psalms 61:2', "Overwhelmed tonight? This is for you.", "When your heart is overwhelmed, ask him to lead you somewhere higher than the problem.", "Lord, lead me to the rock that is higher than I. In Jesus' name, amen."),
 ('Psalms 62:1', "Wind down with this one tonight.", "Waiting isn't wasted time. It's where he does his work.", "Lord, my soul waits on you tonight. In Jesus' name, amen."),
 ('Psalms 63:6', "Lying awake tonight? Use the time this way.", "If you can't sleep, think on him instead of the problem.", "Lord, I'll remember you on my bed tonight. Give me rest. In Jesus' name, amen."),
 ('Psalms 73:26', "Worn out tonight? Hear this before bed.", "When your body and your heart both give out, he's still holding.", "Lord, be the strength of my heart tonight. In Jesus' name, amen."),
 ('Psalms 91:1', "Read this one over your house tonight.", "The secret place isn't a building. It's staying close to him.", "Lord, let me abide under your shadow tonight. Cover my house. In Jesus' name, amen."),
 ('Psalms 91:4-5', "Before you sleep, read these over your family.", "His truth is your shield. The terror by night doesn't get the final say.", "Lord, cover me with your feathers tonight. I won't be afraid. In Jesus' name, amen."),
 ('Psalms 94:19', "Too many thoughts tonight? This is for you.", "When the thoughts pile up, let his comfort be the last one.", "Lord, let your comforts delight my soul tonight. In Jesus' name, amen."),
 ('Psalms 103:2-3', "End the day thankful. Here's why.", "Count what he did today before you count what went wrong.", "Lord, I won't forget your benefits. Thank you for today. In Jesus' name, amen."),
 ('Psalms 107:29', "Storm going on in your life tonight? Hear this.", "He can calm the storm, or calm you in the middle of it.", "Lord, make the storm a calm tonight. Give me peace. In Jesus' name, amen."),
 ('Psalms 116:7', "Before you close your eyes, say this to yourself.", "Tell your own soul to rest. He's been good to you.", "Lord, I'm returning to my rest tonight. You've dealt bountifully with me. In Jesus' name, amen."),
 ('Psalms 121:3-4', "Before you sleep tonight, hear this.", "You can sleep, because he doesn't.", "Lord, you never slumber. Keep me tonight while I rest. In Jesus' name, amen."),
 ('Psalms 121:8', "End the day with this promise.", "Going out this morning, coming in tonight. He covered both.", "Lord, thank you for keeping me today. Keep me tonight. In Jesus' name, amen."),
 ('Psalms 127:2', "Worked all day? This one's for you.", "Staying up late worrying won't add a thing. He gives his beloved sleep.", "Lord, I'm putting the work down. Give me the sleep you promised. In Jesus' name, amen."),
 ('Psalms 131:2', "Quiet your heart with this one tonight.", "Like a child resting on his mother. That kind of quiet.", "Lord, quiet my soul tonight like a weaned child. In Jesus' name, amen."),
 ('Psalms 139:11-12', "Afraid of the dark tonight? Hear this.", "The dark doesn't hide anything from him, and it doesn't hide you either.", "Lord, the darkness is light to you. Watch over me tonight. In Jesus' name, amen."),
 ('Psalms 141:2', "Make your bedtime prayer this one.", "Your evening prayer goes up to him like incense.", "Lord, let my prayer tonight come up before you. In Jesus' name, amen."),
 ('Psalms 147:3', "Hurting tonight? This is for you.", "He doesn't just see the broken heart. He binds it up.", "Lord, heal my heart tonight and bind up the wounds. In Jesus' name, amen."),
 ('Psalms 149:5', "End the day on a good note.", "You can go to bed singing, not worrying.", "Lord, I'm thankful tonight. Let me rest with a song in my heart. In Jesus' name, amen."),
]
PSALM_PART = [(31, 'BFwsZGyPw70', '1–31'), (56, 'enLUGzduXXE', '32–56'), (78, 'aXGIzNACPO8', '57–78'), (104, '9omyQM3ULPU', '79–104'), (124, 'JJQjAr3xG0g', '105–124'), (150, '2V6mjKBs0yo', '125–150')]
MC = ['m-birds0.mp4','m-lake0.mp4','m-water1.mp4','m-forest1.mp4','m-eagle0.mp4','m-lake2.mp4','m-birds1.mp4','m-lake1.mp4','m-forest0.mp4','m-water0.mp4','m-eagle1.mp4','m-birds2.mp4']
NC = ['n-moon0.mp4','n-moon2.mp4','n-stars2.mp4','n-candle1.mp4','n-moon1.mp4','n-lake0.mp4','n-ocean1.mp4','n-stars0.mp4','n-candle0.mp4','n-ocean0.mp4','n-stars1.mp4']
def split_verse(t):
    # one card if short, else two cards split at the nearest ':' or ';' or ',' to the middle
    if len(t) <= 95: return [t]
    cuts = [m.end() for m in re.finditer(r'[:;,] ', t)]
    if not cuts: return [t]
    c = min(cuts, key=lambda x: abs(x - len(t) / 2)); return [t[:c].strip(), t[c:].strip()]
start = datetime.date(2026, 11, 19); os.makedirs('eps', exist_ok=True); man = []
for i, (ref, opener, line, prayer) in enumerate(MORNING):
    d = start + datetime.timedelta(days=i); t = verse(ref); parts = split_verse(t); clips = itertools.cycle(MC[i % 12:] + MC[:i % 12])
    L = [{'say': opener, 'big': 'Good morning.', 'small': opener.replace('Good morning. ', ''), 'clip': next(clips), 'ss': 0.5}]
    for j, p in enumerate(parts):
        last = j == len(parts) - 1
        L.append({'say': p + (' ' + spoken(ref) + '.' if last else ''), 'big': p, 'small': shown(ref) if last else '', 'clip': next(clips), 'ss': 0.5})
    L += [{'say': line, 'big': line, 'small': '', 'clip': next(clips), 'ss': 0.5},
          {'say': prayer, 'big': "In Jesus' name, amen.", 'small': '', 'clip': next(clips), 'ss': 0.5},
          {'say': "Have a blessed day. Type amen, and send this to somebody starting their day.", 'big': 'Have a blessed day.', 'small': 'Type amen, and send this to somebody starting their day', 'clip': next(clips), 'ss': 0.5}]
    fn = f'eps/m-{d}.json'; json.dump({'brand': 'BLESSED MORNING', 'ref': ref, 'kjv': t, 'lines': L}, open(fn, 'w'), indent=1, ensure_ascii=False); man.append(('m', str(d), ref, t, line))
for i, (ref, opener, line, prayer) in enumerate(NIGHT):
    d = start + datetime.timedelta(days=i); t = verse(ref); parts = split_verse(t); clips = itertools.cycle(NC[i % 11:] + NC[:i % 11])
    ps = int(re.match(r'Psalms (\d+)', ref).group(1)); vid, rng = next((v, r) for top, v, r in PSALM_PART if ps <= top)
    L = [{'say': opener, 'big': opener.split('?')[0].split('.')[0], 'small': '', 'clip': next(clips), 'ss': 0.5}]
    for j, p in enumerate(parts):
        last = j == len(parts) - 1
        L.append({'say': p + (' ' + spoken(ref) + '.' if last else ''), 'big': p, 'small': shown(ref) if last else '', 'clip': next(clips), 'ss': 0.5})
    L += [{'say': line, 'big': line, 'small': '', 'clip': next(clips), 'ss': 0.5},
          {'say': prayer, 'big': "In Jesus' name, amen.", 'small': '', 'clip': next(clips), 'ss': 0.5},
          {'say': f"Want the Word playing while you sleep? Psalms {rng.replace('–',' through ')}, read slowly, is on our channel. The link is in the description.", 'big': 'Fall asleep to the Word', 'small': f'Psalms {rng}, read slowly. Link in the description.', 'clip': next(clips), 'ss': 0.5}]
    fn = f'eps/n-{d}.json'; json.dump({'brand': 'REST IN THE WORD', 'speed': 0.9, 'ref': ref, 'kjv': t, 'audio_bible': f'https://www.youtube.com/watch?v={vid}', 'audio_range': rng, 'lines': L}, open(fn, 'w'), indent=1, ensure_ascii=False); man.append(('n', str(d), ref, t, line))
json.dump(man, open('eps/manifest.json', 'w'), indent=1, ensure_ascii=False); print(len(man))
