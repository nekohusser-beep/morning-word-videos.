import sys, re, time, random
import numpy as np, torch, torchaudio as ta
torch.manual_seed(42); np.random.seed(42); random.seed(42)
TEXT = open(sys.argv[1]).read().strip(); REF = sys.argv[2]; OUT = sys.argv[3]
from chatterbox.tts import ChatterboxTTS
m = ChatterboxTTS.from_pretrained(device='cpu')
paras = [p.strip() for p in TEXT.split('\n\n') if p.strip()]
parts = []
short = torch.zeros(1, int(m.sr * 0.30))
long = torch.zeros(1, int(m.sr * 0.75))
for pi, p in enumerate(paras):
    sents = [x.strip() for x in re.split(r'(?<=[.!?])\s+', p) if x.strip()]
    for si, s in enumerate(sents):
        t = time.time()
        w = m.generate(s, audio_prompt_path=REF, exaggeration=0.5, cfg_weight=0.4).cpu()
        parts.append(w)
        if si < len(sents) - 1: parts.append(short)
        print(pi, si, round(w.shape[-1] / m.sr, 2), 's in', round(time.time() - t), 's', flush=True)
    if pi < len(paras) - 1: parts.append(long)
ta.save(OUT, torch.cat(parts, dim=-1), m.sr)
