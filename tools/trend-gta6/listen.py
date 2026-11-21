import json, sys, soundfile as sf, sherpa_onnx, re, difflib
d='models/sherpa-onnx-whisper-small.en/'
rec=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=d+'small.en-encoder.int8.onnx',decoder=d+'small.en-decoder.int8.onnx',tokens=d+'small.en-tokens.txt',num_threads=4)
L=json.load(open('lines.json'))
norm=lambda s: re.sub(r"[^a-z0-9' ]","",s.lower()).split()
for l in L:
    a,sr=sf.read(f"vo_{l['id']}.wav",dtype='float32')
    st=rec.create_stream(); st.accept_waveform(sr,a); rec.decode_stream(st)
    h=st.result.text.strip()
    r=difflib.SequenceMatcher(None,norm(l['say']),norm(h)).ratio()
    print(l['id'],round(r,2),'\n  WROTE:',l['say'],'\n  HEARD:',h)
    if l['id']=='hook': print('  ts:',getattr(st.result,'timestamps',None)[:10] if getattr(st.result,'timestamps',None) else None, st.result.tokens[:10])
