#!/usr/bin/env python3
"""IQ Vid thumbnail picture-read (runs on a GitHub runner; needs torch + open_clip).

  python3 tools/iqvid/thumb_clip.py "img1|img2" --out reports/iqvid/thumbclip-1 \
      [--ref "137:-0.0873,79:-0.0814"] [--ref-entropy 7.3046] [--models "ViT-B-32-quickgelu:openai,..."]

For every image (repo path or https URL) and every model it writes:
  concept scores   zero-shot read of the picture against our own prompt pairs
                   (payoff, open question, color pop, over-saturated, clear subject, face emotion)
  embedding dims   the values of chosen embedding dimensions, raw and length-normalized, with two
                   ways of fitting the picture to the model (center crop, squash)
  --ref            reference values for embedding dimensions from another scorer: the model and fit
                   whose dimensions land closest are reported, to identify which model that scorer uses
  --ref-entropy    reference gray-level entropy: reports which picture size reproduces it

THIS IS A TEST HARNESS, NOT A SCORER (rule set Nov 14 2026). Its numbers rank the candidate thumbnails of
one video. Nothing from here feeds the IQ Vid thumbnail score until one model predicts 3 fresh vidIQ
thumbnail scores within 3 points each, with the predictions written down before the scores are bought
(kingdom-brain tools/iqvid/thumb_score.py --gate; log each one with --log ... --candidate name=prediction).
"""
import argparse, io, json, math, sys, urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

PAIRS = {
    "payoff": ("a video thumbnail that makes clear what the viewer will get", "a vague picture with no clear point"),
    "question": ("a picture that raises a question or mystery the viewer wants answered", "a picture that shows everything and leaves nothing to wonder about"),
    "color_pop": ("a vivid picture with one color that pops", "a dull washed-out picture"),
    "over_saturated": ("a picture with garish over-saturated colors", "a picture with balanced natural colors"),
    "clear_subject": ("a picture with one clear subject", "a busy cluttered picture"),
    "face_emotion": ("a close-up face showing strong emotion", "a picture with no people"),
}
MODELS = ["ViT-B-32-quickgelu:openai", "ViT-B-16-quickgelu:openai", "ViT-B-32:openai", "ViT-B-16:openai",
          "ViT-L-14-quickgelu:openai", "ViT-B-32:laion2b_s34b_b79k", "ViT-B-16:laion2b_s34b_b88k"]
MEAN, STD = (0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711)


def load(src):
    if src.startswith("http"):
        req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
        return Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=30).read())).convert("RGB")
    return Image.open(src).convert("RGB")


def entropy(img, size=None):
    g = img.convert("L")
    if size:
        g = g.resize(size, Image.BILINEAR)
    h = np.bincount(np.asarray(g).ravel(), minlength=256) / (g.size[0] * g.size[1])
    h = h[h > 0]
    return float(-(h * np.log2(h)).sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("images")
    ap.add_argument("--out", required=True)
    ap.add_argument("--ref", default="")
    ap.add_argument("--ref-entropy", type=float, default=None)
    ap.add_argument("--models", default="")
    a = ap.parse_args()
    import torch
    import open_clip

    srcs = [s.strip() for s in a.images.split("|") if s.strip()]
    ref = {int(k): float(v) for k, v in (x.split(":") for x in a.ref.split(",") if ":" in x)}
    models = [m.strip() for m in a.models.split(",") if m.strip()] or MODELS
    imgs, res = {}, {"images": {}, "models": {}, "ref": ref, "errors": []}
    for s in srcs:
        try:
            imgs[s] = load(s)
            e = {"size": imgs[s].size, "entropy_native": round(entropy(imgs[s]), 4)}
            for sz in (224, 256, 299, 336, 384, 512):
                e[f"entropy_{sz}sq"] = round(entropy(imgs[s], (sz, sz)), 4)
            for w, h in ((320, 180), (480, 270), (640, 360), (1280, 720)):
                e[f"entropy_{w}x{h}"] = round(entropy(imgs[s], (w, h)), 4)
            res["images"][s] = e
        except Exception as ex:  # noqa: BLE001
            res["errors"].append(f"image {s}: {ex}")
    lines = []
    if a.ref_entropy is not None:
        lines.append(f"=== entropy vs reference {a.ref_entropy} ===")
        for s, e in res["images"].items():
            best = min((k for k in e if k.startswith("entropy")), key=lambda k: abs(e[k] - a.ref_entropy))
            lines.append(f"{s[-48:]} | closest {best} = {e[best]} (off {abs(e[best]-a.ref_entropy):.4f}) | native {e['entropy_native']}")
    best_match = None
    for spec in models:
        name, _, pre = spec.partition(":")
        try:
            model, _, preprocess = open_clip.create_model_and_transforms(name, pretrained=pre)
            tok = open_clip.get_tokenizer(name)
            model.eval()
        except Exception as ex:  # noqa: BLE001
            res["errors"].append(f"model {spec}: {str(ex)[:200]}")
            continue
        res["models"][spec] = {}
        lines.append(f"=== {spec} ===")
        with torch.no_grad():
            texts = [t for pair in PAIRS.values() for t in pair]
            tf = model.encode_text(tok(texts))
            tf = tf / tf.norm(dim=-1, keepdim=True)
            for s, im in imgs.items():
                out = {}
                size = preprocess.transforms[0].size if hasattr(preprocess.transforms[0], "size") else 224
                size = size if isinstance(size, int) else size[0]
                sq = np.asarray(im.resize((size, size), Image.BICUBIC), dtype=np.float32) / 255
                sq = torch.tensor(((sq - MEAN) / STD).transpose(2, 0, 1), dtype=torch.float32).unsqueeze(0)
                for fit, x in (("crop", preprocess(im).unsqueeze(0)), ("squash", sq)):
                    f = model.encode_image(x)[0]
                    fn = f / f.norm()
                    d = {"dim": int(f.shape[0])}
                    if ref:
                        d["raw"] = {k: round(float(f[k]), 4) for k in ref if k < f.shape[0]}
                        d["norm"] = {k: round(float(fn[k]), 4) for k in ref if k < f.shape[0]}
                        for kind in ("raw", "norm"):
                            if len(d[kind]) == len(ref):
                                err = max(abs(d[kind][k] - ref[k]) for k in ref)
                                d[f"{kind}_maxerr"] = round(err, 4)
                                if best_match is None or err < best_match[0]:
                                    best_match = (err, spec, fit, kind, s)
                    sims = (fn @ tf.T).tolist()
                    d["concepts"] = {}
                    for i, c in enumerate(PAIRS):
                        p, n = sims[2 * i], sims[2 * i + 1]
                        d["concepts"][c] = {"score": round(100 / (1 + math.exp(-100 * (p - n))), 1), "pos": round(p, 4), "neg": round(n, 4)}
                    out[fit] = d
                res["models"][spec][s] = out
                c = out["crop"]["concepts"]
                lines.append(f"{s[-40:]} | " + " ".join(f"{k} {v['score']:.0f}" for k, v in c.items())
                             + (f" | dims crop norm {out['crop'].get('norm')} squash norm {out['squash'].get('norm')}" if ref else ""))
        del model
    if ref:
        if best_match:
            err, spec, fit, kind, s = best_match
            res["best_match"] = {"max_error": round(err, 4), "model": spec, "fit": fit, "kind": kind, "image": s,
                                 "identified": err < 0.01}
            lines.insert(0, f"REFERENCE MATCH: {'YES' if err < 0.01 else 'no'}: closest {spec} / {fit} / {kind} on {s[-40:]}, max error {err:.4f} (under 0.01 = same model)")
        else:
            lines.insert(0, "REFERENCE MATCH: nothing to compare")
    for e in res["errors"]:
        lines.append("ERROR " + e)
    Path(a.out + ".json").write_text(json.dumps(res, indent=1))
    Path(a.out + ".txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
