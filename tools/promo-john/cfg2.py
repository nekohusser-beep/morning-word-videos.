import json,sys,shutil,os
sys.path.insert(0,'/tmp/w'); from mk import make
R='/home/claude/morning-word-videos./tools'
tro=json.load(open('/tmp/trn/transcript-39078256894.json'))
words={}
for k,v in tro.items(): words['o'+k.split('/')[-1][:-4]]=v
import glob
for f in ['/tmp/clips3/transcript-39110349029.json']+glob.glob('/tmp/clips5/transcript-*.json'):
    for k,v in json.load(open(f)).items(): words[k.split('/')[-1][:-4]]=v
l=json.load(open(R+'/scripts-pending/psalm-91.json'))
l['6']="That's the 91st Psalm, verses 1 and 2."
l['14']="Father, be our refuge today, in the traffic, at the job,"
m={"1":"o12","2":"o17","3":"o10","4":"o02","5":"o08","6":"f01","7":"o13","8":"o15","9":"o18","10":"o01","11":"o14","12":"o06","13":"o05","14":"o16","15":"o03","16":"o11","17":"d00","18":"o04","19":"o09"}
vis={str(i):("cam",1.0) for i in range(1,20)}
vis["7"]=("broll",["br_cabin"]); vis["8"]=("broll",["br_truck"]); vis["9"]=("broll",["br_gate"]); vis["10"]=("broll",["br_fortress"])
prev=None
for i in range(1,20):
    k=str(i)
    if vis[k][0]=='cam':
        sc=1.0 if prev in (None,1.08) else 1.08
        vis[k]=("cam",sc); prev=sc
    else: prev=None
gap={"1":0.85,"5":1.0,"6":0.75,"13":0.8,"17":1.0,"19":0.0}
make('psalm91','/tmp/w/ps91',m,gap,vis,{"8":1.50,"13":0.24,"17":2.70},{},'A prayer before you start your day','Morning_Word_Psalm_91',l,19,cardtitle='Morning Word')
json.dump({c:words[c] for c in m.values()},open('/tmp/w/ps91/tr_all.json','w'))
os.makedirs('/tmp/w/ps91/broll',exist_ok=True); os.makedirs('/tmp/w/ps91/clips',exist_ok=True)
for n,f in (('br_cabin','b10'),('br_truck','b04'),('br_gate','b03'),('br_fortress','b09')): shutil.copy(f'/tmp/clips2/{f}.mp4',f'/tmp/w/ps91/broll/{n}.mp4')
for c in m.values():
    src={"d":"/tmp/clips3","f":"/tmp/clips5","e":"/tmp/clips4",'o':'/tmp/clips'}[c[0]]
    shutil.copy(f'{src}/{c[1:] if c[0]=="o" else c}.mp4',f'/tmp/w/ps91/clips/{c}.mp4')
print('ok')
