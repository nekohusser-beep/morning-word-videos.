# Psalm 91 morning long: Kokoro am_michael speed 0.92 (long-video standard), per-sentence wavs @24k + tl.json (adds 'p' = paragraph index).
import re, json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
k=Kokoro('/home/claude/vet/models/kokoro-v1.0.onnx','/home/claude/vet/models/voices-v1.0.bin')
ONES="zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS="","","twenty","thirty","forty","fifty","sixty","seventy","eighty","ninety"
def words(n):
    if n<20: return ONES[n]
    if n<100: return TENS[n//10]+("-"+ONES[n%10] if n%10 else "")
    h=ONES[n//100]+" hundred"; r=n%100
    return h+(" "+words(r) if r else "")
def speak(t): return re.sub(r'\b(\d+)\b',lambda m:words(int(m.group(1))),t)
PRON={'hast':'hˈæst'}
def phon(t):
    ph=k.tokenizer.phonemize(speak(t),'en-us')
    for w,fix in PRON.items():
        bad=k.tokenizer.phonemize(w,'en-us').strip(' .')
        if bad in ph: ph=ph.replace(bad,fix)
    return ph
n=0
def syn(t):
    global n
    parts=[t]
    if len(phon(t))>480:
        parts=[p.strip() for p in re.findall(r"[^.?!]+[.?!]+[\"']?|[^.?!]+$",t) if p.strip()]
        parts=[q for p in parts for q in ([p] if len(phon(p))<=480 else [x.strip() for x in re.findall(r"[^;:]+[;:]?",p) if x.strip()])]
    segs=[]
    for p in parts:
        s,sr=k.create(phon(p),voice='am_michael',speed=0.92,lang='en-us',is_phonemes=True); segs.append(s); segs.append(np.zeros(int(sr*0.28),dtype=np.float32))
    s=np.concatenate(segs[:-1]); f=f'a{n:03d}.wav'; sf.write(f,s,24000); n+=1
    return f,len(s)/24000
paras=json.load(open('paras.json')); SECT=json.load(open('sections.json')); out=[]
for P in paras:
    if str(P['i']) in SECT: out.append({'k':'s','tag':SECT[str(P['i'])]})
    if P['k']=='n':
        sents=[s.strip() for s in re.findall(r"[^.?!]+[.?!]+[\"']?",P['t'])]
        assert ''.join(sents).replace(' ','')==P['t'].replace(' ','').replace('\n',''),P['t']
        for sent in sents:
            f,d=syn(sent); out.append({'k':'n','t':sent,'f':f,'d':d,'p':P['i']})
        out[-1]['para']=1
    else:
        f,d=syn(P['t']); out.append({'k':'v','ref':P['ref'],'t':P['t'],'f':f,'d':d,'para':1,'p':P['i'],'red':P.get('red',[])})
    print(P['i'],n,flush=True)
json.dump(out,open('tl.json','w'),indent=1)
print('TOTAL speech',round(sum(o.get('d',0) for o in out),1),'s; clips',n)
