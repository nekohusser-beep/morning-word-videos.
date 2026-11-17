#!/usr/bin/env python3
"""recut.py - re-cut an old finished Derrick master into a new finished file.
strip old jingle bookends -> trim to speech -> fade -> 720x1280/30fps -> two-pass loudnorm (-14 LUFS, TP -1.5)
-> add current song bumpers (tools/stitch/add_bumpers.sh). No generation, no credits."""
import subprocess, json, sys, os
REPO=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root; sources must be checked out
JOBS = {
 # tag: (source, start, end, fade_out_len)
 'day1':     ('day1/morning-word-day1.mp4',                       5.90, 138.75, 0.30),
 'day2':     ('day2/morning-word-day2-v4.mp4',                    5.68, 110.85, 0.25),
 'day3':     ('day3/morning-word-day3-v2.mp4',                    6.98,  74.98, 0.12),
 'ps118':    ('week2/day1/morning-word-psalm-118-24.mp4',         5.92,  96.32, 0.18),
 'pet57':    ('week2/day4/morning-word-1-peter-5-7.mp4',          5.92,  96.85, 0.30),
 'surrender':('shorts/derrick/surrender-romans-12-1.mp4',         12.45, 103.00, 0.25),
}
TP=os.environ.get('TP','-1.5')
def run(cmd):
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode: print(r.stderr); sys.exit(1)
    return r.stderr+r.stdout
def main(tags):
    W=os.environ.get('WORK','recut-work'); os.makedirs(W+'/mid',exist_ok=True); os.makedirs(W+'/out',exist_ok=True)
    for t in tags:
        src,ss,ee,fd=JOBS[t]; p=f'{REPO}/{src}'; d=ee-ss
        vf=("fps=30,scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,setsar=1,"
            f"fade=t=out:st={d-0.12:.3f}:d=0.12")
        # pass 1 measure
        af=f"afade=t=in:st=0:d=0.012,afade=t=out:st={d-fd:.3f}:d={fd},aresample=48000"
        m=run(['ffmpeg','-hide_banner','-ss',f'{ss}','-t',f'{d:.3f}','-i',p,'-vn','-af',af+f',loudnorm=I=-14:TP={TP}:LRA=11:print_format=json','-f','null','-'])
        j=json.loads(m[m.rindex('{'):m.rindex('}')+1])
        ln=(f"loudnorm=I=-14:TP={TP}:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
            f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
        out=os.environ.get('WORK','recut-work')+f'/mid/{t}.mp4'
        run(['ffmpeg','-hide_banner','-v','error','-y','-ss',f'{ss}','-t',f'{d:.3f}','-i',p,'-vf',vf,
             '-af',af+','+ln+',aresample=48000','-c:v','libx264','-crf','20','-preset','veryfast','-pix_fmt','yuv420p',
             '-c:a','aac','-b:a','192k','-ar','48000',out])
        fin=os.environ.get('WORK','recut-work')+f'/out/{t}.mp4'
        run(['bash',f'{REPO}/tools/stitch/add_bumpers.sh',out,fin])
        print(t,'ok',os.path.getsize(fin))
if __name__=='__main__': main(sys.argv[1:] or list(JOBS))
