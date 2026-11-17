import json,sys,os,urllib.request,shutil,subprocess
N=json.load(open('nights.json')); cache={}
def kjv(b,c,vs):
    if b not in cache: cache[b]=json.load(urllib.request.urlopen(f"https://raw.githubusercontent.com/aruljohn/Bible-kjv/master/{b}.json"))
    ch=next(x for x in cache[b]["chapters"] if int(x["chapter"])==c)
    return " ".join(next(x["text"] for x in ch["verses"] if int(x["verse"])==v).strip() for v in vs).replace('’',"'")
for n in N:
    d=n['id']; os.makedirs(d,exist_ok=True)
    L=[{"say":n['hook'],"big":n['hookBig'],"small":n['hookSmall']}]
    n['texts']=[]
    for b,c,vs,say,ref in n['v']:
        t=kjv(b,c,vs); n['texts'].append((t,ref)); L.append({"say":t+" "+say,"big":t,"small":ref})
    L.append({"say":n['prayer'],"big":n['prayer'].split('.')[0].replace('Lord, ','').strip()[:0] or "In Jesus' name, amen","small":""})
    L.append({"say":f"The full reading of the Psalms for sleep is on the Blessed Prayers channel. Type amen, and leave your prayer request below.","big":"Full Psalms sleep reading","small":"on the Blessed Prayers channel · Type amen"})
    json.dump(L,open(f'{d}/lines.json','w'),indent=1)
    for f in ('tts.py','build.py'): shutil.copy(f'/home/claude/sleep-short/{f}',d)
    subprocess.run(['sed','-i','s/sleep-scriptures.mp4/out.mp4/',f'{d}/build.py'])
json.dump(N,open('nights_full.json','w'),indent=1)
