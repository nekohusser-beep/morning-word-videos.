# Heaven/Hell thumbnail v2: bg.png + overlay.png (face is composited in the browser from Pexels 18861022)
import random, math
from PIL import Image, ImageDraw, ImageFilter, ImageFont
W,H=1280,720
src=Image.open('long-thumbs/Heaven-Without-God-Would-You-Still-Go.jpg').convert('RGB')
bg=Image.new('RGB',(W,H),(0,0,0))
# heaven panel: throne + clouds from the old thumb (right part), placed left
# heavenly sky behind the headline
sky=Image.new('RGB',(W,H)); sp=sky.load()
for y in range(H):
    for x in range(W):
        t=y/H; sp[x,y]=(int(250-60*t),int(225-70*t),int(170-60*t))
bg.paste(sky)
crop=src.crop((830,40,1280,720)).resize((600,907))
fade=Image.new('L',crop.size,255); fd=fade.load()
cw=crop.size[0]
for y in range(crop.size[1]):
    for x in range(cw):
        a=min(1,y/90) * min(1,(cw-x)/140)
        fd[x,y]=int(255*a)
bg.paste(crop,(0,250),fade)
# hell panel: right side, black -> deep red from bottom, embers
hell=Image.new('RGB',(W,H))
px=hell.load()
for y in range(H):
    for x in range(W):
        t=max(0,(y-180)/540)          # redder toward bottom
        r=int(25+200*t**1.3); g=int(4+40*t**2.2); b=int(4+6*t)
        px[x,y]=(r,g,b)
d=ImageDraw.Draw(hell)
random.seed(7)
for _ in range(260):
    x=random.randint(560,W); y=random.randint(260,H); s=random.choice([1,2,2,3,4])
    c=random.choice([(255,170,40),(255,120,20),(255,220,120)])
    d.ellipse((x,y,x+s,y+s),fill=c)
hell=hell.filter(ImageFilter.GaussianBlur(0.6))
# gold heaven glow at top-right (where he looks)
glow=Image.new('L',(W,H),0); gd=ImageDraw.Draw(glow)
for r in range(420,0,-6): gd.ellipse((980-r,-260-r//2,980+r,-260+r+r//2),fill=int(255*(1-r/420)**1.6))
gold=Image.new('RGB',(W,H),(255,214,120))
hell=Image.composite(gold,hell,glow.filter(ImageFilter.GaussianBlur(30)))
# soft seam: heaven left, hell right
mask=Image.new('L',(W,H)); md=mask.load()
for x in range(W):
    v=0 if x<520 else (255 if x>700 else int(255*(x-520)/180))
    for y in range(H): md[x,y]=v
bg=Image.composite(hell,bg,mask)
bg.save('long-thumbs/hh-v2/bg.png')

# overlay: text + arrow, transparent
ov=Image.new('RGBA',(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov)
F='/usr/share/fonts/opentype/inter/Inter-Black.otf'
def txt(xy,s,size,fill):
    f=ImageFont.truetype(F,size)
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).text((xy[0]+6,xy[1]+8),s,font=f,fill=(0,0,0,220),stroke_width=14,stroke_fill=(0,0,0,220))
    ov.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    od.text(xy,s,font=f,fill=fill,stroke_width=12,stroke_fill=(0,0,0))
txt((30,6),'HEAVEN',170,(255,255,255))
txt((34,180),'WITHOUT GOD?',112,(255,214,0))
# red arrow from text toward the empty throne
pts=[(600,330),(590,420),(520,470)]
od.line(pts,fill=(0,0,0),width=34,joint='curve'); od.line(pts,fill=(235,20,20),width=22,joint='curve')
ax,ay=500,482; ang=math.atan2(470-420,520-590)
head=[(ax+40*math.cos(ang),ay+40*math.sin(ang)),(ax+40*math.cos(ang+2.3),ay+40*math.sin(ang+2.3)),(ax+40*math.cos(ang-2.3),ay+40*math.sin(ang-2.3))]
od.polygon(head,fill=(235,20,20),outline=(0,0,0),width=6)
ov.save('long-thumbs/hh-v2/overlay.png')
# preview with placeholder face
pv=bg.convert('RGBA'); pd=ImageDraw.Draw(pv); pd.ellipse((800,150,1180,720),fill=(120,110,105,255))
pv.alpha_composite(ov); pv.convert('RGB').save('/tmp/claude-0/-home-claude-morning-word-videos-/cfa673cd-bacf-5bb0-8ae5-779dfe0395ad/scratchpad/preview.jpg',quality=88)
