import json, re, difflib, soundfile as sf, sherpa_onnx
d='models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8/'
rec=sherpa_onnx.OfflineRecognizer.from_transducer(encoder=d+'encoder.int8.onnx',decoder=d+'decoder.int8.onnx',joiner=d+'joiner.int8.onnx',tokens=d+'tokens.txt',num_threads=2,model_type='nemo_transducer')
L=json.load(open('lines.json')); out={}
for l in L:
    a,sr=sf.read(f"vo_{l['id']}.wav",dtype='float32')
    st=rec.create_stream(); st.accept_waveform(sr,a); rec.decode_stream(st)
    toks,ts=st.result.tokens,st.result.timestamps
    words=[]
    for t,s in zip(toks,ts):
        if t.startswith(' ') or t.startswith('▁') or not words: words.append([t.strip(' ▁'),s])
        else: words[-1][0]+=t
    words=[w for w in words if w[0]]
    out[l['id']]={'dur':round(len(a)/sr,3),'heard':words}
    print(l['id'],out[l['id']]['dur'],' '.join(f"{w}@{s:.2f}" for w,s in words))
json.dump(out,open('align.json','w'),indent=1)
