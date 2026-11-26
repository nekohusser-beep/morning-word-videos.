import json, subprocess
C='clips/'
S={'S01':'6528b7b7','S02':'fb8fc3e8','S18':'f97802e1','S04':'72054133','S05':'8385ee1b','S06':'70130aa5','S07':'aa1352ad','S08':'788f2709','S09':'62d23e84','S10':'1d4187f2','S11':'dc76c6b1','S12':'a8d963cc','S13':'8e4f6e74','S14':'da6c446a','S15':'46332197','S16':'bcfdc94d','S19':'0a15ec1e','S17':'54d6460d','JS':'jesus_solo','JD':'jesus_duet'}
# (shot, start_in_song, end_in_song, offset_in_clip)
E=[('S15',0,5,0),('S12',5,10,0),('S02',10,18,0),('S19',18,26,0),('S05',26,34,0),('S12',34,35.5,3),
('S04',35.5,42,0),('S01',42,48,0),('S18',48,53.5,0),('S02',53.5,57,4),('S19',57,62,0),('S12',62,66.3,0),
('S17',66.3,70.8,0),('S06',70.8,74,0),('S07',74,81.9,0),('S08',81.9,89.8,0),('S12',89.8,91.3,5),
('S09',91.3,94.5,0),('S10',94.5,98.8,0),('S11',98.8,103.8,0),('S15',103.8,111.7,0),('S08',111.7,119.6,0),
('S13',119.6,124.5,0),('JS',124.5,132.4,0),('JD',132.4,140.3,0),('S07',140.3,148.2,0),('S15',148.2,156.1,0),
('S17',156.1,160,3),('S16',160,167.9,0),('S12',167.9,173,0),('S01',173,180,0)]
# check continuity
t=0
for s,a,b,o in E:
    assert abs(a-t)<1e-6,(s,a,t); assert b-a+o<=8.1,(s,a,b,o); t=b
assert t==180
ins=[];fc=[]
for i,(s,a,b,o) in enumerate(E):
    ins+=['-ss',str(o),'-t',f'{b-a:.3f}','-i',C+S[s]+'.mp4']
    fc.append(f'[{i}:v]fps=30,scale=1408:792,crop=1280:720:64:0,setsar=1,tpad=stop_mode=clone:stop_duration=0.4,trim=duration={b-a:.3f},setpts=PTS-STARTPTS[v{i}]')
fc.append(''.join(f'[v{i}]' for i in range(len(E)))+f'concat=n={len(E)}:v=1:a=0[cat]')
fc.append('[cat]ass=lyrics.ass,fade=t=in:st=0:d=0.8,fade=t=out:st=178:d=2[vo]')
cmd=['ffmpeg','-y','-v','error']+ins+['-i','song1.mp3','-filter_complex',';'.join(fc),'-map','[vo]','-map',f'{len(E)}:a','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-af','loudnorm=I=-14:TP=-1.5:LRA=11','-t','180','-movflags','+faststart','little-amens-ep1-pilot-v2.mp4']
subprocess.run(cmd,check=True)
