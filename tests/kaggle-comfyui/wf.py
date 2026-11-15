"""Headless ComfyUI Wan 2.2 5B image-to-video test. Run after the server is up on 127.0.0.1:8188.
usage: python wf.py <image_name_in_comfy_input> <out_prefix> <length> <width> <height> <seed>"""
import json, sys, time, urllib.request, uuid
img, prefix, length, width, height, seed = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
key = sys.argv[7] if len(sys.argv) > 7 else "skip"
POS = ("A cartoon man with spiky blue hair and an orange hoodie angrily points at an empty office break room fridge "
       "with one hand while holding a crumpled paper lunch bag in the other. He shakes the bag, his eyebrows furrow "
       "and his mouth moves as he complains. Flat 2D cartoon style, bold black outlines, steady background, slow camera push-in.")
NEG = "blurry, distorted face, warped mouth, extra fingers, morphing, flicker, jitter, static image, low quality, text, watermark, subtitles"
if key == "derrick":
    POS = ("A man in a dark blazer and white t-shirt sits in a warm podcast studio and speaks calmly to the camera. Natural blinking, "
           "small head movements, a slight friendly smile, relaxed shoulders. Realistic photo, warm soft lighting, steady camera, shallow depth of field.")
wf = {
 "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "wan2.2_ti2v_5B_fp16.safetensors", "weight_dtype": "default"}},
 "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan", "device": "default"}},
 "3": {"class_type": "VAELoader", "inputs": {"vae_name": "wan2.2_vae.safetensors"}},
 "4": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["1", 0], "shift": 8.0}},
 "5": {"class_type": "CLIPTextEncode", "inputs": {"text": POS, "clip": ["2", 0]}},
 "6": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["2", 0]}},
 "7": {"class_type": "LoadImage", "inputs": {"image": img}},
 "8": {"class_type": "Wan22ImageToVideoLatent", "inputs": {"vae": ["3", 0], "width": width, "height": height, "length": length, "batch_size": 1, "start_image": ["7", 0]}},
 "9": {"class_type": "KSampler", "inputs": {"model": ["4", 0], "seed": seed, "steps": 20, "cfg": 5.0, "sampler_name": "uni_pc", "scheduler": "simple",
        "positive": ["5", 0], "negative": ["6", 0], "latent_image": ["8", 0], "denoise": 1.0}},
 "10": {"class_type": "VAEDecode", "inputs": {"samples": ["9", 0], "vae": ["3", 0]}},
 "11": {"class_type": "SaveImage", "inputs": {"images": ["10", 0], "filename_prefix": prefix}},
}
base = "http://127.0.0.1:8188"
def post(path, obj):
    req = urllib.request.Request(base + path, data=json.dumps(obj).encode(), headers={"Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode()[:3000]); raise
t0 = time.time()
r = post("/prompt", {"prompt": wf, "client_id": str(uuid.uuid4())})
pid = r["prompt_id"]; print("QUEUED", pid, flush=True)
while True:
    h = json.load(urllib.request.urlopen(f"{base}/history/{pid}"))
    if pid in h:
        st = h[pid].get("status", {})
        print("STATUS", st.get("status_str"), "WALL_SECONDS", round(time.time() - t0, 1))
        if st.get("status_str") != "success":
            print(json.dumps(st)[:4000]); sys.exit(2)
        print("OUTPUTS", json.dumps(h[pid].get("outputs"))[:600]); break
    time.sleep(5)
