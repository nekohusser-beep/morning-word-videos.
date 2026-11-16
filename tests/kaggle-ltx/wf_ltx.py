"""Headless ComfyUI LTX-2.3 distilled (GGUF) text-to-video + audio. Server must be up on 127.0.0.1:8188.
usage: python wf_ltx.py <out_prefix>   env: UNET GEMMA PROMPT NEG WID HGT LEN FPS SEED"""
import json, os, sys, time, urllib.request, uuid
prefix = sys.argv[1]
UNET, GEMMA = os.environ["UNET"], os.environ["GEMMA"]
W, H, L, FPS, SEED = (int(os.environ.get(k, d)) for k, d in (("WID", 480), ("HGT", 832), ("LEN", 97), ("FPS", 24), ("SEED", 20261116)))
POS = os.environ.get("PROMPT") or (
    "Vertical cinematic shot of golden sunrise breaking over a calm mountain lake in soft morning mist. Warm rays of light stream through the clouds "
    "and shimmer on gentle ripples. In the foreground a rugged wooden cross stands on a grassy hill, its silhouette lit from behind by the glow. "
    "The camera pushes in slowly and steadily. Peaceful, reverent mood, rich warm colors, natural film look. Soft wind, distant morning birds and quiet water sounds.")
NEG = os.environ.get("NEG") or "blurry, low quality, distorted, warped, flicker, jitter, text, watermark, subtitles, logo"
SIGMAS = "1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0"
wf = {
 "1": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": UNET}},
 "2": {"class_type": "DualCLIPLoaderGGUF", "inputs": {"clip_name1": GEMMA, "clip_name2": "ltx-2.3-22b-distilled_embeddings_connectors.safetensors", "type": "ltxv"}},
 "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ltx-2.3-22b-distilled_video_vae.safetensors"}},
 "4": {"class_type": "LTXVAudioVAELoader", "inputs": {"ckpt_name": "ltx-2.3-22b-distilled_audio_vae.safetensors"}},
 "5": {"class_type": "CLIPTextEncode", "inputs": {"text": POS, "clip": ["2", 0]}},
 "6": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["2", 0]}},
 "7": {"class_type": "LTXVConditioning", "inputs": {"positive": ["5", 0], "negative": ["6", 0], "frame_rate": float(FPS)}},
 "8": {"class_type": "EmptyLTXVLatentVideo", "inputs": {"width": W, "height": H, "length": L, "batch_size": 1}},
 "9": {"class_type": "LTXVEmptyLatentAudio", "inputs": {"frames_number": L, "frame_rate": FPS, "batch_size": 1, "audio_vae": ["4", 0]}},
 "10": {"class_type": "LTXVConcatAVLatent", "inputs": {"video_latent": ["8", 0], "audio_latent": ["9", 0]}},
 "11": {"class_type": "ManualSigmas", "inputs": {"sigmas": SIGMAS}},
 "12": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
 "13": {"class_type": "CFGGuider", "inputs": {"model": ["1", 0], "positive": ["7", 0], "negative": ["7", 1], "cfg": 1.0}},
 "14": {"class_type": "RandomNoise", "inputs": {"noise_seed": SEED}},
 "15": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["14", 0], "guider": ["13", 0], "sampler": ["12", 0], "sigmas": ["11", 0], "latent_image": ["10", 0]}},
 "16": {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["15", 0]}},
 "17": {"class_type": "VAEDecode", "inputs": {"samples": ["16", 0], "vae": ["3", 0]}},
 "18": {"class_type": "LTXVAudioVAEDecode", "inputs": {"samples": ["16", 1], "audio_vae": ["4", 0]}},
 "19": {"class_type": "SaveImage", "inputs": {"images": ["17", 0], "filename_prefix": prefix}},
 "20": {"class_type": "SaveAudio", "inputs": {"audio": ["18", 0], "filename_prefix": "audio/" + prefix}},
}
base = "http://127.0.0.1:8188"
def post(path, obj):
    req = urllib.request.Request(base + path, data=json.dumps(obj).encode(), headers={"Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode()[:4000]); raise
t0 = time.time()
r = post("/prompt", {"prompt": wf, "client_id": str(uuid.uuid4())})
pid = r["prompt_id"]; print("QUEUED", pid, "unet", UNET, "gemma", GEMMA, f"{W}x{H} len={L} fps={FPS}", flush=True)
n = 0
while True:
    h = json.load(urllib.request.urlopen(f"{base}/history/{pid}"))
    if pid in h:
        st = h[pid].get("status", {})
        print("STATUS", st.get("status_str"), "WALL_SECONDS", round(time.time() - t0, 1))
        if st.get("status_str") != "success":
            print(json.dumps(st)[:5000]); sys.exit(2)
        print("OUTPUTS", json.dumps(h[pid].get("outputs"))[:700]); break
    n += 1
    if n % 6 == 0: print("...running", round(time.time() - t0), "s", flush=True)
    time.sleep(5)
