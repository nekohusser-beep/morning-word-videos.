import subprocess, os
STD=[(474,175,110,36),(977,172,122,36)]
BOX={'o3':[(1037,190,118,36),(547,190,50,32)],'c1':[(1147,190,108,36)],'c3':[(1107,180,118,36)]}
for k in ['o1','o2','o3','o4','o5','c1','c2','c3','c4','c5','c6','c7']:
    bx=BOX.get(k,STD); fc=['[0:v]split='+str(len(bx)+1)+''.join(f'[s{i}]' for i in range(len(bx)+1))]
    last='s0'
    for i,(x,y,w,h) in enumerate(bx,1):
        fc.append(f'[s{i}]crop={w}:{h}:{x}:{y},boxblur=8:2:4:1[b{i}]'); fc.append(f'[{last}][b{i}]overlay={x}:{y}[o{i}]'); last=f'o{i}'
    subprocess.check_call(['ffmpeg','-y','-loglevel','error','-i',f'clip_{k}.mp4','-filter_complex',';'.join(fc),'-map',f'[{last}]','-map','0:a','-c:v','libx264','-crf','15','-preset','veryfast','-pix_fmt','yuv420p','-c:a','copy',f'/tmp/cb_{k}.mp4'])
    os.replace(f'/tmp/cb_{k}.mp4',f'clip_{k}.mp4')
print('ok')
