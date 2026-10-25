#!/usr/bin/env python3
"""ps51 compose: per-clip pre-composite. Crops the Hailuo watermark, lays B-roll windows (silent) over Derrick's face,
keeps Derrick's audio untouched, same timeline as the source clip.
Usage: compose.py PLAN.json
PLAN: {"src":dir, "broll":dir, "out":dir, "xf":0.30, "crf":12, "clips": {"1":[[t0,t1,"name",{opts}],...], ...}}
  t0/t1 = seconds on the source clip.  opts (all optional): ss = start offset inside the B-roll file (s),
  fi / fo = 0 to disable the alpha fade in / out.
Auto rules: t0 <= 0.05 -> no fade in; t1 >= clip end - 0.05 -> no fade out (so clip seams carry no face flash);
two windows closer than 0.6 s share their midpoint as a hard cut (no face flicker between two B-roll shots)."""
import json, subprocess, sys, os

def sh(c):
    r = subprocess.run(c, capture_output=True, text=True)
    if r.returncode:
        print("FAILED:", " ".join(c)[:300], "\n", r.stderr[-1800:]); sys.exit(1)
    return r.stdout

def dur(p):
    return float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))

def main(planp):
    P = json.load(open(planp))
    src, brd, out = P["src"], P["broll"], P["out"]; xf = P.get("xf", 0.30); crf = P.get("crf", 12)
    W, H, FPS = 768, 1344, 24
    os.makedirs(out, exist_ok=True)
    rep = {}
    for n, wins in P["clips"].items():
        clip = f"{src}/b{n}.mp4"; o = f"{out}/c{n}.mp4"
        d = dur(clip)
        wins = [[float(w[0]), min(float(w[1]), d), w[2], dict(w[3]) if len(w) > 3 else {}] for w in wins]
        wins.sort(key=lambda w: w[0])
        for w in wins:
            if w[0] <= 0.05: w[0] = 0.0; w[3].setdefault("fi", 0)
            if w[1] >= d - 0.05: w[1] = d; w[3].setdefault("fo", 0)
        for a, b in zip(wins[:-1], wins[1:]):
            if b[0] - a[1] < 0.6:
                mid = round((a[1] + b[0]) / 2, 3)
                a[1] = mid; b[0] = mid; a[3]["fo"] = 0; b[3]["fi"] = 0
        inputs = ["-i", clip]; fc = []
        # watermark sits in the bottom ~4.5 %: crop 4.8 % off the bottom and re-fill the frame (1.05x, no distortion)
        cw = int(round(W * 0.952 / 2) * 2); ch = int(round(H * 0.952 / 2) * 2)
        z, zy = P.get("zoom", {}).get(n, [1.0, 0.0])      # optional tighter framing for a wider clip (matches neighbours)
        cwz = int(round(cw / z / 2) * 2); chz = int(round(ch / z / 2) * 2)
        yz = min(int(round(H * zy)), H - chz - int(H * 0.048))
        fc.append(f"[0:v]crop={cwz}:{chz}:{(W - cwz) // 2}:{max(0, yz)},scale={W}:{H}:flags=lanczos,fps={FPS},setsar=1,format=yuv420p[base]")
        cur = "base"; info = []
        for i, (t0, t1, name, op) in enumerate(wins, 1):
            bf = f"{brd}/{name}.mp4"
            if not os.path.exists(bf):
                print("missing broll", bf); sys.exit(1)
            inputs += ["-i", bf]
            bd = dur(bf); ss = float(op.get("ss", 0)); win = t1 - t0
            avail = bd - ss - 0.05
            stretch = max(1.0, win / avail)
            if stretch > 1.20:
                print(f"WARN clip {n} window {t0}-{t1} needs x{stretch:.2f} on {name} ({bd:.2f}s, ss {ss})")
            fi = float(op.get("fi", 1)) * xf; fo = float(op.get("fo", 1)) * xf
            fades = ""
            if fi > 0: fades += f"fade=t=in:st=0:d={fi}:alpha=1,"
            if fo > 0: fades += f"fade=t=out:st={max(0.0, win - fo):.3f}:d={fo}:alpha=1,"
            fc.append(
                f"[{i}:v]trim=start={ss:.3f},setpts=PTS-STARTPTS,setpts={stretch:.4f}*PTS,fps={FPS},trim=duration={win:.3f},setpts=PTS-STARTPTS,"
                f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1,"
                f"eq=contrast=1.04:saturation=1.04,format=yuva420p,{fades}setpts=PTS+{t0:.3f}/TB[b{i}]")
            fc.append(f"[{cur}][b{i}]overlay=eof_action=pass:enable='between(t,{t0:.3f},{t1:.3f})'[o{i}]")
            cur = f"o{i}"; info.append({"win": [round(t0, 3), round(t1, 3)], "broll": name, "ss": ss, "stretch": round(stretch, 3), "fi": fi > 0, "fo": fo > 0})
        cmd = ["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", ";".join(fc), "-map", f"[{cur}]", "-map", "0:a",
               "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", "-r", str(FPS),
               "-c:a", "copy", "-movflags", "+faststart", o]
        sh(cmd)
        rep[n] = {"dur": round(d, 3), "out_dur": round(dur(o), 3), "wins": info}
        print("clip", n, json.dumps(rep[n]))
    json.dump(rep, open(f"{out}/compose_report.json", "w"), indent=1)

if __name__ == "__main__":
    main(sys.argv[1])
