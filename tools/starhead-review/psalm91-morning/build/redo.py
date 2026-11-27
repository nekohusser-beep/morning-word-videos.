import json,re,sys
exec(open('voice.py').read().split("paras=json.load(open('paras.json'))")[0])   # reuse model + syn()
n=len(__import__('glob').glob('a*.wav'))
paras={p['i']:p for p in json.load(open('paras.json'))}; tl=json.load(open('tl.json')); redo=json.load(open('redo.json'))['redo']
out=[]; done=set()
for it in tl:
    if it['k']=='s' or it.get('p') not in redo: out.append(it); continue
    P=paras[it['p']]
    if it['p'] in done: continue
    done.add(it['p'])
    if P['k']=='n':
        sents=[s.strip() for s in re.findall(r"[^.?!]+[.?!]+[\"']?",P['t'])]
        for sent in sents:
            f,d=syn(sent); out.append({'k':'n','t':sent,'f':f,'d':d,'p':P['i']})
        out[-1]['para']=1
    else:
        f,d=syn(P['t']); out.append({'k':'v','ref':P['ref'],'t':P['t'],'f':f,'d':d,'para':1,'p':P['i'],'red':P.get('red',[])})
json.dump(out,open('tl.json','w'),indent=1); print('redone',sorted(done))
