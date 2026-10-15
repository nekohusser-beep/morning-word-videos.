import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from engine import *

CREAM='#F3EEE3'; GOLD='#C9A54A'; INK='#232323'; RUST='#A8522A'; OLIVE='#6E6A3A'
FOREST='#2F4A36'; CRIMSON='#8E2430'; NAVY='#1F2C44'; SAGE='#7D8B6A'; MUSTARD='#C08A2B'

def render(els, path):
    im, d = new()
    y = 100; cx = W // 2
    for e in els:
        k = e['t']
        if k == 'text':
            maxw = W * e.get('w', 0.9)
            f, size = fit_size(d, e['s'], e['f'], maxw, e.get('size', 900), e.get('tr', 0))
            y = draw_text(d, cx, y, e['s'], f, e['c'], size * e.get('tr', 0))
            y += e.get('gap', 60)
        elif k == 'cross':
            h = e['h']; cross(d, cx, y + h / 2, h, e['c']); y += h + e.get('gap', 60)
        elif k == 'star':
            r = e['r']; star(d, cx, y + r, r, e['c']); y += 2 * r + e.get('gap', 60)
        elif k == 'rule':
            rule(d, cx, y, W * e.get('w', 0.5), e['c'], e.get('th', 16)); y += e.get('gap', 70)
        elif k == 'ruleicon':  # —— icon ——
            w = W * e.get('w', 0.6); th = e.get('th', 14); ic = e.get('icon', 'cross'); s = e.get('s', 200)
            rule(d, cx, y + s / 2, w, e['c'], th, gap=s * 0.9, dot=True)
            if ic == 'cross': cross(d, cx, y + s / 2, s, e['c2'] if 'c2' in e else e['c'])
            elif ic == 'star': star(d, cx, y + s / 2, s / 2, e.get('c2', e['c']))
            elif ic == 'snow': snowflake(d, cx, y + s / 2, s / 2, e.get('c2', e['c']))
            y += s + e.get('gap', 70)
        elif k == 'wheat':
            h = e['h']
            wheat(d, cx - 120, y + h, h, e['c'], lean=-0.35); wheat(d, cx, y + h, h * 1.05, e['c'], 0); wheat(d, cx + 120, y + h, h, e['c'], lean=0.35)
            y += h + e.get('gap', 80)
        elif k == 'laurel':
            h = e['h']
            branch(d, cx - 60, y + h, h, -2.2, e['c']); branch(d, cx + 60, y + h, h, -0.94, e['c'])
            y += h + e.get('gap', 60)
        elif k == 'snow3':
            r = e['r']
            for dx, rr in ((-r * 3, r * 0.7), (0, r), (r * 3, r * 0.7)):
                snowflake(d, cx + dx, y + r, rr, e['c'])
            y += 2 * r + e.get('gap', 70)
        elif k == 'space':
            y += e['h']
    return finish(im, path)

T = lambda s, f, c, **k: dict(t='text', s=s, f=f, c=c, **k)

D = {}
# ---------- MEN TEES ----------
D['M1'] = ('dark', [
    dict(t='cross', h=520, c=GOLD, gap=90),
    T('I AM THE WAY', 'bebas', CREAM, w=0.92, gap=10),
    T('THE TRUTH', 'bebas', CREAM, w=0.70, gap=10),
    T('AND THE LIFE', 'bebas', CREAM, w=0.92, gap=90),
    dict(t='rule', w=0.32, c=GOLD, th=18, gap=70),
    T('JOHN 14:6  ·  KJV', 'mont', GOLD, w=0.42, tr=0.12)])
D['M2'] = ('dark', [
    T('BE STRONG', 'anton', CREAM, w=0.9, gap=20),
    T('AND OF A GOOD', 'oswald', GOLD, w=0.62, tr=0.08, gap=40),
    T('COURAGE', 'anton', CREAM, w=0.9, gap=80),
    T('FOR THE LORD THY GOD IS WITH THEE', 'mont', CREAM, w=0.78, tr=0.05, gap=30),
    T('WHITHERSOEVER THOU GOEST', 'mont', CREAM, w=0.62, tr=0.05, gap=80),
    T('JOSHUA 1:9', 'oswald', GOLD, w=0.28, tr=0.15)])
D['M3'] = ('light', [
    T('IRON', 'archivo', INK, w=0.75, gap=30),
    T('SHARPENETH', 'archivo', INK, w=0.92, gap=30),
    T('IRON', 'archivo', INK, w=0.75, gap=80),
    dict(t='ruleicon', w=0.7, c=RUST, icon='cross', s=230, gap=70),
    T('SO A MAN SHARPENETH THE COUNTENANCE OF HIS FRIEND', 'mont', INK, w=0.86, tr=0.04, gap=40),
    T('PROVERBS 27:17', 'oswald', RUST, w=0.34, tr=0.15)])
D['M4'] = ('dark', [
    T('NO WEAPON', 'anton', CREAM, w=0.9, gap=20),
    T('THAT IS FORMED AGAINST THEE', 'oswald', GOLD, w=0.86, tr=0.06, gap=30),
    T('SHALL PROSPER', 'anton', CREAM, w=0.9, gap=90),
    dict(t='rule', w=0.3, c=GOLD, th=18, gap=70),
    T('ISAIAH 54:17', 'oswald', CREAM, w=0.3, tr=0.15)])
D['M5'] = ('light', [
    T('FOR I AM', 'oswald', NAVY, w=0.4, tr=0.12, gap=40),
    T('NOT ASHAMED', 'archivo', NAVY, w=0.92, gap=40),
    T('OF THE GOSPEL OF CHRIST', 'oswald', NAVY, w=0.86, tr=0.06, gap=90),
    dict(t='ruleicon', w=0.6, c=CRIMSON, icon='cross', s=220, gap=70),
    T('ROMANS 1:16', 'oswald', CRIMSON, w=0.28, tr=0.15)])
# ---------- WOMEN TEES ----------
D['W1'] = ('light', [
    T('It is well', 'vibes', INK, w=0.85, gap=20),
    T('WITH MY SOUL', 'cinzel', INK, w=0.82, tr=0.1, gap=80),
    dict(t='laurel', h=520, c=SAGE, gap=40)])
D['W2'] = ('light', [
    T('For I know the thoughts', 'vibes', INK, w=0.88, gap=30),
    T('THAT I THINK TOWARD YOU, SAITH THE LORD,', 'cinzel', INK, w=0.88, tr=0.05, gap=40),
    T('THOUGHTS OF PEACE, AND NOT OF EVIL,', 'cormorant', INK, w=0.8, tr=0.05, gap=20),
    T('TO GIVE YOU AN EXPECTED END', 'cormorant', INK, w=0.66, tr=0.05, gap=80),
    dict(t='ruleicon', w=0.5, c=MUSTARD, icon='star', s=180, gap=60),
    T('JEREMIAH 29:11', 'cinzel', MUSTARD, w=0.32, tr=0.12)])
D['W3'] = ('light', [
    T('PRAY', 'abril', INK, w=0.62, gap=10),
    T('without ceasing', 'vibes', RUST, w=0.82, gap=80),
    T('1 THESSALONIANS 5:17', 'mont', INK, w=0.44, tr=0.14)])
D['W4'] = ('dark', [
    T('Strength', 'vibes', GOLD, w=0.8, gap=0),
    T('AND HONOUR', 'cinzel', CREAM, w=0.62, tr=0.12, gap=50),
    T('ARE HER CLOTHING', 'cinzel', CREAM, w=0.72, tr=0.08, gap=50),
    T('AND SHE SHALL REJOICE IN TIME TO COME', 'cormorant', CREAM, w=0.78, tr=0.05, gap=70),
    T('PROVERBS 31:25', 'cinzel', GOLD, w=0.32, tr=0.12)])
D['W5'] = ('light', [
    T('THE LORD IS', 'cinzel', FOREST, w=0.62, tr=0.12, gap=20),
    T('my Shepherd', 'vibes', FOREST, w=0.88, gap=30),
    T('I SHALL NOT WANT', 'cinzel', FOREST, w=0.66, tr=0.1, gap=70),
    dict(t='laurel', h=420, c=SAGE, gap=50),
    T('PSALM 23:1', 'mont', FOREST, w=0.24, tr=0.15)])
# ---------- MEN SWEATSHIRTS ----------
D['MS1'] = ('dark', [
    T('KING OF KINGS', 'cinzel', CREAM, w=0.9, tr=0.04, gap=40),
    dict(t='ruleicon', w=0.72, c=GOLD, icon='cross', s=280, gap=40),
    T('LORD OF LORDS', 'cinzel', CREAM, w=0.9, tr=0.04, gap=80),
    T('REVELATION 19:16', 'mont', GOLD, w=0.36, tr=0.15)])
D['MS2'] = ('dark', [
    T('O MAN OF GOD', 'anton', CREAM, w=0.9, gap=50),
    T('FOLLOW AFTER RIGHTEOUSNESS, GODLINESS,', 'mont', CREAM, w=0.84, tr=0.04, gap=25),
    T('FAITH, LOVE, PATIENCE, MEEKNESS', 'mont', CREAM, w=0.72, tr=0.04, gap=70),
    T('1 TIMOTHY 6:11', 'oswald', GOLD, w=0.3, tr=0.15)])
D['MS3'] = ('dark', [
    T('PUT ON', 'oswald', GOLD, w=0.36, tr=0.15, gap=30),
    T('THE WHOLE', 'anton', CREAM, w=0.72, gap=10),
    T('ARMOUR', 'anton', CREAM, w=0.9, gap=10),
    T('OF GOD', 'anton', CREAM, w=0.56, gap=70),
    T('EPHESIANS 6:11', 'oswald', GOLD, w=0.32, tr=0.15)])
D['MS4'] = ('light', [
    T('WATCH YE', 'archivo', INK, w=0.7, gap=30),
    T('STAND FAST IN THE FAITH', 'oswaldb', INK, w=0.9, tr=0.04, gap=30),
    T('QUIT YOU LIKE MEN', 'oswaldb', INK, w=0.74, tr=0.04, gap=30),
    T('BE STRONG', 'archivo', RUST, w=0.7, gap=80),
    T('1 CORINTHIANS 16:13', 'mont', INK, w=0.4, tr=0.15)])
D['MS5'] = ('dark', [  # Christmas
    dict(t='star', r=260, c=GOLD, gap=70),
    T('FOR UNTO YOU IS BORN THIS DAY', 'cinzel', CREAM, w=0.88, tr=0.05, gap=25),
    T('IN THE CITY OF DAVID', 'cinzel', CREAM, w=0.66, tr=0.06, gap=30),
    T('A SAVIOUR', 'abril', GOLD, w=0.8, gap=30),
    T('WHICH IS CHRIST THE LORD', 'cinzel', CREAM, w=0.84, tr=0.06, gap=70),
    T('LUKE 2:11', 'mont', GOLD, w=0.22, tr=0.15)])
# ---------- WOMEN SWEATSHIRTS ----------
D['WS1'] = ('light', [  # fall
    dict(t='wheat', h=620, c=MUSTARD, gap=70),
    T('O give thanks', 'vibes', RUST, w=0.86, gap=20),
    T('UNTO THE LORD', 'cinzel', INK, w=0.7, tr=0.1, gap=20),
    T('FOR HE IS GOOD', 'cinzel', INK, w=0.72, tr=0.1, gap=60),
    T('PSALM 107:1', 'mont', RUST, w=0.26, tr=0.15)])
D['WS2'] = ('light', [  # fall
    T('SEEDTIME', 'abril', RUST, w=0.82, gap=10),
    T('& harvest', 'vibes', OLIVE, w=0.72, gap=50),
    dict(t='ruleicon', w=0.62, c=MUSTARD, icon='cross', s=200, gap=50),
    T('WHILE THE EARTH REMAINETH,', 'cormorant', INK, w=0.6, tr=0.05, gap=20),
    T('SEEDTIME AND HARVEST . . . SHALL NOT CEASE', 'cormorant', INK, w=0.86, tr=0.04, gap=60),
    T('GENESIS 8:22', 'mont', RUST, w=0.28, tr=0.15)])
D['WS3'] = ('dark', [  # fall/thanksgiving
    T('In every thing', 'vibes', GOLD, w=0.86, gap=10),
    T('GIVE THANKS', 'cinzel', CREAM, w=0.84, tr=0.08, gap=60),
    dict(t='laurel', h=420, c=GOLD, gap=50),
    T('1 THESSALONIANS 5:18', 'mont', CREAM, w=0.42, tr=0.15)])
D['WS4'] = ('light', [  # Christmas
    dict(t='star', r=230, c=MUSTARD, gap=60),
    T('O come', 'vibes', CRIMSON, w=0.66, gap=10),
    T('LET US ADORE HIM', 'cinzel', FOREST, w=0.84, tr=0.08, gap=60),
    T('CHRIST THE LORD', 'mont', CRIMSON, w=0.42, tr=0.18)])
D['WS5'] = ('dark', [  # New Year
    T('Behold,', 'vibes', GOLD, w=0.56, gap=10),
    T('I MAKE', 'cinzel', CREAM, w=0.5, tr=0.12, gap=20),
    T('ALL THINGS NEW', 'cinzel', CREAM, w=0.88, tr=0.06, gap=70),
    dict(t='ruleicon', w=0.5, c=GOLD, icon='star', s=170, gap=60),
    T('REVELATION 21:5', 'mont', GOLD, w=0.34, tr=0.15)])
# ---------- MEN HOODIES ----------
D['MH1'] = ('dark', [
    T('THE BATTLE', 'anton', CREAM, w=0.9, gap=20),
    T("IS THE LORD'S", 'anton', GOLD, w=0.9, gap=80),
    T('1 SAMUEL 17:47', 'oswald', CREAM, w=0.32, tr=0.15)])
D['MH2'] = ('dark', [
    T('I AM', 'cinzel', CREAM, w=0.5, tr=0.1, gap=20),
    T('THAT', 'cinzel', GOLD, w=0.4, tr=0.2, gap=20),
    T('I AM', 'cinzel', CREAM, w=0.5, tr=0.1, gap=80),
    dict(t='rule', w=0.3, c=GOLD, th=16, gap=60),
    T('EXODUS 3:14', 'mont', GOLD, w=0.26, tr=0.15)])
D['MH3'] = ('light', [
    T('MORE THAN', 'oswaldb', INK, w=0.6, tr=0.08, gap=20),
    T('CONQUERORS', 'archivo', INK, w=0.92, gap=40),
    T('THROUGH HIM THAT LOVED US', 'oswald', RUST, w=0.7, tr=0.08, gap=70),
    T('ROMANS 8:37', 'mont', INK, w=0.26, tr=0.15)])
D['MH4'] = ('dark', [
    T('THE LION', 'abril', GOLD, w=0.86, gap=30),
    T('OF THE TRIBE OF JUDA', 'cinzel', CREAM, w=0.88, tr=0.06, gap=30),
    T('HATH PREVAILED', 'cinzel', CREAM, w=0.6, tr=0.1, gap=70),
    dict(t='ruleicon', w=0.5, c=GOLD, icon='cross', s=200, gap=60),
    T('REVELATION 5:5', 'mont', GOLD, w=0.32, tr=0.15)])
D['MH5'] = ('dark', [  # Christmas
    T('WONDERFUL', 'cinzel', CREAM, w=0.8, tr=0.08, gap=30),
    T('COUNSELLOR', 'cinzel', CREAM, w=0.8, tr=0.08, gap=50),
    dict(t='ruleicon', w=0.66, c=GOLD, icon='star', s=200, gap=50),
    T('THE MIGHTY GOD · THE EVERLASTING FATHER', 'mont', GOLD, w=0.88, tr=0.04, gap=25),
    T('THE PRINCE OF PEACE', 'mont', GOLD, w=0.46, tr=0.05, gap=60),
    T('ISAIAH 9:6', 'mont', CREAM, w=0.24, tr=0.15)])
# ---------- WOMEN HOODIES ----------
D['WH1'] = ('light', [
    T('Let your light', 'vibes', MUSTARD, w=0.86, gap=10),
    T('SO SHINE', 'cinzel', INK, w=0.62, tr=0.14, gap=40),
    T('BEFORE MEN', 'cinzel', INK, w=0.5, tr=0.14, gap=60),
    dict(t='ruleicon', w=0.5, c=MUSTARD, icon='star', s=170, gap=50),
    T('MATTHEW 5:16', 'mont', INK, w=0.28, tr=0.15)])
D['WH2'] = ('light', [
    T('Be still', 'vibes', SAGE, w=0.7, gap=10),
    T('AND KNOW', 'cinzel', INK, w=0.5, tr=0.14, gap=20),
    T('THAT I AM GOD', 'cinzel', INK, w=0.74, tr=0.1, gap=70),
    dict(t='laurel', h=380, c=SAGE, gap=40),
    T('PSALM 46:10', 'mont', INK, w=0.26, tr=0.15)])
D['WH3'] = ('dark', [
    T('We love him', 'vibes', GOLD, w=0.84, gap=20),
    T('BECAUSE HE', 'cinzel', CREAM, w=0.56, tr=0.12, gap=20),
    T('FIRST LOVED US', 'cinzel', CREAM, w=0.76, tr=0.1, gap=70),
    T('1 JOHN 4:19', 'mont', GOLD, w=0.26, tr=0.15)])
D['WH4'] = ('light', [
    T('THE JOY', 'abril', RUST, w=0.62, gap=10),
    T('of the Lord', 'vibes', INK, w=0.74, gap=10),
    T('IS YOUR STRENGTH', 'cinzel', INK, w=0.8, tr=0.08, gap=70),
    T('NEHEMIAH 8:10', 'mont', RUST, w=0.3, tr=0.15)])
D['WH5'] = ('dark', [  # Christmas
    dict(t='snow3', r=150, c=CREAM, gap=60),
    T('Joy to the world', 'vibes', GOLD, w=0.88, gap=20),
    T('THE LORD IS COME', 'cinzel', CREAM, w=0.8, tr=0.1, gap=70),
    dict(t='ruleicon', w=0.4, c=GOLD, icon='star', s=150, gap=10)])

# ---------- NEW: Half Hood Half Holy (tee + hoodie, same art) ----------
D['HH1'] = ('dark', [
    T('HALF HOOD', 'anton', CREAM, w=0.92, gap=10),
    T('HALF HOLY', 'anton', GOLD, w=0.92, gap=60)])
# ---------- NEW: Psalm 78:52-53 KJV (tee + hoodie, same art) ----------
D['PS1'] = ('dark', [
    T('GUIDED THEM IN', 'cinzel', CREAM, w=0.84, tr=0.06, gap=10),
    T('THE WILDERNESS', 'anton', GOLD, w=0.9, gap=10),
    T('LIKE A FLOCK', 'cinzel', CREAM, w=0.84, tr=0.06, gap=50),
    dict(t='rule', w=0.3, c=GOLD, th=18, gap=60),
    T('AND HE LED THEM ON SAFELY', 'mont', CREAM, w=0.74, tr=0.04, gap=40),
    T('PSALM 78:52-53', 'oswald', GOLD, w=0.4, tr=0.15)])
# ---------- NEW: Tap My Shoulder, same big-type style, our own wording ----------
D['TS1'] = ('dark', [
    T('NEED PRAYER?', 'anton', CREAM, w=0.9, gap=10),
    T('TAP MY SHOULDER', 'anton', GOLD, w=0.92, gap=10),
    T("I'LL PRAY FOR YOU", 'oswald', CREAM, w=0.7, tr=0.06, gap=40),
    T('MATTHEW 18:20', 'mont', GOLD, w=0.3, tr=0.15)])

if __name__ == '__main__':
    out = os.path.join(os.path.dirname(__file__), 'out'); os.makedirs(out, exist_ok=True)
    ids = sys.argv[1:] or list(D)
    for k in ids:
        tone, els = D[k]
        render(els, os.path.join(out, f'{k}.png')); print(k, tone)
