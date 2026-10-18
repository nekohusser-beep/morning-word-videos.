import json,sys,shutil,os
sys.path.insert(0,'/tmp/w'); from mk import make
R='/home/claude/morning-word-videos./tools'
tro=json.load(open('/tmp/trn/transcript-39078256894.json'))
trn=json.load(open('/tmp/clips2/transcript-39081263355.json'))
trb=json.load(open('/tmp/clips2/transcript-39108239063.json'))
words={}
for k,v in tro.items(): words['o'+k.split('/')[-1][:-4]]=v
for k,v in trn.items(): words[k.split('/')[-1][:-4]]=v
for k,v in trb.items(): words[k.split('/')[-1][:-4]]=v
# ---- John
jl=json.load(open(R+'/scripts-pending/john-promo.json'))
jl['5']="That's John 14:27."; jl['10']="all 21 chapters, in the King James."
jmap={"1":"o34","2":"o39","3":"o33","4":"o36","5":"o37","6":"o32","7":"o38","8":"o35","9":"c31","10":"o29","11":"o21","12":"o30","13":"o19","14":"c32","15":"o26","16":"c30","17":"o20","18":"o23","19":"o22"}
jvis={}
for i in range(1,20):
    jvis[str(i)]=("cam",1.0 if i%2 else 1.08)
jvis["6"]=("broll",["br_supper"]); jvis["7"]=("broll",["br_olive"]); jvis["8"]=("broll",["br_bed"])
jvis["9"]=("cam",1.08)
def alt(v,n):
    prev=None
    for i in range(1,n+1):
        k=str(i)
        if v[k][0]=='cam':
            sc=1.0 if prev in (None,1.08) else 1.08
            v[k]=('cam',sc); prev=sc
        else: prev=None
alt(jvis,19)
make('john','/tmp/w/john',jmap,{"4":1.0,"5":0.75,"16":1.0,"19":0.0},jvis,{"9":3.30,"16":1.86},{},'The Gospel of John  KJV','Sleep_Promo_John',jl,19)
# ---- Proverbs
pl=json.load(open(R+'/scripts-pending/proverbs-promo.json'))
pl['1']="Do you ever lie awake planning tomorrow with nothing left in you?"
pl['2']="When thou liest down, thou shalt not be afraid:"
pl['3']="yea, thou shalt lie down, and thy sleep shall be sweet."
pl['4']="That's Proverbs 3:24."; pl['8']="So we made the Book of Proverbs, all 31 chapters,"
pmap={"1":"c23","2":"c26","3":"c13","4":"c24","5":"c17","6":"c21","7":"c14","8":"c19","9":"c15","10":"c22","11":"c18","12":"c27","13":"c16","14":"b11","15":"c20","16":"c25","17":"c12"}
pvis={}
for i in range(1,18): pvis[str(i)]=("cam",1.0 if i%2 else 1.08)
pvis["5"]=("broll",["br_porch"]); pvis["7"]=("broll",["br_bedroom"]); pvis["8"]=("broll",["br_bible"])
pvis["6"]=("cam",1.0); pvis["9"]=("cam",1.08)
alt(pvis,17)
make('prov','/tmp/w/prov',pmap,{"3":0.55,"4":1.0,"14":1.0,"17":0.0,"1":0.8},pvis,{"9":0.0},{},'The Book of Proverbs  KJV','Sleep_Promo_Proverbs',pl,17)
for d,m in (('john',jmap),('prov',pmap)):
    json.dump({c:words[c] for c in m.values()},open(f'/tmp/w/{d}/tr_all.json','w'))
    os.makedirs(f'/tmp/w/{d}/broll',exist_ok=True)
for n,f in (('br_supper','b06'),('br_olive','b07'),('br_bed','b08')): shutil.copy(f'/tmp/clips2/{f}.mp4',f'/tmp/w/john/broll/{n}.mp4')
for n,f in (('br_porch','b01'),('br_bedroom','b00'),('br_bible','b02')): shutil.copy(f'/tmp/clips2/{f}.mp4',f'/tmp/w/prov/broll/{n}.mp4')
print('made')
