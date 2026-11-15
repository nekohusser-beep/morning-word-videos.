"""Stitch a short from Wan 2.2 5B clips + the existing Skip voice lines (run inside the Kaggle runner, ComfyUI server up on :8188).
Per line: trim the voice, make one Wan clip about as long as the line, fit the clip to the voice (ping-pong + trim),
put the voice under it, burn the caption, then concat everything with ffmpeg. usage: python episode.py"""
import glob, json, math, os, subprocess, sys, time, wave, textwrap
import numpy as np
FPS, W, H = 24, 480, 832
cfg = json.load(open("shots.json"))
GAP, CAP, SEED = cfg["gap"], cfg["cap_frames"], cfg["seed"]
os.makedirs("ep", exist_ok=True)
OUT = "/kaggle/working" if os.path.isdir("/kaggle/working") else "ep"
FONT = next((f for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf") if os.path.exists(f)), None)
print("FONT", FONT)
def run(*a, **k): return subprocess.run([str(x) for x in a], check=True, **k)
segs, total_expected, t0_all = [], 0.0, time.time()
for s in cfg["shots"]:
    i = s["idx"]
    run("ffmpeg", "-y", "-loglevel", "error", "-i", s["audio"], "-ar", "44100", "-ac", "1", "-sample_fmt", "s16", f"ep/a{i}.wav")
    with wave.open(f"ep/a{i}.wav") as w: raw = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    nz = np.where(np.abs(raw.astype(np.float32) / 32768) > 0.01)[0]
    a0, a1 = max(0, nz[0] - 400), min(len(raw), nz[-1] + 2000)
    with wave.open(f"ep/t{i}.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(44100); w.writeframes(raw[a0:a1].tobytes())
    dur = (a1 - a0) / 44100; total = dur + GAP; total_expected += total
    frames = min(CAP, 4 * math.ceil(dur * FPS / 4) + 1)
    print(f"== line {i}: voice {dur:.2f}s, clip frames {frames}", flush=True)
    ok = False
    for fr in (frames, 73, 49):
        for old in glob.glob(f"ComfyUI/output/wan5b/ep{i}_*.png"): os.remove(old)
        env = dict(os.environ, PROMPT=s["prompt"])
        t1 = time.time()
        r = subprocess.run(["python", "wf.py", s["still"], f"wan5b/ep{i}", str(fr), str(W), str(H), str(SEED), "skip"], env=env)
        print(f"   wan {fr} frames: exit {r.returncode}, {time.time() - t1:.0f}s", flush=True)
        if r.returncode == 0: frames, ok = fr, True; break
    if not ok: print("LINE FAILED", i); sys.exit(3)
    run("ffmpeg", "-y", "-loglevel", "error", "-framerate", FPS, "-i", f"ComfyUI/output/wan5b/ep{i}_%05d_.png", "-c:v", "libx264", "-crf", 14, "-pix_fmt", "yuv420p", f"ep/raw{i}.mp4")
    run("ffmpeg", "-y", "-loglevel", "error", "-i", f"ep/raw{i}.mp4", "-filter_complex", "[0:v]split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1[v]", "-map", "[v]", "-c:v", "libx264", "-crf", 14, "-pix_fmt", "yuv420p", f"ep/pp{i}.mp4")
    cap = "\n".join(textwrap.wrap(s["caption"], 24)); open(f"ep/cap{i}.txt", "w").write(cap)
    vf = "scale=1080:1920:flags=lanczos"
    if FONT: vf += f",drawtext=fontfile={FONT}:textfile=ep/cap{i}.txt:fontsize=70:fontcolor=white:borderw=7:bordercolor=black:x=(w-text_w)/2:y=h-560:line_spacing=12:enable='lt(t,{dur:.3f})'"
    vf += f",fps={FPS},format=yuv420p"
    def seg(vf):
        run("ffmpeg", "-y", "-loglevel", "error", "-stream_loop", -1, "-i", f"ep/pp{i}.mp4", "-i", f"ep/t{i}.wav", "-filter_complex", f"[0:v]{vf}[v];[1:a]apad,aresample=44100[a]",
            "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}", "-c:v", "libx264", "-crf", 18, "-preset", "veryfast", "-c:a", "aac", "-b:a", "192k", f"ep/seg{i}.mp4")
    try: seg(vf)
    except subprocess.CalledProcessError:
        print("   drawtext failed, building this segment without captions", flush=True); seg(f"scale=1080:1920:flags=lanczos,fps={FPS},format=yuv420p")
    segs.append(f"ep/seg{i}.mp4")
open("ep/list.txt", "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in segs))
final = os.path.join(OUT, "skip_ep2b_wan_pilot.mp4")
run("ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", 0, "-i", "ep/list.txt", "-c", "copy", final)
for st in ("v:0", "a:0"):
    print("FINAL", st, subprocess.run(["ffprobe", "-v", "error", "-select_streams", st, "-show_entries", "stream=codec_name,width,height,duration", "-of", "csv=p=0", final], capture_output=True, text=True).stdout.strip())
print("FINAL_BYTES", os.path.getsize(final), "EXPECTED_SECONDS", round(total_expected, 2), "WALL_MINUTES", round((time.time() - t0_all) / 60, 1))
