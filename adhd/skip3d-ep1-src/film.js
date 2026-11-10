// SKIP EP1 (3D): "ADHD vs Getting Up Off the Couch". 62 s. Apartment <-> Brain HQ.
import * as T from 'three';
import {clamp,lerp,ease,seg,kf,V,mesh,mat,Person,makeRenderer,makePost,SKIP,FOCUS,DOPA,PANIC,ANK} from './lib3d.js';
import {blob,walk3} from './world3d.js';
const FPS=30,DUR_=62;
const CUTS=[0,150,225,405,555,660,810,936,1092,1200,1356,1440,1710,1860];
const HQ=new Set([2,4,6,8]);
const R=makeRenderer(),post=makePost(R),sc=new T.Scene(),cam=new T.PerspectiveCamera(35,16/9,.05,80);
sc.background=new T.Color('#2a1b3d');sc.add(cam);
const box=(w,h,d,c,x,y,z,o)=>{const m=mesh(new T.BoxGeometry(w,h,d),mat(c,o));m.position.set(x,y,z);sc.add(m);return m};
const bbox=(w,h,d,c,x,y,z)=>{const m=new T.Mesh(new T.BoxGeometry(w,h,d),new T.MeshBasicMaterial({color:c}));m.position.set(x,y,z);sc.add(m);return m};
const flat={form:0};
const canvasTex=(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;const t=new T.CanvasTexture(c);t.colorSpace=T.NoColorSpace;t.anisotropy=8;return {c,x:c.getContext('2d'),t,key:''}};
function drawCard(ct,key,bg,lines,opt={}){if(ct.key===key)return;ct.key=key;const {x,c}=ct;x.fillStyle=bg;x.fillRect(0,0,c.width,c.height);
 if(opt.frame){x.strokeStyle=opt.frame;x.lineWidth=c.width*.02;x.strokeRect(c.width*.03,c.height*.05,c.width*.94,c.height*.9)}
 if(opt.batt!=null){const bw=c.width*.5,bh=c.height*.32,bx=(c.width-bw)/2,by=c.height*.5;x.strokeStyle='#fff';x.lineWidth=c.width*.015;x.strokeRect(bx,by,bw,bh);x.fillStyle='#fff';x.fillRect(bx+bw,by+bh*.3,bw*.06,bh*.4);x.fillStyle=opt.batt<.12?'#FF3B3B':'#7CFFB2';x.fillRect(bx+6,by+6,Math.max(4,(bw-12)*opt.batt),bh-12)}
 x.textAlign='center';x.textBaseline='middle';for(const L of lines){x.fillStyle=L.c||'#fff';x.font=`bold ${Math.round(c.height*L.s)}px DejaVu Sans, Arial`;x.fillText(L.t,c.width/2,c.height*L.y)}ct.t.needsUpdate=true}

// ================= APARTMENT =================
const fl=new T.Mesh(new T.PlaneGeometry(16,12),mat('#B9774F',flat));fl.rotation.x=-Math.PI/2;fl.position.set(0,0,1);sc.add(fl);
for(let i=-7;i<=7;i++)box(.012,.002,12,'#9C5F3D',i*.55,.001,1,flat);
const rug=new T.Mesh(new T.CircleGeometry(1.2,40),mat('#2DB2AE',flat));rug.rotation.x=-Math.PI/2;rug.position.set(-1.1,.004,-1.2);rug.scale.set(1.5,1,1);sc.add(rug);
box(14,3.2,.1,'#FFD9A8',0,1.6,-3.05,flat);box(14,.9,.12,'#F2A65A',0,.45,-2.98,flat);box(14,.05,.14,'#FFF1DC',0,.92,-2.97,flat);
box(.1,3.2,10,'#FFC98E',-4.5,1.6,2,flat);
box(.7,.5,.04,'#2DB2AE',-1.9,2.05,-2.98,flat);box(.6,.6,.04,'#F6B73C',-1.0,2.15,-2.98,flat);box(.5,.4,.04,'#7A56A0',-.2,2.05,-2.98,flat);
const win=bbox(1.4,1.0,.04,'#9FD8F0',2.6,2.0,-2.98);box(1.4,.05,.06,'#FFF1DC',2.6,2.0,-2.96,flat);box(.05,1.0,.06,'#FFF1DC',2.6,2.0,-2.96,flat);
box(.3,.35,.3,'#E4493F',3.6,.175,-2.6);const pl=mesh(new T.SphereGeometry(.32,14,10),mat('#3FA34D'));pl.position.set(3.6,.62,-2.6);sc.add(pl);
// couch (facing +z)
const CX=-1.2,CZ=-2.45;
box(2.2,.3,.85,'#3A5C9A',CX,.15,CZ);box(2.2,.62,.22,'#2F4C82',CX,.55,CZ-.34);for(const s of [-1,1])box(.22,.46,.85,'#2F4C82',CX+s*1.0,.23,CZ);
box(.95,.13,.7,'#4C6FB5',CX-.5,.36,CZ+.04);box(.95,.13,.7,'#4C6FB5',CX+.5,.36,CZ+.04);
const pil=mesh(new T.BoxGeometry(.38,.34,.12),mat('#F6B73C'));pil.position.set(CX-.75,.6,CZ-.1);pil.rotation.set(-.2,.3,.15);sc.add(pil);
// outlet + charger + cord on floor ending short of the couch
const OX=1.45;box(.12,.18,.02,'#FFF1DC',OX,.38,-2.97,flat);box(.06,.07,.05,'#F2F2F2',OX,.4,-2.93);
const CORD_END=[-.13,.012,-1.74];
const cordPts=[V(OX,.4,-2.9),V(OX,.06,-2.88),V(OX-.3,.012,-2.7),V(.8,.012,-2.3),V(.35,.012,-1.95),V(...CORD_END)];
const cord=new T.Mesh(new T.TubeGeometry(new T.CatmullRomCurve3(cordPts),40,.012,6,false),mat('#F2F2F2'));sc.add(cord);
const plug=mesh(new T.BoxGeometry(.04,.025,.08),mat('#F2F2F2'));plug.position.set(CORD_END[0]-.02,.02,CORD_END[2]);plug.rotation.y=-.3;sc.add(plug);
// phone (box + screen)
const phT=canvasTex(240,420);const phone=new T.Group();sc.add(phone);
const phB=mesh(new T.BoxGeometry(.075,.14,.012),mat('#17141F'));phone.add(phB);
const phS=new T.Mesh(new T.PlaneGeometry(.066,.128),new T.MeshBasicMaterial({map:phT.t}));phS.position.z=.0065;phone.add(phS);
// short cord from outlet to phone for the ending
const shortCord=new T.Mesh(new T.TubeGeometry(new T.CatmullRomCurve3([V(OX,.4,-2.9),V(OX,.3,-2.7)]),6,.012,6,false),mat('#F2F2F2'));sc.add(shortCord);
const skip=new Person(sc,SKIP);const sSh=blob(sc,1,.5);

// ================= BRAIN HQ at x=40 =================
const O=40,cx=x=>O+x;
const crFloor=new T.Mesh(new T.PlaneGeometry(12,10),new T.MeshBasicMaterial({color:'#2B2F55'}));crFloor.rotation.x=-Math.PI/2;crFloor.position.set(O,0,1);sc.add(crFloor);
for(let i=-5;i<=5;i++)bbox(.02,.003,10,'#3A3F6E',cx(i*.6),.002,1);
const crWalls=[bbox(12,4,.1,'#1F2348',O,2,-3.05),bbox(.1,4,10,'#262A52',O-5,2,1),bbox(.1,4,10,'#262A52',O+5,2,1)];const wallBase=['#1F2348','#262A52','#262A52'];
for(let i=0;i<9;i++){const b=new T.Mesh(new T.TorusGeometry(.35,.06,8,20,Math.PI*1.3),new T.MeshBasicMaterial({color:'#FF7FB8'}));b.position.set(cx(-4.4+i*1.1),3.55,-3.0);b.rotation.z=i*.7;sc.add(b)}
const scrT=canvasTex(1024,576);const scr=new T.Mesh(new T.PlaneGeometry(3.6,2.02),new T.MeshBasicMaterial({map:scrT.t}));scr.position.set(O,1.95,-2.93);sc.add(scr);bbox(3.8,2.2,.06,'#0d0b14',O,1.95,-3.0);
const sgT=canvasTex(512,96);drawCard(sgT,'s','#FF4FB8',[{t:'BRAIN HQ',y:.52,s:.62,c:'#1F2348'}]);const sg=new T.Mesh(new T.PlaneGeometry(1.6,.3),new T.MeshBasicMaterial({map:sgT.t}));sg.position.set(O,3.15,-2.88);sc.add(sg);
box(3.4,.9,.55,'#3A2F55',O,.45,-1.45);box(3.5,.06,.7,'#5C3F80',O,.92,-1.42);
const btnC=['#2DB2AE','#F6B73C','#7A56A0','#2DB2AE','#F6B73C'];for(let i=0;i<5;i++){const b=mesh(new T.CylinderGeometry(.04,.04,.03,14),mat(btnC[i]));b.position.set(cx(-1.4+i*.22),.965,-1.4);sc.add(b)}
const BTN=[cx(.95),.95,-1.38];const bBase=mesh(new T.CylinderGeometry(.16,.18,.05,24),mat('#17141F'));bBase.position.set(BTN[0],.96,BTN[2]);sc.add(bBase);
const red=mesh(new T.CylinderGeometry(.13,.13,.08,24),mat('#E4493F'));red.position.set(BTN[0],1.01,BTN[2]);sc.add(red);
const siren=new T.Mesh(new T.SphereGeometry(.18,16,12),new T.MeshBasicMaterial({color:'#5a1a1a'}));siren.position.set(O,3.85,-1.2);sc.add(siren);
// a beanbag for Dopamine
const bean=mesh(new T.SphereGeometry(.42,20,14),mat('#FF4FB8'));bean.scale.set(1,.55,1);bean.position.set(cx(1.6),.22,-.2);sc.add(bean);
const focus=new Person(sc,FOCUS),dopa=new Person(sc,DOPA),panic=new Person(sc,PANIC);const fSh=blob(sc,1,.5),dSh=blob(sc,1,.5),pSh=blob(sc,1,.5);
const tint=new T.Mesh(new T.PlaneGeometry(4,4),new T.MeshBasicMaterial({color:'#000',transparent:true,opacity:0,depthWrite:false,depthTest:false}));tint.position.set(0,0,-.2);tint.renderOrder=999;cam.add(tint);

// ================= helpers =================
function bl(t,l){for(const b of l)if(t>b&&t<b+.16)return Math.sin((t-b)/.16*Math.PI);return 0}
const sideV=y=>[Math.cos(y),-Math.sin(y)],fwdV=y=>[Math.sin(y),Math.cos(y)];const yawTo=(a,b)=>Math.atan2(b[0]-a[0],b[1]-a[1]);
const mixP=(a,b,k)=>[lerp(a[0],b[0],k),lerp(a[1],b[1],k),lerp(a[2],b[2],k)];
const talkW={F:[[8.0,10.99],[18.8,21.87],[38.8,39.6]],D:[[11.3,13.07],[27.3,30.86],[38.95,39.6]],P:[[36.6,38.67]]};
const talk=(t,w)=>{for(const [a,b] of talkW[w])if(t>a&&t<b)return .35+.35*Math.abs(Math.sin(t*17+a));return 0};
function stand(x,z,yaw,y=.72){const S=sideV(yaw),F=fwdV(yaw);return {pos:[x,y,z],yaw,x,z,feet:{l:[x+S[0]*.13,ANK,z+S[1]*.13],r:[x-S[0]*.13,ANK,z-S[1]*.13]},at:(sd,fw,h)=>[x+S[0]*sd+F[0]*fw,h,z+S[1]*sd+F[1]*fw]}}
function fromWalk(q){const F=fwdV(q.yaw),S=sideV(q.yaw);return {pos:q.pos,yaw:q.yaw,x:q.x,z:q.z,feet:q.feet,hands:q.hands,walking:q.walking,at:(sd,fw,h)=>[q.x+S[0]*sd+F[0]*fw,h,q.z+S[1]*sd+F[1]*fw]}}
const pack=(b,hands,lean,hy,hp,face)=>({pos:b.pos,yaw:b.yaw,feet:b.feet,hands,lean,hy,hp,x:b.x,z:b.z,face});
const hidden={pos:[cx(20),-5,0],yaw:0,feet:{l:[cx(20),-5,0],r:[cx(20),-5,0]},hands:{l:[cx(20),-5,0],r:[cx(20),-5,0]},face:{},x:cx(20),z:0};

// ---------- Skip (apartment) ----------
const SEAT=[CX+.5,CZ+.12];   // right-hand cushion (screen right)
const wIn=walk3({pts:[[2.4,.6],[.6,-1.2],[SEAT[0]+.15,SEAT[1]+.45]],t0:.4,t1:2.7,stride:.6});
const wRun=walk3({pts:[[SEAT[0]+.2,SEAT[1]+.4],[.6,-2.2],[OX-.15,-2.55]],t0:40.6,t1:42.0,stride:.85});
const FLOOR=[OX-.25,-2.55];
function phonePct(t){if(t<31.5)return 3;if(t<33.6)return 2;if(t<36.4)return 1;if(t<42.6)return 0;return kf(t,[[42.6,1],[60,6]])}
function skipPose(t){
 const face={mouth:.4,brow:.2,blink:bl(t,[4.5,10,16.8,25.5,46,52,58])};
 // walk in + flop
 if(t<2.7){const q=fromWalk(wIn.at(t));const hr=q.at(-.25,.22,1.0);return {...pack(q,{l:q.hands.l,r:hr},.05,0,.25,{...face,mouth:.3}),ph:hr,phFace:true}}
 if(t<40.4){
  const legK=ease(seg(t,22.5,23.6))*(1-ease(seg(t,26.6,27.0)));const x=SEAT[0],z=SEAT[1]+.22*legK,yaw=0,S=sideV(0),F=fwdV(0);
  let flop=ease(seg(t,2.7,3.2)),y=lerp(.72,.5,flop)-.04*Math.sin(Math.PI*seg(t,3.1,3.5));
  let lean=lerp(.05,-.32,flop);
  // lean forward then back (13.8-18.2)
  lean+=.5*ease(seg(t,14.2,15.0))*(1-ease(seg(t,15.8,16.5)));
  // leg stretch (22.4-26.6)
  const leg=ease(seg(t,22.5,23.6))*(1-ease(seg(t,26.6,27.0)));
  const wig=leg*Math.sin(t*9)*.025;
  let fl=[x+S[0]*.14,ANK,z+.45],fr=[x-S[0]*.12,ANK,z+.45];
  const hip=[x+S[0]*.115,y,z],dv=[CORD_END[0]-hip[0],CORD_END[1]+ANK-hip[1],CORD_END[2]-hip[2]],dl=Math.hypot(...dv),rch=.64/dl;
  fl=mixP(fl,[hip[0]+dv[0]*rch+wig,Math.max(ANK,hip[1]+dv[1]*rch),hip[2]+dv[2]*rch],leg);
  // phone in right hand at chest, screen to face
  const raise=ease(seg(t,30.8,31.4))*(1-ease(seg(t,36.4,36.8)));const ph=[x-S[0]*.12,lerp(.8,1.05,raise)+.03*Math.sin(t*1.3),z+lerp(.3,.4,raise)];
  const hl=leg>0.1?[x+S[0]*.35,.62,z+.05]:[x+S[0]*.33,.68,z+.12];
  const stare=ease(seg(t,31.3,31.8))*(1-ease(seg(t,36.3,36.6)));
  const panicK=ease(seg(t,36.5,36.9));
  face.eyeS=1+.35*stare+.5*panicK;face.brow=.2+.8*panicK-.2*stare;face.mouth=kf(t,[[3,.5],[13,.5],[14.5,-.2],[16.5,.3],[22.4,-.3],[26.6,-.6],[27.5,.1],[31,0],[36.5,-.8]]);face.open=panicK*.7;
  face.look=leg>.2?.6:0;face.lookY=leg>.2?-.8:0;
  const hp=kf(t,[[3,.3],[13,.3],[22.4,.3],[23.2,.55],[26.6,.55],[27.2,.3],[31.3,.35],[36.5,.1]]);
  return {pos:[x,y,z],yaw,lean,feet:{l:fl,r:fr},hands:{l:hl,r:ph},hy:leg>.2?.35*leg:0,hp,face,ph,phFace:true}}
 if(t<42.0){const q=fromWalk(wRun.at(t));const hr=q.at(-.3,.3,1.25);return {...pack(q,{l:q.at(.33,.2,1.2+Math.sin(t*20)*.15),r:hr},.25,0,.05,{mouth:-.6,open:.7,brow:1,eyeS:1.5}),ph:hr,phFace:false}}
 // plug in (42.0-42.8) then sit on floor (43.2-44.2)
 const x=FLOOR[0],z=FLOOR[1],yaw=kf(t,[[42,Math.PI*.95],[43,Math.PI*.95],[43.6,-.25]]);const S=sideV(yaw),F=fwdV(yaw);
 const sit=ease(seg(t,43.2,44.1));const y=lerp(.72,.24,sit);
 const feet=sit<.05?{l:[x+S[0]*.13,ANK,z+S[1]*.13],r:[x-S[0]*.13,ANK,z-S[1]*.13]}:{l:[x+S[0]*.14+F[0]*.6*sit,ANK,z+S[1]*.14+F[1]*.6*sit],r:[x-S[0]*.14+F[0]*.55*sit,ANK,z-S[1]*.14+F[1]*.55*sit]};
 let ph=mixP([OX,.42,-2.85],[x-S[0]*.1+F[0]*.3,lerp(.5,.62,sit),z-S[1]*.1+F[1]*.3],ease(seg(t,42.6,43.6)));
 const wave=ease(seg(t,57.2,57.7));const hl=mixP([x+S[0]*.3+F[0]*.15,.3+.3*(1-sit),z+S[1]*.3+F[1]*.15],[x+S[0]*.38,1.2+Math.sin(t*9)*.06,z+S[1]*.38+F[1]*.1],wave);
 const face2={mouth:kf(t,[[42,-.3],[44,.7],[57,.9]]),brow:kf(t,[[42,1],[44.5,.2]]),eyeS:t<43.5?1.4:1,blink:bl(t,[46,50.5,54,59.5])};
 const hy=t>48?kf(t,[[48,0],[48.6,-.25],[57,-.25],[57.4,0]]):0;
 return {pos:[x,y,z],yaw,lean:kf(t,[[42,.35],[42.8,.1],[44,-.05]]),feet,hands:{l:hl,r:ph},hy,hp:t<48?kf(t,[[44,.35],[47,.35],[47.6,.1]]):.1,face:face2,ph,phFace:true,plugged:t>42.6}}

// ---------- Brain HQ crew ----------
const FP=[cx(-.35),-.78],DP=[cx(.95),-.72],PP=[cx(-1.3),-.5];
function loopPts(ph){const P=[];for(let i=0;i<=48;i++){const a=ph+i/24*Math.PI*2;P.push([cx(Math.sin(a)*1.0),.1+Math.cos(a)*1.0])}return P}
const cF=walk3({pts:loopPts(0),t0:38.7,t1:40.6,stride:.62}),cD=walk3({pts:loopPts(2.1),t0:38.7,t1:40.6,stride:.62}),cP=walk3({pts:loopPts(4.2),t0:38.7,t1:40.6,stride:.62});
const wP=walk3({pts:[[cx(-4.2),.8],[cx(-2.6),0],PP],t0:36.3,t1:37.2,stride:.75});
function runCircle(w,t,eyes){const q=fromWalk(w.at(t));return pack(q,{l:q.at(.28,.05,1.45+Math.sin(t*13)*.08),r:q.at(-.28,.05,1.45+Math.cos(t*13)*.08)},.05,0,.1,{open:.85,brow:1,eyeS:eyes,blink:0})}
function focusPose(t){if(t>=38.7)return runCircle(cF,t,1.7);const tk=talk(t,'F');
 const yaw=kf(t,[[0,Math.PI],[8,Math.PI],[8.4,Math.PI+1.0],[11,Math.PI+1.0],[11.3,Math.PI+1.4],[18.6,Math.PI+1.4],[18.9,Math.PI+.4],[22,Math.PI+.4],[27,Math.PI+1.4],[36.3,Math.PI+1.4],[36.6,-1.2]]);
 const b=stand(FP[0],FP[1],yaw);const hands={l:b.at(.25,.38,.97),r:b.at(-.25,.38,.97)};
 if(t>8&&t<11){const k=ease(seg(t,8.1,8.5))*(1-ease(seg(t,10.6,11)));hands.l=mixP(hands.l,b.at(.4,.35,1.25+Math.sin(t*6)*.05),k)}
 if(t>18.8&&t<22){const k=ease(seg(t,18.9,19.3))*(1-ease(seg(t,21.6,22)));hands.r=mixP(hands.r,b.at(-.45,.3,1.3),k)}
 const fp=t>27.2&&t<31.2?1:0;if(fp){hands.l=b.at(.05,.18,1.45);}
 return pack(b,hands,.03,kf(t,[[0,0],[11.2,0],[11.5,.3]]),fp?.35:.05,{open:tk,mouth:kf(t,[[0,.1],[11,.1],[11.5,-.5],[18,-.3],[27,-.7]]),brow:kf(t,[[0,0],[11.3,-.4],[13.2,.6],[18,.1],[27.5,.5],[36.5,1]]),sad:kf(t,[[0,0],[11.3,-.5],[13.5,.2]]),eyeS:t>36.4?1.6:1,blink:bl(t,[9.5,19.5,29])})}
function dopaPose(t){if(t>=38.7)return runCircle(cD,t,1.8);const tk=talk(t,'D');
 // lounging on the beanbag the whole time, sits up to talk
 const x=cx(1.6),z=-.2,yaw=yawTo([x,z],FP)+.3,S=sideV(yaw),F=fwdV(yaw);
 const up=Math.max(ease(seg(t,11.0,11.4))*(1-ease(seg(t,13.2,13.6))),ease(seg(t,27.0,27.4))*(1-ease(seg(t,31.0,31.4))),ease(seg(t,36.4,36.8)));
 const y=lerp(.36,.45,up);
 const feet={l:[x+S[0]*.15+F[0]*.55,ANK,z+S[1]*.15+F[1]*.55],r:[x-S[0]*.15+F[0]*.6,ANK,z-S[1]*.15+F[1]*.6]};
 let hands={l:[x+S[0]*.3,.62,z+S[1]*.3-F[1]*.05],r:[x-S[0]*.3,.62,z-S[1]*.3-F[1]*.05]};
 // hands behind head while lounging
 const lounge=1-up;hands.l=mixP(hands.l,[x+S[0]*.18-F[0]*.12,1.1,z+S[1]*.18-F[1]*.12],lounge*.9);hands.r=mixP(hands.r,[x-S[0]*.18-F[0]*.12,1.1,z-S[1]*.18-F[1]*.12],lounge*.9);
 if(up>.5){hands.l=[x+S[0]*.35+F[0]*.25,.95+Math.sin(t*8)*.08,z+S[1]*.35+F[1]*.25];hands.r=[x-S[0]*.35+F[0]*.25,.95+Math.cos(t*8)*.08,z-S[1]*.35+F[1]*.25]}
 return {pos:[x,y,z],yaw,feet,hands,lean:lerp(-.45,-.05,up),hy:0,hp:lerp(-.1,.05,up),x,z,face:{open:tk,mouth:.95,brow:up>.5?.8:.3,eyeS:up>.5?1.3:1,blink:bl(t,[9,15,20,24,33])}}}
function panicPose(t){if(t<36.3)return hidden;if(t>=38.7)return runCircle(cP,t,2);const tk=talk(t,'P');
 const q=t<37.2?fromWalk(wP.at(t)):stand(PP[0],PP[1],.7);return pack(q,{l:q.at(.3,.05,1.6+Math.sin(t*14)*.06),r:q.at(-.3,.05,1.6+Math.cos(t*14)*.06)},.1,0,.05,{open:Math.max(tk,.5),brow:1,eyeS:2,sad:-.3,blink:0})}

// ---------- cameras ----------
function camFor(s,u,t,P){const sk=P.skip;
 switch(s){
 case 0: return {p:[lerp(2.3,1.6,ease(u)),1.55,lerp(2.3,1.6,u)],l:[lerp(.4,-.6,ease(u)),1.0,-2.2],fov:46,focus:3.2,ap:.1};
 case 1: return {p:[lerp(.2,.5,u),.55,-1.3],l:[lerp(.6,OX,ease(seg(u,0,.5))),.35,-2.8],fov:lerp(44,34,ease(u)),focus:1.6,ap:.35};
 case 2: return {p:[cx(lerp(.2,.6,u)),2.1,lerp(3.0,2.5,ease(u))],l:[cx(.3),1.3,-1.4],fov:50,focus:3.6,ap:.1};
 case 3: return {p:[SEAT[0]+1.6,1.1,SEAT[1]+1.5],l:[SEAT[0],.95,SEAT[1]],fov:40,focus:1.5,ap:.3};
 case 4: return {p:[cx(-1.4),1.35,-.05],l:[FP[0],1.3,FP[1]],fov:38,focus:1.3,ap:.4};
 case 5: return u<.45?{p:[SEAT[0]+.3,.95,SEAT[1]+2.1],l:[SEAT[0]+.3,.6,SEAT[1]+.2],fov:46,focus:2,ap:.15}:{p:[lerp(.45,.35,u),.18,lerp(-1.25,-1.4,u)],l:[CORD_END[0]-.06,.07,CORD_END[2]-.02],fov:lerp(40,34,u),focus:.75,ap:.45};
 case 6: return {p:[cx(lerp(-.4,-.1,u)),1.6,1.4],l:[cx(.8),1.1,-.8],fov:48,focus:2.4,ap:.15};
 case 7:{if(u<.5)return {p:[.5,1.02,-.93],l:[.5,1.0,-1.2],fov:30,focus:.27,ap:.6};const ph=sk.ph;const k=ease(seg(u,0,.55));return {p:[lerp(ph[0]+.22,SEAT[0]+.15,k),lerp(ph[1]+.22,1.2,k),lerp(ph[2]-.22,SEAT[1]+1.0,k)],l:[lerp(ph[0],SEAT[0],k),lerp(ph[1],1.1,k),lerp(ph[2],SEAT[1],k)],fov:lerp(34,32,k),focus:lerp(.25,.9,k),ap:.55};}
 case 8: return u<.5?{p:[cx(.25),1.45,.45],l:[P.panic.pos[0],1.35,P.panic.pos[2]],fov:44,focus:1.4,ap:.35}:{p:[cx(lerp(-.5,.5,u)),2.9,2.9],l:[cx(0),.9,.1],fov:46,focus:3.4,ap:.08};
 case 9: return {p:[lerp(.2,.4,u),1.5,lerp(1.4,.6,ease(u))],l:[lerp(SEAT[0],OX-.2,ease(seg(u,.05,.55))),.9,-2.5],fov:48,focus:lerp(2.4,3,u),ap:.1};
 case 10: return {p:[lerp(-.2,-.9,ease(u)),1.4,lerp(.3,.9,u)],l:[lerp(OX-.3,.2,ease(u)),.7,-2.5],fov:46,focus:3.2,ap:.12};
 case 11: return {p:[lerp(OX-1.3,OX-1.0,u),lerp(1.0,.85,u),lerp(-1.0,-1.35,ease(u))],l:[FLOOR[0],.6,FLOOR[1]],fov:40,focus:1.5,ap:.3};
 default: return {p:[OX-.9,.8,-1.4],l:[FLOOR[0],.7,FLOOR[1]],fov:38,focus:1.2,ap:.3};
 }}

const shotOf=f=>{let s=0;while(s<CUTS.length-2&&f>=CUTS[s+1])s++;return s};
const poseIt=(who,P,sh)=>{who.pose({pos:P.pos,yaw:P.yaw,lean:P.lean||0,breath:0,feet:P.feet,hands:P.hands,pole:P.pole||{l:[0,-1,-.6],r:[0,-1,.6]},hand:{},hy:P.hy||0,hp:P.hp||0,face:P.face||{}});sh.position.set(P.pos[0],P.pos[1]<0?-5:.006,P.pos[2])};
window.renderAt=t=>{t=clamp(t,0,DUR_-1/60);const f=Math.round(t*FPS),s=shotOf(f),u=(f-CUTS[s])/(CUTS[s+1]-CUTS[s]);
 const sp=skipPose(t);poseIt(skip,sp,sSh);
 const P={skip:sp,focus:focusPose(t),dopa:dopaPose(t),panic:panicPose(t)};poseIt(focus,P.focus,fSh);poseIt(dopa,P.dopa,dSh);poseIt(panic,P.panic,pSh);
 // phone
 const pct=phonePct(t);const insert=s===7&&u<.5;if(insert){phone.position.set(.5,1.0,-1.2);phone.rotation.set(0,0,.05*Math.sin(t*2))}else{phone.position.set(...sp.ph);phone.rotation.set(-.35,sp.yaw+(sp.phFace?Math.PI:0),0)}
 if(pct<=0&&t<42.6)drawCard(phT,'dead','#000',[{t:'',y:.5,s:.1}]);
 else drawCard(phT,'p'+Math.round(pct)+(sp.plugged?'c':''),'#101828',[{t:Math.round(pct)+'%',y:.3,s:.16,c:pct<=3&&!sp.plugged?'#FF3B3B':'#7CFFB2'},{t:sp.plugged?'charging':'',y:.88,s:.07,c:'#7CFFB2'}],{batt:Math.max(.02,pct/100*3)});
 shortCord.visible=!!sp.plugged;cord.visible=!sp.plugged;plug.visible=!sp.plugged;
 if(sp.plugged){shortCord.geometry.dispose();shortCord.geometry=new T.TubeGeometry(new T.CatmullRomCurve3([V(OX,.4,-2.9),V(OX,.08,-2.8),V((OX+sp.ph[0])/2,.05,(-2.8+sp.ph[2])/2),V(sp.ph[0],sp.ph[1]-.07,sp.ph[2])]),20,.012,6,false)}
 // HQ screen
 let sk,bg='#0d1b3a',L,o={frame:'#FF4FB8'};
 if(t<18.5){sk='task';L=[{t:'MISSION: CHARGE PHONE',y:.2,s:.085,c:'#9FD8F0'},{t:'DISTANCE: 8 FEET',y:.42,s:.1,c:'#fff'},{t:'ENERGY NEEDED: 9,000%',y:.65,s:.1,c:'#FF5E5E'}];if(t>11.3){sk='task2';L.push({t:'STATUS: NOPE',y:.85,s:.08,c:'#F6B73C'})}}
 else if(t<27){sk='toes';L=[{t:'PLAN B',y:.3,s:.12,c:'#F6B73C'},{t:'USE THE TOES',y:.58,s:.13,c:'#fff'}]}
 else if(t<36.3){const b=t<29?.03:t<33.6?.02:.01;sk='watch'+b;L=[{t:'NOW SHOWING: BATTERY',y:.22,s:.085,c:'#FFD27A'},{t:Math.round(b*100)+'%',y:.43,s:.11,c:'#FF5E5E'}];o.batt=b*3}
 else{const fl=Math.floor(t*4)%2;sk='dead'+fl;bg=fl?'#E4493F':'#5a0d14';L=[{t:'!! PHONE DYING !!',y:.38,s:.12,c:'#fff'},{t:'GET UP. GET UP. GET UP.',y:.65,s:.1,c:'#FFD27A'}]}
 drawCard(scrT,sk,bg,L,o);
 const alarm=t>36.3&&t<40.6,pulse=alarm?.5+.5*Math.sin(t*14):0;siren.material.color.set(alarm?(pulse>.5?'#FF2A2A':'#7a1010'):'#5a1a1a');crWalls.forEach((w,i)=>w.material.color.set(alarm&&pulse>.5?'#5a1530':wallBase[i]));
 const inHQ=HQ.has(s);tint.material.color.set('#ff0000');tint.material.opacity=inHQ&&alarm?.18*pulse:0;
 const C=camFor(s,u,t,P);cam.fov=C.fov;cam.position.set(...C.p);cam.lookAt(...C.l);cam.updateProjectionMatrix();post.P.focus.value=C.focus;post.P.ap.value=C.ap;post.P.time.value=f*.137%17;
 // quick dip to black on every jump between the apartment and Brain HQ
 let fade=Math.max(1-seg(t,0,.5),seg(t,DUR_-.6,DUR_-.03));for(const c of [7.5,13.5,18.5,22,27,31.2,36.4,40]){const d=Math.abs(t-c);if(d<.18)fade=Math.max(fade,1-d/.18)}
 post.P.fade.value=fade;post.render(sc,cam);
 return {t,f,sh:s,people:{},contacts:[],sym:0}};
window.CUTF=CUTS;window.DUR=DUR_;
window.EVENTS=[{t:3.1,k:'flop'},{t:7.4,k:'whoosh'},{t:13.4,k:'whoosh'},{t:15.0,k:'creak'},{t:16.4,k:'flop2'},{t:18.4,k:'whoosh'},{t:21.9,k:'whoosh'},{t:26.9,k:'whoosh'},{t:31.1,k:'whoosh'},{t:33.6,k:'beep'},{t:36.3,k:'alarm'},{t:39.9,k:'whoosh'},{t:40.45,k:'launch'},{t:42.6,k:'plug'},{t:42.7,k:'chime'},{t:43.9,k:'flop2'}];
const steps=(t0,t1,n)=>Array.from({length:n},(_,i)=>t0+(t1-t0)*(i+.5)/n);
window.PLANTS={walk:steps(.4,2.7,5),run:[...steps(36.3,37.2,3),...steps(38.7,40.6,10)],sprint:steps(40.6,42.0,4)};window.READY=true;
