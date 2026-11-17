# ComfyUI + Wan 2.2 5B on the free Kaggle T4 (Nov 15 2026)

Ran headless (no UI, no tunnel, no custom nodes), cost $0.
Setup per session about 3 minutes, then about 5 to 6 minutes per 3-second clip (73 frames, 24 fps, 480x832).
fp16 on the T4: no NaN, no black frames, no out-of-memory.

| Clip | Mean frame diff | Verdict |
|---|---|---|
| Big Skip cartoon | 7.83 (max 29.84) | On-model, background steady; pointing hand turns to a fist and the bag lifts into his face by the end |
| Derrick photo | 4.06 (max 11.03) | Same person all the way through, small head tilt and smile, no melting; no lip sync (no audio input) |

Rerun: new Kaggle notebook, Accelerator GPU, Internet on, one cell:
`!curl -sL https://raw.githubusercontent.com/nekohusser-beep/morning-word-videos./<SHA>/tests/kaggle-comfyui/run_test.sh -o /tmp/rt.sh && SHA=<SHA> bash /tmp/rt.sh`
