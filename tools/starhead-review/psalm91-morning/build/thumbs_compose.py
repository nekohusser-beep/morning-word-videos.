#!/usr/bin/env python3
"""Thanksgiving long thumbnails from the video's own free stock frames (Pexels). 4 words or fewer."""
import subprocess, sys
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
FONT="/usr/share/fonts/truetype/google-fonts/ofl/anton/Anton-Regular.ttf"
W,H=1280,720; YEL=(255,200,40); WHITE=(255,255,255)
def frame(clip,t):
    subprocess.check_call(['ffmpeg','-y','-loglevel','error','-ss',str(t),'-i',f'/home/claude/lib/{clip}.mp4','-frames:v','1','/tmp/th_f.png'])
    return Image.open('/tmp/th_f.png').convert('RGB').resize((W,H),Image.LANCZOS)
def punch(im,c=1.15,s=1.3,b=0.95):
    return ImageEnhance.Brightness(ImageEnhance.Color(ImageEnhance.Contrast(im).enhance(c)).enhance(s)).enhance(b)
def shade(im,side):
    ov=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov)
    for x in range(W):
        a=int(170*max(0,1-(x/(W*0.62)))) if side=='left' else int(170*max(0,1-((W-x)/(W*0.62))))
        d.line([(x,0),(x,H)],fill=(0,0,0,a))
    return Image.alpha_composite(im.convert('RGBA'),ov)
def text(im,xy,s,size,fill):
    f=ImageFont.truetype(FONT,size); st=max(6,size//14)
    sh=Image.new('RGBA',im.size,(0,0,0,0)); ImageDraw.Draw(sh).text((xy[0]+size//18,xy[1]+size//14),s,font=f,fill=(0,0,0,210),stroke_width=st,stroke_fill=(0,0,0,210))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(size//16)))
    ImageDraw.Draw(im).text(xy,s,font=f,fill=fill,stroke_width=st,stroke_fill=(0,0,0))
def make(out,clip,t,lines,side='left'):
    im=shade(punch(frame(clip,t)),side)
    x=60 if side=='left' else W-60
    y=140
    for s,col,size in lines:
        f=ImageFont.truetype(FONT,size); bb=ImageDraw.Draw(im).textbbox((0,0),s,font=f)
        xx=x if side=='left' else x-(bb[2]-bb[0])
        text(im,(xx,y),s,size,col); y+=int(size*1.12)
def make(out,clip,t,lines,side='left',circle=None,y0=140):
    im=shade(punch(frame(clip,t)),side)
    if circle:
        cx,cy,rx,ry=circle; d=ImageDraw.Draw(im)
        for k in range(14): d.ellipse([cx-rx-k,cy-ry-k,cx+rx+k,cy+ry+k],outline=(235,30,30,255))
    x=60 if side=='left' else W-60
    y=y0
    for s,col,size in lines:
        f=ImageFont.truetype(FONT,size); bb=ImageDraw.Draw(im).textbbox((0,0),s,font=f)
        xx=x if side=='left' else x-(bb[2]-bb[0])
        text(im,(xx,y),s,size,col); y+=int(size*1.12)
    im.convert('RGB').save(out,quality=92)
make('thumb-A-dont-leave-yet.jpg',3371852,2.0,[("DON'T LEAVE",WHITE,170),('YET',YEL,210)],'right',circle=(480,520,180,150))
make('thumb-B-pray-this-first.jpg',5495831,8.0,[('PRAY THIS',WHITE,170),('FIRST',YEL,210)],'left')
make('thumb-C-psalm-91-before-work.jpg',4288032,3.0,[('PSALM 91',YEL,210),('BEFORE WORK',WHITE,140)],'left')
