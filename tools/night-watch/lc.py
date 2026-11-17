import json, re, numpy as np, soundfile as sf, sherpa_onnx, subprocess, difflib
d='sherpa-onnx-whisper-small.en/'
r=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=d+'small.en-encoder.int8.onnx',decoder=d+'small.en-decoder.int8.onnx',tokens=d+'small.en-tokens.txt',language='en',task='transcribe',num_threads=4)
tl=json.load(open('v/tl.json')); T=json.load(open('timeline.json'))
subprocess.run(['ffmpeg','-y','-v','error','-i','nightwatch_nocaps.mp4','-ac','1','-ar','16000','final16.wav'],check=True)
a,sr=sf.read('final16.wav',dtype='float32')
norm=lambda s: re.sub(r'[^a-z0-9 ]','',s.lower().replace('-',' ')).split()
num={'130':'one hundred thirty'}
bad=0
for i,l in enumerate(tl):
    s=T['starts'][i]-0.15; e=T['starts'][i]+l['dur']+0.25
    seg=a[int(max(0,s)*sr):int(e*sr)]
    st=r.create_stream(); st.accept_waveform(sr,seg); r.decode_stream(st)
    hyp=st.result.text.strip()
    ref=l['text']
    h=norm(hyp.replace('130','one hundred thirty').replace('6','six')); rr=norm(ref)
    m=difflib.SequenceMatcher(None,rr,h).ratio()
    print(i+1,round(m,2),'|',hyp); 
    if m<0.9: bad+=1; print('   REF:',ref)
print('lines under 0.90:',bad)
