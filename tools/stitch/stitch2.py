#!/usr/bin/env python3
"""stitch2: fused-seam stitcher for talking-head clips (Oct 22 2026 FFmpeg Bible).

Usage: stitch2.py CFG.json
CFG: {"clips":["c1.mp4",...], "words":[[{"text","start","end"},...], ...] (one list per clip),
      "lines":["caption text for clip 1", ...] (optional, KJV-proofed script text),
      "out":"out.mp4", "work":"/tmp/work", "fps":24, "W":1080, "H":1920,
      "head_pad":0.35, "tail_pad":0.55, "dissolve":0.30, "hard":0.04, "ssim_min":0.60,
      "punch":1.08, "lufs":-14, "tp":-1.0}
Rules: trim to speech by word times; per-seam SSIM picks dissolve (similar) or hard cut + alternating
punch-in (pose jump); dissolve seams keep one scale so the seam stays fused; per-clip constant gain;
captions burned last from word times; two-pass loudnorm; one final x264 encode.
"""
import json, re, subprocess, sys, os, difflib

def sh(cmd, **kw):
    return subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, **kw)

def probe_dur(p):
    return float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).stdout)

def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())

NUMS = {"derek":"derrick","1":"one","2":"two","3":"three","4":"four","5":"five","6":"six","7":"seven","8":"eight","9":"nine","10":"ten",
        "11":"eleven","12":"twelve","20":"twenty","28":"twentyeight","29":"twentynine"}

def n2(w):
    n = norm(w)
    return NUMS.get(n, n)

def align_words(script_text, words):
    """map script words to whisper times (difflib); interpolate gaps."""
    sw = script_text.split()
    sn = [n2(w) for w in sw]
    wn = [n2(w["text"]) for w in words]
    sm = difflib.SequenceMatcher(a=sn, b=wn, autojunk=False)
    t = [None] * len(sw)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                t[i1 + k] = (words[j1 + k]["start"], words[j1 + k]["end"])
    # fill gaps by interpolation
    last_end = words[0]["start"] if words else 0.0
    i = 0
    while i < len(t):
        if t[i] is None:
            j = i
            while j < len(t) and t[j] is None:
                j += 1
            nxt = t[j][0] if j < len(t) else (words[-1]["end"] if words else last_end + 0.3 * (j - i))
            step = (nxt - last_end) / (j - i + 0.0)
            for k in range(i, j):
                t[k] = (last_end + step * (k - i), last_end + step * (k - i + 1))
            i = j
        else:
            last_end = t[i][1]
            i += 1
    return [(sw[k], t[k][0], t[k][1]) for k in range(len(sw))]

def ass_time(s):
    h = int(s // 3600); m = int(s % 3600 // 60); sec = s % 60
    return f"{h}:{m:02d}:{sec:05.2f}"

def build_ass(cues, W, H, path, fontsize, outline, marginv):
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,Poppins,{fontsize},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,{outline},1,2,150,150,{marginv},1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    lines = []
    for (s, e, txt) in cues:
        txt = txt.replace("{", "").replace("}", "")
        lines.append(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},Default,,0,0,0,,{{\\fscx88\\fscy88\\t(0,90,\\fscx100\\fscy100)}}{txt}")
    open(path, "w").write(hdr + "\n".join(lines) + "\n")

def main(cfgp):
    cfg = json.load(open(cfgp))
    clips = cfg["clips"]; W = cfg.get("W", 1080); H = cfg.get("H", 1920); fps = cfg.get("fps", 24)
    hp = cfg.get("head_pad", 0.35); tp_ = cfg.get("tail_pad", 0.55)
    dis = cfg.get("dissolve", 0.30); hard = cfg.get("hard", 0.04); ssim_min = cfg.get("ssim_min", 0.60)
    punch = cfg.get("punch", 1.08); lufs = cfg.get("lufs", -14); tpk = cfg.get("tp", -1.5)
    work = cfg.get("work", "/tmp/stitch2"); os.makedirs(work, exist_ok=True)
    out = cfg["out"]
    n = len(clips)
    # 1. trims by word times
    ab = []
    for i, c in enumerate(clips):
        d = probe_dur(c); w = cfg["words"][i]
        hpi = cfg["heads"][i] if cfg.get("heads") else hp; tpi = cfg["tails"][i] if cfg.get("tails") else tp_
        a = max(0.0, w[0]["start"] - hpi); b = min(d, w[-1]["end"] + tpi)
        ab.append((a, b))
    L = [b - a for a, b in ab]
    # 2. per-seam SSIM decision
    seam = []
    for i in range(n - 1):
        f1 = f"{work}/s{i}_end.png"; f2 = f"{work}/s{i}_start.png"
        sh(["ffmpeg", "-v", "error", "-y", "-ss", f"{ab[i][1] - 1.0 / fps:.3f}", "-i", clips[i], "-frames:v", "1", "-vf", "scale=360:-1,format=gray", f1])
        sh(["ffmpeg", "-v", "error", "-y", "-ss", f"{ab[i + 1][0]:.3f}", "-i", clips[i + 1], "-frames:v", "1", "-vf", "scale=360:-1,format=gray", f2])
        r = sh(["ffmpeg", "-i", f1, "-i", f2, "-lavfi", "ssim", "-f", "null", "-"])
        m = re.search(r"All:([0-9.]+)", r.stderr)
        s = float(m.group(1)) if m else 0.0
        seam.append({"ssim": s, "type": "dissolve" if s >= ssim_min else "hard"})
    if cfg.get("seam_force"):
        for i, ty in enumerate(cfg["seam_force"]):
            if ty: seam[i]["type"] = ty
    d = [dis if s["type"] == "dissolve" else hard for s in seam]
    # 3. punch scale per clip: alternate only across hard seams
    scale = [1.0]
    for i in range(n - 1):
        if seam[i]["type"] == "hard":
            scale.append(punch if scale[-1] == 1.0 else 1.0)
        else:
            scale.append(scale[-1])
    if cfg.get("scales"):
        scale = list(cfg["scales"])
    # 4. per-clip gain to common -20 LUFS speech level
    gains = []
    for i, c in enumerate(clips):
        r = sh(["ffmpeg", "-v", "info", "-ss", f"{ab[i][0]:.3f}", "-t", f"{L[i]:.3f}", "-i", c, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"])
        m = re.findall(r"I:\s+(-?[0-9.]+) LUFS", r.stderr)
        li = float(m[-1]) if m else -20.0
        gains.append(max(-12.0, min(12.0, -20.0 - li)))
    # 5. filter graph
    vf = []; af = []
    for i in range(n):
        a, b = ab[i]; s = scale[i]
        asp = f"crop=min(iw\\,trunc(ih*{W}/{H}/2)*2):min(ih\\,trunc(iw*{H}/{W}/2)*2),"
        crop = asp + ("" if s == 1.0 else f"crop=iw/{s}:ih/{s}:(iw-iw/{s})/2:(ih-ih/{s})/2,")
        vf.append(f"[{i}:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS,fps={fps},{crop}scale={W}:{H}:flags=lanczos,cas=0.25,setsar=1,format=yuv420p[v{i}]")
        af.append(f"[{i}:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS,aresample=48000,highpass=f=70,volume={gains[i]:.2f}dB[a{i}]")
    cur = "v0"; acur = "a0"; cum = 0.0; cumd = 0.0
    for i in range(n - 1):
        cum += L[i]; cumd += d[i]
        off = cum - cumd
        vf.append(f"[{cur}][v{i + 1}]xfade=transition=fade:duration={d[i]:.3f}:offset={off:.3f}[x{i}]")
        cur = f"x{i}"
        af.append(f"[{acur}][a{i + 1}]acrossfade=d={d[i]:.3f}:c1=tri:c2=tri[ax{i}]")
        acur = f"ax{i}"
    total = sum(L) - sum(d)
    # captions: output timeline offsets
    starts = []; acc = 0.0
    for i in range(n):
        starts.append(acc)
        acc += L[i] - (d[i] if i < n - 1 else 0)
    cues = []
    for i in range(n):
        text = cfg["lines"][i] if cfg.get("lines") else " ".join(w["text"] for w in cfg["words"][i])
        al = align_words(text, cfg["words"][i])
        # group <=4 words, break after punctuation
        grp = []; cur_g = []
        for (w, s0, e0) in al:
            cur_g.append((w, s0, e0))
            if len(cur_g) >= 4 or re.search(r"[.,;:?!]$", w):
                grp.append(cur_g); cur_g = []
        if cur_g:
            grp.append(cur_g)
        for gi, g in enumerate(grp):
            s0 = g[0][1] - ab[i][0] + starts[i]
            e0 = (grp[gi + 1][0][1] - ab[i][0] + starts[i]) if gi + 1 < len(grp) else g[-1][2] - ab[i][0] + starts[i] + 0.25
            e0 = min(e0, g[-1][2] - ab[i][0] + starts[i] + 0.45)
            cues.append((s0, e0, " ".join(x[0] for x in g)))
    k = W / 720.0
    ass = f"{work}/caps.ass"
    build_ass(cues, W, H, ass, round(52 * k), round(4.2 * k, 1), round(205 * k))
    with open(f"{work}/caps.srt", "w") as f:
        for ci, (s0, e0, t) in enumerate(cues, 1):
            def st(x):
                return f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{int(x % 60):02d},{int(round((x % 1) * 1000)):03d}"
            f.write(f"{ci}\n{st(s0)} --> {st(e0)}\n{t}\n\n")
    inputs = []
    for c in clips:
        inputs += ["-i", c]
    # audio master pass 1 (mix) -> measure -> pass 2
    amix = f"{work}/mix.wav"
    sh(["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", ";".join(af), "-map", f"[{acur}]", "-ar", "48000", "-c:a", "pcm_s16le", amix])
    r = sh(["ffmpeg", "-i", amix, "-af", f"loudnorm=I={lufs}:TP={tpk}:LRA=11:print_format=json", "-f", "null", "-"])
    j = json.loads(r.stderr[r.stderr.rindex("{"):])
    ln = (f"loudnorm=I={lufs}:TP={tpk}:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
          f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    amaster = f"{work}/master.wav"
    sh(["ffmpeg", "-v", "error", "-y", "-i", amix, "-af", ln, "-ar", "48000", amaster])
    # video + captions + mux, one encode
    vgraph = ";".join(vf) + f";[{cur}]subtitles={ass}:fontsdir=/usr/share/fonts/truetype/google-fonts[vout]"
    cmd = ["ffmpeg", "-v", "error", "-y"] + inputs + ["-i", amaster, "-filter_complex", vgraph, "-map", "[vout]", "-map", f"{n}:a",
           "-c:v", "libx264", "-preset", "slow"] + (["-b:v", cfg["vb"], "-maxrate", cfg["vb"], "-bufsize", "4M"] if cfg.get("vb") else ["-crf", str(cfg.get("crf", 20))]) + [ "-pix_fmt", "yuv420p", "-profile:v", "high", "-bf", "2", "-g", str(fps // 2),
           "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-r", str(fps),
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", out]
    r = sh(cmd)
    if r.returncode:
        print(r.stderr[-1500:]); sys.exit(1)
    rep = {"trims": ab, "seams": seam, "scale": scale, "gains": gains, "total_expected": total, "cues": len(cues), "out": out}
    json.dump(rep, open(f"{work}/report.json", "w"), indent=1)
    print(json.dumps(rep, indent=1))

if __name__ == "__main__":
    main(sys.argv[1])
