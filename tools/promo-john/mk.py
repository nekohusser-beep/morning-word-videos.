import re,json,sys,shutil,os,glob
T=open('/home/claude/morning-word-videos./tools/sleep-promo-psalms/build.py').read()
def make(name, W, clipmap, gap, vis, start_ov, end_ov, cardsub, outname, lines, last, cardtitle=None):
    s=T
    a=s.index('CLIPMAP ='); b=s.index('OPEN = 5.7333')
    mid=f'''CLIPMAP = {json.dumps(clipmap)}
GAP = {json.dumps(gap)}
START_OV = {json.dumps(start_ov)}
END_OV = {json.dumps(end_ov)}
CLIP = {{}}
for k, c in CLIPMAP.items():
    s_, e_ = _bounds(c)
    if k in START_OV: s_ = START_OV[k]
    if k in END_OV: e_ = END_OV[k]
    CLIP[k] = (c, s_, e_, 0, GAP.get(k, 0.65))
VIS = {json.dumps(vis)}
ORDER = [str(i) for i in range(1, {last}+1)]
PRE = {{}}
'''
    s=s[:a]+mid+s[b:]
    s=s.replace('T["16"]','T["%d"]'%last).replace('D["16"]','D["%d"]'%last)
    s=s.replace("The Book of Psalms  KJV",cardsub)
    if cardtitle: s=s.replace("text='Sleep with the Word':fontsize=58","text='%s':fontsize=64"%cardtitle)
    s=s.replace("Sleep_Promo_Psalms",outname).replace("sleep-promo-psalms.srt",outname+".srt")
    s=s.replace('"/usr/share','"/usr/share')
    # bounds: prefer start from the energy map unless overridden
    s=s.replace('REPO = "/home/claude/morning-word-videos."','REPO = "/home/claude/morning-word-videos."')
    os.makedirs(W,exist_ok=True)
    open(f'{W}/build.py','w').write(s)
    json.dump(lines,open(f'{W}/lines.json','w'),indent=0)
