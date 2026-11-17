#!/usr/bin/env python3
"""Flow (Veo 3.1 Lite) version of the instruction-gag Short. Three 8 s Flow clips (c1_salt, c2_spoon, c3_sip, 720x1280)
get a Kokoro instructor voice (bm_george), big Poppins captions, a text end card, -14 LUFS.
  build_flow.py CLIPS_DIR OUT_DIR      env KOKORO_DIR=/tmp/kk"""
import os, sys, subprocess, json, numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont
CL, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
KD = os.environ.get("KOKORO_DIR", "/tmp/kk"); SR = 24000
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
# (clip, start-in-clip seconds, text)
LINES = [("c1_salt", 0.25, "Okay. Easy one. Grab the salt shaker..."),
         ("c1_salt", 4.1, "...and move it away from the sugar."),
         ("c2_spoon", 0.25, "If anything goes in the wrong cup, pick up the spoon..."),
         ("c2_spoon", 4.6, "...and set it down. I'll bring a fresh one."),
         ("c3_sip", 0.9, "You got all that?")]
CLIPS = ["c1_salt", "c2_spoon", "c3_sip"]; CLEN = 8.0; CARD = 3.6
CARD_TEXT = ["What helps me:", "let them finish", "the sentence.", "Then pick up", "the spoon."]
def run(c): subprocess.run(c, check=True)
from kokoro_onnx import Kokoro
K = Kokoro(f"{KD}/kokoro-v1.0.onnx", f"{KD}/voices-v1.0.bin")
total = len(CLIPS) * CLEN + CARD; mix = np.zeros(int(total * SR) + SR, dtype=np.float32); caps = []
for clip, st, text in LINES:
    a, sr = K.create(text.replace("...", ", ").strip(", ") if text.startswith("...") else text.replace("...", ","), voice="bm_george", speed=0.95, lang="en-us")
    t0 = CLIPS.index(clip) * CLEN + st; d = len(a) / sr
    if st + d > CLEN - 0.15: print(f"WARN line runs past clip: {text} {st+d:.2f}s")
    i = int(t0 * SR); mix[i:i + len(a)] += a.astype(np.float32); caps.append((t0, t0 + d + 0.25, text))
sf.write(f"{OUT}/vo.wav", mix, SR)
# silent video from the clips (hard cuts), scale to 1080x1920, then end card
for c in CLIPS:
    run(["ffmpeg", "-v", "error", "-y", "-i", f"{CL}/{c}.mp4", "-an", "-vf", "scale=1080:1920:flags=lanczos,fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "17", f"{OUT}/{c}_s.mp4"])
img = Image.new("RGB", (1080, 1920), (24, 28, 36)); dr = ImageDraw.Draw(img)
f = ImageFont.truetype(FONT, 104); y = 600
for i, ln in enumerate(CARD_TEXT):
    w = dr.textlength(ln, font=f); col = (255, 214, 102) if i in (0,) else (255, 255, 255)
    dr.text(((1080 - w) / 2, y), ln, font=f, fill=col, stroke_width=3, stroke_fill=(0, 0, 0)); y += 150 if i != 2 else 210
img.save(f"{OUT}/card.png")
run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", str(CARD), "-i", f"{OUT}/card.png", "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "17", f"{OUT}/card.mp4"])
open(f"{OUT}/list.txt", "w").write("".join(f"file '{OUT}/{c}_s.mp4'\n" for c in CLIPS) + f"file '{OUT}/card.mp4'\n")
run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{OUT}/list.txt", "-c", "copy", f"{OUT}/silent.mp4"])
# captions (ASS), big
def ts(t): h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60; return f"{h}:{m:02d}:{s:05.2f}"
ass = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n[V4+ Styles]\n"
       "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
       "Style: Cap,Poppins,84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,6,0,2,60,60,330,1\n\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")
for a, b, t in caps: ass += f"Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{t.replace(chr(10), ' ')}\n"
open(f"{OUT}/caps.ass", "w").write(ass)
# audio: normalise to -14 LUFS (two pass)
run(["ffmpeg", "-v", "error", "-y", "-i", f"{OUT}/vo.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=7:print_format=json", "-f", "null", "-"]) if False else None
r = subprocess.run(["ffmpeg", "-y", "-i", f"{OUT}/vo.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=7:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
j = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
ln = (f"loudnorm=I=-14:TP=-1.5:LRA=7:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
run(["ffmpeg", "-v", "error", "-y", "-i", f"{OUT}/vo.wav", "-af", ln, "-ar", "48000", f"{OUT}/vo_n.wav"])
run(["ffmpeg", "-v", "error", "-y", "-i", f"{OUT}/silent.mp4", "-i", f"{OUT}/vo_n.wav", "-vf", f"ass={OUT}/caps.ass:fontsdir=/usr/share/fonts/truetype/google-fonts", "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-shortest", f"{OUT}/Instructions_Flow_Short.mp4"])
run(["ffmpeg", "-v", "error", "-y", "-i", f"{OUT}/silent.mp4", "-i", f"{OUT}/vo_n.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", f"{OUT}/Instructions_Flow_Short_nocaps.mp4"])
print("built", f"{OUT}/Instructions_Flow_Short.mp4", total, "s")
