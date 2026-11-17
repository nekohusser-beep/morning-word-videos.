import os, sys, time, json, gc, traceback, importlib, subprocess
from unittest import mock

T0 = time.time()
W = '/kaggle/working'


def log(*a):
    print('[LT %7.1fs]' % (time.time() - T0), *a, flush=True)


sys.argv = ['inference_example.py', '--config', 'configs/t4.yaml']
sys.path.insert(0, os.getcwd())
sys.path.append('OmniAvatar')

import torch
log('torch', torch.__version__, 'cuda', torch.version.cuda, torch.cuda.get_device_name(0))

import types, importlib.machinery
class _S(types.ModuleType):
    def __getattr__(self,n):
        if n.startswith('__'): raise AttributeError(n)
        return mock.MagicMock()
def mk(n):
    m=_S(n); m.__spec__=importlib.machinery.ModuleSpec(n,None); m.__path__=[]; sys.modules[n]=m
# heavy training-only deps the repo imports but inference never uses
for m in ['wandb', 'lmdb', 'torchao', 'tensorboardX', 'dashscope', 'pycuda', 'pycuda.driver', 'pycuda.autoinit',
          'onnx', 'onnxruntime', 'onnxscript', 'onnxconverter_common', 'flask', 'flask_socketio', 'dominate',
          'pycocotools', 'pycocotools.mask', 'clip', 'open_clip', 'tensorrt']:
    try:
        importlib.import_module(m)
    except Exception:
        mk(m)

PIPMAP = {'cv2': 'opencv-python-headless', 'yaml': 'pyyaml', 'PIL': 'pillow', 'skimage': 'scikit-image',
          'sklearn': 'scikit-learn'}


def heal(fn, tries=15):
    for i in range(tries):
        try:
            return fn()
        except ModuleNotFoundError as e:
            root = (e.name or '').split('.')[0]
            if not root:
                raise
            log('missing module', e.name, '-> pip install')
            rc = subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', PIPMAP.get(root, root)]).returncode
            if rc != 0:
                log('pip failed for', root, '-> shim')
                mk(root)
            importlib.invalidate_caches()
    raise RuntimeError('too many missing modules')


ie = heal(lambda: importlib.import_module('scripts.inference_example'))
args = ie.args
log('imported pipeline module; dtype', args.dtype, 'steps', args.denoising_step_list)

if os.environ.get('LT_DRY'):
    log('DRY IMPORT OK'); sys.exit(0)
dev = torch.device('cuda:0')
torch.set_grad_enabled(False)
prompt = args.prompt

# ---------- Stage A: encode the prompt once, then free the 11 GB text encoder ----------
tA = time.time()


def stageA():
    from wan.modules.tokenizers import HuggingfaceTokenizer
    from wan.modules.t5 import umt5_xxl
    tp = os.path.join(os.path.dirname(args.text_encoder_path), 'google/umt5-xxl/')
    tok = HuggingfaceTokenizer(name=tp, seq_len=512, clean='whitespace')
    m = umt5_xxl(encoder_only=True, return_tokenizer=False, dtype=torch.bfloat16,
                 device=torch.device('cpu')).eval().requires_grad_(False)
    try:
        sd = torch.load(args.text_encoder_path, map_location='cpu', mmap=True, weights_only=True)
    except Exception as ex:
        log('mmap load failed', repr(ex)[:200], '-> plain load')
        sd = torch.load(args.text_encoder_path, map_location='cpu')
    m.load_state_dict(sd)
    del sd
    gc.collect()
    log('umt5 loaded (bf16, cpu)')
    ids, mask = tok([prompt], return_mask=True, add_special_tokens=True)
    seq = mask.gt(0).sum(dim=1).long()

    def enc(d):
        m.to(d)
        ctx = m(ids.to(d), mask.to(d))
        for u, v in zip(ctx, seq.to(d)):
            u[v:] = 0.0
        return ctx.float().cpu()

    try:
        ctx = enc(torch.device('cuda:0'))
        log('text encoded on GPU (bf16)')
    except Exception as ex:
        log('GPU text encode failed:', repr(ex)[:300], '-> CPU')
        m.to('cpu')
        torch.cuda.empty_cache()
        ctx = enc(torch.device('cpu'))
    m.to('cpu')
    del m
    gc.collect()
    torch.cuda.empty_cache()
    return ctx


ctx = stageA()
log('prompt embeds', tuple(ctx.shape), 'finite', bool(torch.isfinite(ctx).all()), 'absmax', float(ctx.abs().max()),
    'stageA s', round(time.time() - tA, 1))
EMB = ctx.to(torch.float16)
if not bool(torch.isfinite(EMB).all()):
    log('WARNING fp16 embeds non-finite (overflow)')


class StubTE(torch.nn.Module):
    def __init__(self, *a, **k):
        super().__init__()
        self.register_buffer('p', EMB.clone(), persistent=False)

    def forward(self, text_prompts):
        return {'prompt_embeds': self.p}


ie.WanTextEncoder = StubTE

# ---------- Stage B: build pipeline ----------
tB = time.time()
pipe = ie.CausalInferencePipeline.from_pretrained(args=args, device=dev)
pipe.text_encoder.to(dev)
torch.cuda.synchronize()
T_LOAD = time.time() - tB
log('pipeline built in %.1fs; gpu mem alloc %.2f GB' % (T_LOAD, torch.cuda.memory_allocated() / 1e9))

FW = []
_orig = pipe._generator_forward


def timed(*a, **k):
    torch.cuda.synchronize()
    t = time.time()
    r = _orig(*a, **k)
    torch.cuda.synchronize()
    dt = time.time() - t
    ts = k.get('timestep')
    is_ctx = bool((ts == 0).all().item()) if ts is not None else False
    FW.append((is_ctx, dt))
    log('forward %d %s %.2fs' % (len(FW), 'ctx' if is_ctx else 'denoise', dt))
    return r


pipe._generator_forward = timed

import numpy as np
from PIL import Image


def mux(video, out_path):
    import imageio
    vnp = (video.squeeze(0).permute(0, 2, 3, 1).cpu().float().numpy() * 255).astype(np.uint8)
    tmp = out_path + '.silent.mp4'
    imageio.mimsave(tmp, vnp, fps=args.fps, codec='libx264', macro_block_size=None,
                    ffmpeg_params=['-crf', '18', '-preset', 'veryfast', '-pix_fmt', 'yuv420p'])
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', tmp, '-i', args.audio_path, '-map', '0:v:0',
                    '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-ar', '48000', '-ac', '1', '-b:a', '96k',
                    '-movflags', '+faststart', '-shortest', out_path], check=True)
    os.remove(tmp)
    return vnp


def gen(tag, H, W_, out_path, seed, dur=5):
    global FW
    FW = []
    lh, lw = H // 8, W_ // 8
    pipe.frame_seq_length = (lh // 2) * (lw // 2)
    pipe.kv_cache1 = None
    ie.args.image_sizes_720 = [[H, W_]]
    args.video_duration = dur
    nf = (dur * args.fps + 4) // 4
    torch.manual_seed(seed)
    noise = torch.randn([1, nf, 16, lh, lw], device=dev, dtype=pipe.dtype)
    torch.cuda.reset_peak_memory_stats()
    log('[%s] start H=%d W=%d latent=%dx%d frame_seq=%d frames=%d' % (tag, H, W_, lh, lw, pipe.frame_seq_length, nf))
    t = time.time()
    video = pipe(noise=noise, text_prompts=prompt, image_path=args.image_path, audio_path=args.audio_path,
                 initial_latent=None, return_latents=False)
    torch.cuda.synchronize()
    t_gen = time.time() - t
    peak = torch.cuda.max_memory_allocated() / 1e9
    nan = int(torch.isnan(video).sum().item())
    fm = video.squeeze(0).float().mean(dim=(1, 2, 3)).cpu()
    black = int((fm < 0.03).sum().item())
    vnp = mux(video, out_path)
    den = [d for c, d in FW if not c]
    cx = [d for c, d in FW if c]
    n = vnp.shape[0]
    idx = [0, n // 2, n - 1]
    os.makedirs(W + '/frames', exist_ok=True)
    for nm, i in zip(['first', 'mid', 'last'], idx):
        Image.fromarray(vnp[i]).save('%s/frames/%s_%s.png' % (W, tag, nm))
    extra = {}
    if tag in ('long', 'narr'):
        sw = vnp[:, 480:700, 80:320, :].mean(axis=(1, 2))
        bk = vnp[:, 0:200, 0:120, :].mean(axis=(1, 2))
        pick = [i for i in (0, 40, 80, 120, 160, 200) if i < n]
        extra['sweater_rgb_at'] = {str(i): [round(float(x), 1) for x in sw[i]] for i in pick}
        extra['bookshelf_rgb_at'] = {str(i): [round(float(x), 1) for x in bk[i]] for i in pick}
        extra['sweater_brightness_every10'] = [round(float(sw[i].mean()), 1) for i in range(0, n, 10)]
        extra['n_frames_total'] = int(n)
        for i in pick:
            Image.fromarray(vnp[i]).save('%s/frames/long_f%d.png' % (W, i))
        for nm, (i, j) in {'long_a': (0, 40), 'long_b': (80, 120), 'long_c': (160, 200)}.items():
            if j < n:
                s2 = Image.new('RGB', (vnp.shape[2] * 2, vnp.shape[1]))
                s2.paste(Image.fromarray(vnp[i]), (0, 0))
                s2.paste(Image.fromarray(vnp[j]), (vnp.shape[2], 0))
                s2.save('%s/%s.png' % (W, nm))
    if tag == 'narr':
        np.save(W + '/narr_frames.npy', vnp)
    res = dict(tag=tag, H=H, W=W_, frames=int(n), fps=args.fps, video_s=round(n / args.fps, 2),
               nan_values=nan, black_frames=black, frame_means_min=float(fm.min()),
               t_pipeline_call_s=round(t_gen, 1), n_denoise_fw=len(den), n_ctx_fw=len(cx),
               denoise_avg_s=round(float(np.mean(den)), 2) if den else None,
               denoise_min_s=round(float(np.min(den)), 2) if den else None,
               denoise_max_s=round(float(np.max(den)), 2) if den else None,
               ctx_avg_s=round(float(np.mean(cx)), 2) if cx else None,
               transformer_total_s=round(sum(d for _, d in FW), 1),
               decode_and_other_s=round(t_gen - sum(d for _, d in FW), 1), peak_gpu_gb=round(peak, 2),
               frame_idx=idx, seed=seed, dur=dur, out=out_path, **extra)
    log('[%s] RESULT %s' % (tag, json.dumps(res)))
    return res


results = {'load_s': round(T_LOAD, 1), 'stageA_s': round(time.time() - tA - T_LOAD, 1)}
T_GEN0 = time.time()
try:
    img = Image.open(args.image_path)
    h, w = img.size[1], img.size[0]
    sel = ie.match_size([[400, 720], [720, 720], [720, 400]], h, w)
    log('still size h=%d w=%d -> selected %s' % (h, w, sel))
    dur = int(open(W + '/narr_dur.txt').read())
    args.audio_path = W + '/narr.wav'
    rN = gen('narr', sel[0], sel[1], W + '/lt_narr.mp4', 42, dur=dur)
    results['narr'] = rN
except Exception:
    results['error'] = traceback.format_exc()[-3000:]
    log('FAILED', results['error'])
results['gen_wall_s'] = round(time.time() - T_GEN0, 1)
results['runner_total_s'] = round(time.time() - T0, 1)
json.dump(results, open(W + '/lt_result7.json', 'w'), indent=1)
log('RUNNER DONE')
