import json,sys,subprocess,os
T=json.load(open(sys.argv[1])); os.makedirs('w',exist_ok=True); y=[]
for t in T:
    v=f"w/{t['id']}.mp4"; a=f"w/{t['id']}.wav"
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t.get('v0',0)),'-i',f"tools/little-amens/clips/{t['clip']}.mp4",'-t',str(t['dur']),'-an','-r','25','-c:v','libx264','-crf','14','-pix_fmt','yuv420p',v],check=True)
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t['a0']),'-t',str(t['dur']),'-i','tools/little-amens/audio/vocals.mp3','-ar','16000','-ac','1',a],check=True)
    y.append(f"{t['id']}:\n  video_path: \"{os.path.abspath(v)}\"\n  audio_path: \"{os.path.abspath(a)}\"\n"+(f"  bbox_shift: {t['bbox_shift']}\n" if 'bbox_shift' in t else ''))
open('w/cfg.yaml','w').write(''.join(y)); print(open('w/cfg.yaml').read())
