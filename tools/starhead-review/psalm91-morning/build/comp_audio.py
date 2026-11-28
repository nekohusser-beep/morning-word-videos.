# Psalm 91 composite audio: Neko voice opening + prayer close around the (unchanged) narrated master.
# Opening/closing use the SAME chain the master used (voice: highpass 70 / compressor / +3 dB; pad: lowpass 2600 / echo / -19 dB;
# amix; loudnorm I=-14 TP=-1.5 LRA=11) so the speech level, the pad ebb and flow and the end fade match the middle.
# Middle = master_audio.wav [SEAM1, SEAM2] sample-rate-warped by 0.015 % so it lands exactly on the 30 fps frame grid of chunks 1-6.
import subprocess, json, sys, re, numpy as np, soundfile as sf
sys.path.insert(0, '/home/claude/ps91/build'); sys.path.insert(0, '/home/claude/ps91/mix')
import comp_plan as C
import pad as PAD

SR = 48000; W = '/home/claude/ps91'; M = W + '/mix'; B = W + '/build'
XF = 0.06                     # seam crossfade (s)
PAD_DIV = 8.08206844          # original pad normalisation divisor
FPS = 30.0

def sh(c):
    subprocess.run(c, shell=True, check=True)

def nframes(f):
    o = subprocess.check_output(f"ffprobe -v error -select_streams v:0 -count_packets -show_entries stream=nb_read_packets -of csv=p=0 {f}", shell=True).decode().strip()
    return int(o)

def measure(path, args=''):
    r = subprocess.run(f"ffmpeg -hide_banner -nostats {args} -i {path} -af ebur128=peak=true -f null - 2>&1", shell=True, capture_output=True, text=True).stdout
    I = re.findall(r'\n\s+I:\s+(-?[\d.]+) LUFS', r); P = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r)
    return (float(I[-1]) if I else None, float(P[-1]) if P else None)

def rd(p):
    x, sr = sf.read(p, dtype='float32', always_2d=True); assert sr == SR, (p, sr); return x

# ---- exact lengths from the rendered video pieces
F_OPEN = nframes(B + '/comp_open.mp4'); F_CLOSE = nframes(B + '/comp_close.mp4')
F_MID = sum(nframes(f'{B}/chunk{i}.mp4') for i in range(1, 7))
T_OPEN, T_MID, T_CLOSE = F_OPEN / FPS, F_MID / FPS, F_CLOSE / FPS
TOTAL = T_OPEN + T_MID + T_CLOSE
MID_SRC = C.SEAM2 - C.SEAM1            # 370.788 s of master
WARP = MID_SRC / T_MID                 # >1 : master is played this much faster
print('frames', F_OPEN, F_MID, F_CLOSE, 'T', round(T_OPEN, 4), round(T_MID, 4), round(T_CLOSE, 4), 'TOTAL', round(TOTAL, 4), 'warp', round(WARP, 7), flush=True)

VOICE_CHAIN = 'highpass=f=70,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120,volume=3dB,aformat=channel_layouts=stereo'
PAD_CHAIN = 'lowpass=f=2600,aecho=0.8:0.7:90|180|330:0.35|0.25|0.18,aformat=channel_layouts=stereo,volume=-19dB'

def build_part(name, voice_wav, pad_in, pad_ss, pad_len, pad_rate, length, voice_gain_db):
    """voice_wav (48k mono) + pad slice -> chain -> amix -> loudnorm -> mix/<name>_ln.wav (48k stereo, `length` s)."""
    # pad slice, warped onto the video timeline with asetrate (pure sample-rate change, no pitch artefacts at this size)
    sr_in = sf.info(pad_in).samplerate
    sh(f'ffmpeg -y -hide_banner -loglevel error -ss {pad_ss:.4f} -t {pad_len:.4f} -i {pad_in} -af "asetrate={sr_in*pad_rate:.3f},aresample={SR}" -ac 1 {M}/{name}_pad.wav')
    sh(f'ffmpeg -y -hide_banner -loglevel error -i {voice_wav} -i {M}/{name}_pad.wav -filter_complex '
       f'"[0:a]volume={voice_gain_db:.3f}dB,{VOICE_CHAIN}[v];[1:a]{PAD_CHAIN}[m];[v][m]amix=inputs=2:normalize=0:duration=longest,loudnorm=I=-14:TP=-1.5:LRA=11,atrim=duration={length:.4f}[a]" '
       f'-map "[a]" -ar {SR} -ac 2 {M}/{name}_ln.wav')
    return rd(f'{M}/{name}_ln.wav')

def main(voice_gain_db=0.0):
    # voice tracks (pre-chain), built by comp_voice.py
    sh(f'python3 {B}/comp_voice.py > {M}/voice_build.log')
    # pad for the closing (new total, same normalisation / seeds as the master pad)
    pad_total = C.SEAM2 + T_CLOSE
    PAD.make(pad_total, PAD_DIV, M + '/pad_new.wav')
    # OPENING: pad time = video time * (SEAM1/T_OPEN) so the pad runs straight into the master's pad
    r_open = C.SEAM1 / T_OPEN
    op = build_part('open', M + '/voice_open.wav', M + '/pad_orig.wav', 0.0, C.SEAM1 + 0.15, r_open, T_OPEN + XF + 0.05, voice_gain_db)
    # CLOSING: pad time continues from the master's SEAM2 at real-time rate
    cl = build_part('close', M + '/voice_close.wav', M + '/pad_new.wav', C.SEAM2, T_CLOSE + 0.1, 1.0, T_CLOSE + 0.05, voice_gain_db)
    # MIDDLE: master slice, warped to T_MID (+XF extension at the end for the closing crossfade)
    sh(f'ffmpeg -y -hide_banner -loglevel error -ss {C.SEAM1:.4f} -t {MID_SRC + XF * WARP + 0.02:.4f} -i {W}/master_audio.wav -af "asetrate={SR*WARP:.3f},aresample={SR}" -ac 2 {M}/mid.wav')
    mid = rd(M + '/mid.wav')
    n = int(round(TOTAL * SR)); out = np.zeros((n, 2), np.float32)
    i0 = int(round(T_OPEN * SR)); i1 = int(round((T_OPEN + T_MID) * SR)); xf = int(XF * SR)
    ramp = np.linspace(0, 1, xf, dtype=np.float32)[:, None]
    # opening (0 .. T_OPEN + XF)
    out[:i0 + xf] += op[:i0 + xf] * np.concatenate([np.ones((i0, 1), np.float32), 1 - ramp])
    # middle (T_OPEN .. T_OPEN+T_MID+XF), faded in over XF at the front, out over XF at the back
    mm = mid[:(i1 - i0) + xf].copy(); mm[:xf] *= ramp; mm[-xf:] *= (1 - ramp)
    out[i0:i0 + len(mm)] += mm
    # closing (T_OPEN+T_MID .. end), faded in over XF at the front
    cc = cl[:n - i1].copy(); cc[:xf] *= ramp
    out[i1:i1 + len(cc)] += cc
    sf.write(M + '/final_pre.wav', out, SR, subtype='FLOAT')
    print('pre written', out.shape, flush=True)

if __name__ == '__main__':
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 0.0)
