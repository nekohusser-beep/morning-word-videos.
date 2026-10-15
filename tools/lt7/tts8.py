import sys, os, random, time, re
import numpy as np
import torch
import torchaudio as ta
torch.manual_seed(42); np.random.seed(42); random.seed(42)
TEXT = open(sys.argv[1]).read().strip(); REF = sys.argv[2]; OUT = sys.argv[3]
t = time.time()
from chatterbox.tts import ChatterboxTTS
m = ChatterboxTTS.from_pretrained(device='cuda')
print('loaded', round(time.time() - t, 1), flush=True)
t = time.time()
sents = [x.strip() for x in re.split(r'(?<=[.!?])\s+', TEXT) if x.strip()]
parts = []
gap = torch.zeros(1, int(m.sr * 0.28))
for i, s in enumerate(sents):
    w = m.generate(s, audio_prompt_path=REF, exaggeration=0.65, cfg_weight=0.5).cpu()
    parts.append(w)
    if i < len(sents) - 1:
        parts.append(gap)
    print('sent', i, round(w.shape[-1] / m.sr, 2), 's', flush=True)
wav = torch.cat(parts, dim=-1)
ta.save(OUT, wav, m.sr)
print('generated', round(time.time() - t, 1), 'sr', m.sr, 'samples', wav.shape, flush=True)
