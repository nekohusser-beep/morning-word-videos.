import sys, os, random, time
import numpy as np
import torch
import torchaudio as ta
torch.manual_seed(42); np.random.seed(42); random.seed(42)
TEXT = sys.argv[1]; REF = sys.argv[2]; OUT = sys.argv[3]
t = time.time()
from chatterbox.tts import ChatterboxTTS
m = ChatterboxTTS.from_pretrained(device='cuda')
print('loaded', round(time.time() - t, 1), flush=True)
t = time.time()
wav = m.generate(TEXT, audio_prompt_path=REF, exaggeration=0.5, cfg_weight=0.5)
ta.save(OUT, wav.cpu(), m.sr)
print('generated', round(time.time() - t, 1), 'sr', m.sr, 'samples', wav.shape, flush=True)
