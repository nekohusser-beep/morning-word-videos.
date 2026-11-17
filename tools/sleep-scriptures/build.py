import json, wave, random, math, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H=1080,1920
L=json.load(open('lines.json'))
SER='/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'; POP='/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
def dur(i):
    with wave.open(f'a{i:02d}.wav') as w: return w.getnframes()/w.getframerate()
D=[dur(i) for i in range(len(L))]; T=sum(D)
# background: night sky, oversized for slow zoom
BW,BH=1296,2304
bg=Image.new('RGB',(BW,BH)); d=ImageDraw.Draw(bg)
for y in range(BH):
    t=y/BH; d.line([(0,y),(BW,y)],fill=(int(6+14*t),int(10+18*t),int(28+36*t)))
glow=Image.new('RGBA',(BW,BH),(0,0,0,0)); g=ImageDraw.Draw(glow)
mx,my=BW*0.72,BH*0.2
for r in range(380,0,-8): g.ellipse([mx-r,my-r,mx+r,my+r],fill=(180,200,255,int(3+60*(1-r/380)**3)))
g.ellipse([mx-70,my-70,mx+70,my+70],fill=(245,240,220,255))
glow=glow.filter(ImageFilter.GaussianBlur(6)); bg=Image.alpha_composite(bg.convert('RGBA'),glow)
random.seed(3); s=ImageDraw.Draw(bg)
for _ in range(420):
    x,y=random.random()*BW,random.random()*BH*0.85; r=random.choice([1,1,1.5,2,2.5]); a=random.randint(90,255)
    s.ellipse([x-r,y-r,x+r,y+r],fill=(255,255,255,a))
hill=Image.new('RGBA',(BW,BH),(0,0,0,0)); h=ImageDraw.Draw(hill)
h.polygon([(0,BH)]+[(x,BH*0.86-60*math.sin(x/260)-30*math.sin(x/97)) for x in range(0,BW+1,8)]+[(BW,BH)],fill=(4,6,14,255))
bg=Image.alpha_composite(bg,hill).convert('RGB'); bg.save('bg.png')
def wrap(d,text,font,maxw):
    out,cur=[],''
    for w_ in text.split():
        t=(cur+' '+w_).strip()
        if d.textlength(t,font=font)<=maxw: cur=t
        else: out.append(cur); cur=w_
    out.append(cur); return out
for i,l in enumerate(L):
    im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im); big=l['big']
    size=100 if len(big)<40 else 76 if len(big)<80 else 66
    f=ImageFont.truetype(SER,size); lines=wrap(d,big,f,920); lh=size+30
    y0=880-len(lines)*lh//2
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); sd=ImageDraw.Draw(sh)
    for j,ln in enumerate(lines): sd.text((W/2,y0+j*lh),ln,font=f,fill=(0,0,0,220),anchor='mt')
    im=Image.alpha_composite(im,sh.filter(ImageFilter.GaussianBlur(14))); d=ImageDraw.Draw(im)
    for j,ln in enumerate(lines): d.text((W/2,y0+j*lh),ln,font=f,fill=(255,255,255,255),anchor='mt')
    y=y0+len(lines)*lh+34
    if l['small']:
        fs=ImageFont.truetype(POP,56)
        for ln in wrap(d,l['small'],fs,880): d.text((W/2,y),ln,font=fs,fill=(255,214,120,255),anchor='mt',stroke_width=3,stroke_fill=(0,0,0,160)); y+=76
    d.text((W/2,230),'BLESSED PRAYERS',font=ImageFont.truetype(POP,40),fill=(255,255,255,190),anchor='mm')
    im.save(f'card{i}.png')
open('a.txt','w').write(''.join(f"file 'a{i:02d}.wav'\n" for i in range(len(L))))
subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i','a.txt','-c:a','pcm_s16le','voice.wav'],check=True)
inp=['-loop','1','-t',f'{T:.3f}','-i','bg.png']
for i in range(len(L)): inp+=['-loop','1','-t',f'{T:.3f}','-i',f'card{i}.png']
inp+=['-i','voice.wav']
fc=f"[0:v]fps=30,zoompan=z='1+0.00012*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps=30,trim=duration={T:.3f}[b0];"
st=0; prev='b0'
for i,dd in enumerate(D):
    e=st+dd
    fc+=f"[{i+1}:v]format=rgba,fade=in:st={st:.2f}:d=0.5:alpha=1,fade=out:st={e-0.4:.2f}:d=0.4:alpha=1[c{i}];[{prev}][c{i}]overlay=0:0:enable='between(t,{st:.2f},{e:.2f})'[b{i+1}];"
    prev=f'b{i+1}'; st=e
fc+=f"[{prev}]fade=in:st=0:d=0.4,format=yuv420p[v]"
subprocess.run(['ffmpeg','-y','-loglevel','error']+inp+['-filter_complex',fc,'-map','[v]','-map',f'{len(L)+1}:a','-c:v','libx264','-preset','veryfast','-crf','20','-r','30','-c:a','aac','-b:a','192k','-shortest','sleep-scriptures.mp4'],check=True)
print('total',round(T,2))
