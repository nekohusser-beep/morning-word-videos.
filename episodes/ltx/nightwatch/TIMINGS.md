# Night Watch LTX scenes, free Kaggle T4 (Nov 16 2026), $0

LTX-2.3 22B distilled GGUF Q4_K_S, ComfyUI 0.45.0, 480x832, 97 frames, 24 fps (4.0 s), 8 steps, with audio. ComfyUI started with `--reserve-vram 3`.

| scene | total wall | generation only | attempts | GPU peak (sampled every 20 s) | host RAM peak |
|---|---|---|---|---|---|
| s1_night_lake | 746 s | 525.2 s | 1 | 12,617 MiB | 28 GB |
| s2_watchtower | 755 s | 525.2 s | 1 | 12,621 MiB | 29 GB |
| s3_lantern_wall | 756 s | 525.2 s | 1 | 12,589 MiB | 28 GB |
| s4_first_light | 757 s | 525.2 s | 1 | 12,621 MiB | 28 GB |
| s5_sunrise | 755 s | 525.2 s | 1 | 12,589 MiB | 29 GB |

Total wall minus generation (about 230 s) is the per-scene warm-up pass, which is no longer needed with `--reserve-vram 3`.
Without the reserve flag, 3 of 3 fresh-server attempts on s1 died with CUDA out of memory in the sampler (12.45 GiB allocated, 576 MiB requested, 22 MiB free): see ltx_oom_fail_s1_no_reserve_vram.log.
The earlier run (no reserve flag) produced the s2 clip stamped 0850 in 715 s after OOM retries; the s2 stamped 0932 is the rerun, same seed, drifts to dawn colors at the end. Use 0850 for a night shot.
License: LTX-2.x Community License (free under about $10M revenue), not Apache.
