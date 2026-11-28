import subprocess, os
BOX={'c1':[(1085,165,175,55),(722,182,60,32)]}
for k,bx in BOX.items():
    fc=['[0:v]split='+str(len(bx)+1)+''.join(f'[s{i}]' for i in range(len(bx)+1))]; last='s0'
    for i,(x,y,w,h) in enumerate(bx,1):
        fc.append(f'[s{i}]crop={w}:{h}:{x}:{y},boxblur=9:3:4:1[b{i}]'); fc.append(f'[{last}][b{i}]overlay={x}:{y}[o{i}]'); last=f'o{i}'
    subprocess.check_call(['ffmpeg','-y','-loglevel','error','-i',f'clip_{k}.mp4','-filter_complex',';'.join(fc),'-map',f'[{last}]','-map','0:a','-c:v','libx264','-crf','15','-preset','veryfast','-pix_fmt','yuv420p','-c:a','copy',f'/tmp/cb_{k}.mp4'])
    os.replace(f'/tmp/cb_{k}.mp4',f'clip_{k}.mp4')
print('ok')
