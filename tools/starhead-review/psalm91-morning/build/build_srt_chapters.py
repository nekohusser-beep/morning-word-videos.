# Builds pack/captions.srt and prints chapter start times from /home/claude/ps91m/tl.json (same clock as asm_tg.py; video time = timeline time - 0.3)
import json,math,sys
tl=json.load(open('/home/claude/ps91m/tl.json')); SECT=json.load(open('/home/claude/ps91m/sections.json'))
K=0.9;START=0.0
def ts(x):
    x=max(0,x);ms=int(round(x*1000));h,r=divmod(ms,3600000);m,r=divmod(r,60000);s,ms=divmod(r,1000);return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
t=START;first=True;items=[];starts={}
for it in tl:
    if it['k']=='s':
        if not first:t+=0.7
        first=False
    elif it['k']=='n':
        starts.setdefault(it['p'],t-START);items.append((t-START,t-START+it['d'],it['t']));t+=it['d']+K*(0.62+(1.25 if it.get('para') else 0))
    else:
        t+=0.45;starts.setdefault(it['p'],t-START);items.append((t-START,t-START+it['d'],it['t']));t+=it['d']+K*2.4
def balance(words,n):
    tot=sum(len(w)+1 for w in words);tgt=tot/n;g=[];cur=[]
    for w in words:
        done=sum(len(x)+1 for gg in g for x in gg)
        if cur and len(g)<n-1 and done+sum(len(x)+1 for x in cur)+len(w)/2>tgt*(len(g)+1):
            g.append(cur);cur=[]
        cur.append(w)
    g.append(cur);return g
def two(text):
    if len(text)<=42:return text
    w=text.split();best=None
    for i in range(1,len(w)):
        a=" ".join(w[:i]);b=" ".join(w[i:])
        if max(len(a),len(b))<=42:
            s=abs(len(a)-len(b))
            if best is None or s<best[0]:best=(s,a+"\n"+b)
    return best[1] if best else text
out=[];n=0
for a,b,tx in items:
    words=tx.split();k=max(1,math.ceil(len(tx)/80))
    while True:
        groups=balance(words,k)
        if all(max(len(l) for l in two(" ".join(g)).split("\n"))<=42 and two(" ".join(g)).count("\n")<=1 for g in groups):break
        k+=1
    tot=sum(len(" ".join(g)) for g in groups);pos=a
    for g in groups:
        txt=" ".join(g);d=(b-a)*len(txt)/tot;n+=1
        out.append(f"{n}\n{ts(pos)} --> {ts(pos+d)}\n{two(txt)}\n");pos+=d
open('pack/captions.srt','w').write("\n".join(out)+"\n")
print(n,"cues, last ends",round(items[-1][1],1))
for kk,v in sorted(SECT.items(),key=lambda x:int(x[0])):
    s=int(starts[int(kk)]);print(f"{s//60}:{s%60:02d} {v}")
