// SKIP #2: ADHD vs a hot cup of coffee. One world: Skip seated at the dining table, cup on the table, clock on the wall.
const SKIP={skin:'#F8E9CC',cloth:'#FF8C1A',hood:'#D96E0A',hand:'#F8E9CC',face:INK,leg:'#2C2A49',shoe:'#17141F',finger:INK,hair:'#1E78E6'};
const SEAT=[760,560],CUP=[905,832],S=1;
const clockT=t=>t+2400*ease(seg(t,9.8,23.3));
const heat=t=>1-ease(seg(t,10,22));
// hand weight toward the cup: quick touch-and-recoil (too hot), then the real grab and sip
const touch=t=>ease(seg(t,5.1,5.6))*(1-ease(seg(t,5.75,6.3)));
const grab=t=>ease(seg(t,21.6,22.2))*(1-ease(seg(t,26.2,26.9)));
const sip=t=>ease(seg(t,22.3,23.0))*(1-ease(seg(t,24.6,25.4)));
const cupAt=t=>{const s=sip(t);return [lerp(CUP[0],SEAT[0]+142,s),lerp(CUP[1],SEAT[1]-8,s)]};
const DEF=[97,220];
function skip(t){const s=sip(t),g=grab(t),tc=touch(t),c=cupAt(t);
 const drift=kf(t,[[0,0],[9.6,0],[10.1,1],[23.4,1],[23.6,0]]);
 const p={x:SEAT[0],y:SEAT[1],s:S,face:1,noLegs:true,breath:t*2.1,
  look:kf(t,[[0,.15],[3.6,.15],[4.0,.7],[9.6,.7],[10.1,-.35],[13.8,-.35],[14.1,.4],[17.4,.4],[17.7,-.2],[21.3,-.2],[21.6,.7],[26.8,.7],[27.2,.1]]),
  lookY:kf(t,[[0,.3],[3.6,.3],[4.0,.6],[9.6,.6],[10.1,-.8],[21.3,-.8],[21.6,.55],[26.8,.55],[27.2,.2]]),
  brow:kf(t,[[0,.2],[5.6,.2],[5.8,.9],[6.6,.4],[17.6,.4],[17.9,.7],[21.2,.5],[23.6,.5],[23.9,-.2],[26.6,-.2],[27,.3]]),
  sad:kf(t,[[0,0],[23.6,0],[23.9,.7],[26.7,.7],[27.1,.25]]),
  mouth:kf(t,[[0,.6],[5.6,.6],[5.8,-.35],[6.6,.4],[17.6,.4],[17.9,.9],[21.2,.65],[23.6,.6],[23.85,-.6],[26.7,-.6],[27.1,.45]]),
  open:kf(t,[[0,0],[5.6,0],[5.75,.5],[6.3,0],[23.6,0],[23.8,.35],[24.6,0]]),
  tilt:kf(t,[[0,.02],[9.6,.02],[10.1,-.1],[21.3,-.1],[21.6,.02]])+lerp(0,-.12,s)+drift*Math.sin(t*1.3)*.03,
  blink:blinkAt(t,[2.2,7.3,12.4,16.1,19.9,25.6,31.2,36.4]),hands:{},tuck:{r:s>.3}};
 const w=Math.max(g,tc);let tgt;
 if(g>0&&s>0)tgt=[(c[0]-12-p.x)/p.s,(c[1]-lerp(52,40,s)-p.y)/p.s];
 else tgt=[(CUP[0]-12-p.x)/p.s,(CUP[1]-52-p.y)/p.s];
 p.hands.r=[lerp(DEF[0],tgt[0],w),lerp(DEF[1],tgt[1],w)];
 if(w<.05)delete p.hands.r;
 return p}
function steam(x,t,a){if(a<.02)return;x.save();x.lineCap='round';x.lineWidth=5;
 for(let i=0;i<3;i++){const ph=t*1.1+i*.33,k=ph%1,bx=CUP[0]-18+i*18,by=CUP[1]-78;
  x.strokeStyle=`rgba(255,244,230,${a*.55*Math.sin(k*Math.PI)})`;x.beginPath();x.moveTo(bx,by-k*20);
  for(let j=1;j<=6;j++){const yy=by-k*20-j*14;x.lineTo(bx+Math.sin(j*.9+t*2+i)*9,yy)}x.stroke()}x.restore()}
function card(x,cx,cy,txt,a,sc=1){if(a<.02)return;x.save();x.globalAlpha=a;x.translate(cx,cy);x.scale(sc,sc);x.font='bold 46px sans-serif';const w=x.measureText(txt).width+64;
 x.fillStyle='rgba(255,248,236,.96)';x.beginPath();x.roundRect(-w/2,-44,w,88,26);x.fill();
 x.beginPath();x.moveTo(-w/2+50,40);x.lineTo(-w/2+20,92);x.lineTo(-w/2+96,40);x.closePath();x.fill();
 x.fillStyle='#2A1F42';x.textAlign='center';x.textBaseline='middle';x.fillText(txt,0,2);x.restore()}
function banner(txt,y,a,bg,fg='#FFFFFF',sz=58){if(a<.02)return;ctx.save();ctx.setTransform(1,0,0,1,0,0);ctx.globalAlpha=a;ctx.font=`bold ${sz}px sans-serif`;const w=ctx.measureText(txt).width+80;
 ctx.fillStyle=bg;ctx.beginPath();ctx.roundRect(W/2-w/2,y-sz*.85,w,sz*1.7,28);ctx.fill();ctx.fillStyle=fg;ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(txt,W/2,y+2);ctx.restore()}
const pop=(t,a,b)=>ease(seg(t,a,a+.25))*(1-ease(seg(t,b-.25,b)));
const SHOTS=[
 u=>({x:960,y:540,z:lerp(1,1.04,ease(u)),b:[1,0,0]}),          // 0 wide: the world
 u=>({x:lerp(840,860,u),y:600,z:lerp(1.55,1.65,ease(u)),b:[3,0,0]}), // 1 medium: too hot
 u=>({x:1540,y:260,z:lerp(2.3,2.45,u),b:[0,0,0]}),             // 2 clock: one minute
 u=>({x:lerp(900,930,u),y:470,z:lerp(1.35,1.42,u),b:[2,0,0]}), // 3 drift: email
 u=>({x:lerp(1040,1080,u),y:430,z:lerp(1.15,1.2,u),b:[2,0,0]}),// 4 drift: oil change, clock racing behind
 u=>({x:lerp(880,900,u),y:470,z:lerp(1.4,1.5,u),b:[2,0,0]}),   // 5 drift: guitar
 u=>({x:850,y:640,z:lerp(1.5,1.6,ease(u)),b:[3,0,0]}),         // 6 coffee time
 u=>({x:820,y:470,z:lerp(2.1,2.3,ease(u)),b:[6,0,0]}),         // 7 cold
 u=>({x:960,y:lerp(560,540,u),z:lerp(1.08,1,ease(u)),b:[2,0,0]}) // 8 why + tip
];
FILM={dur:39.5,cuts:[0,117,237,294,417,525,639,705,807,1185],fadeIn:.5,fadeOut:.8,
 cam(s,u,t){return SHOTS[s](u)},
 draw(t,cam,shot){const ct=clockT(t),sp=sip(t),cw=cupAt(t);
  let x=layer('room',cam);drawRoom(x,false,t,ct);
  const h=layer('hero',cam),sk=skip(t),hp=actor(h,'skip',SKIP,sk,cam);
  const f=layer('tab',cam);drawRoomTable(f,[],[]);saucer(f,CUP[0],CUP[1],1);
  steam(f,t,heat(t)*(1-sp));drawCup(f,cw[0],cw[1],1,lerp(0,-.42,sp));
  if(grab(t)>.95||sp>0){cupGrip(f,cw[0]-10+6*sp,cw[1]-lerp(26,28,sp),lerp(0,-.42,sp),SKIP,1);contact('hand-cup',h2w(hp,'r'),[cw[0]-12,cw[1]-lerp(52,40,sp)])}
  const ui=layer('ui',cam);
  card(ui,1130,300,'That email from Tuesday...',pop(t,10.3,13.9));
  card(ui,1180,280,'Car needs an oil change',pop(t,14.2,17.5));
  card(ui,1140,300,'Learn guitar?!',pop(t,17.8,21.3),1.1);
  comp([['room',cam.b[0]],['hero',0],['tab',cam.b[1]],['ui',0]]);
  banner('ADHD vs. a hot cup of coffee',120,pop(t,.4,3.9),'#E4493F');
  banner('"Just one minute."',940,pop(t,7.9,9.8),'#2A1F42');
  banner('40 minutes later...',120,pop(t,24.0,26.9),'#2A1F42');
  banner('Boring task = brain goes hunting',120,pop(t,27.4,33.0),'#7A56A0');
  banner('Tip: set a timer you can HEAR',120,pop(t,33.2,39.4),'#187E86');
  banner('Tag somebody drinking cold coffee',950,pop(t,36.6,39.4),'#E4493F','#FFFFFF',46)},
 plants(){return {}}};
say(5.55,'hot');say(22.2,'lift');say(23.75,'cold');say(26.5,'cupdown');say(9.9,'whoosh');say(23.4,'whoosh');
for(let k=0;k<6;k++)say(7.95+k*.32,'tick');
