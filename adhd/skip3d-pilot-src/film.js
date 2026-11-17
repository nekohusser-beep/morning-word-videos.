// SKIP PILOT (3D): "Inside the ADHD Brain: Pay ONE Bill". 50 s.
import * as T from 'three';
import {clamp,lerp,ease,seg,kf,V,mesh,mat,Person,makeRenderer,makePost,SKIP,FOCUS,DOPA,PANIC,ANK} from './lib3d.js';
import {blob,walk3,chair3} from './world3d.js';
const FPS=30,DUR_=50,W_=1920,H_=1080;
const CUTS=[0,162,252,360,426,498,546,756,798,888,1137,1359,1500];
const R=makeRenderer(),post=makePost(R),sc=new T.Scene(),cam=new T.PerspectiveCamera(35,W_/H_,.05,80);
sc.background=new T.Color('#2a1b3d');sc.add(cam);
const box=(w,h,d,c,x,y,z,o)=>{const m=mesh(new T.BoxGeometry(w,h,d),mat(c,o));m.position.set(x,y,z);sc.add(m);return m};
const bbox=(w,h,d,c,x,y,z)=>{const m=new T.Mesh(new T.BoxGeometry(w,h,d),new T.MeshBasicMaterial({color:c}));m.position.set(x,y,z);sc.add(m);return m};
const flat={form:0};
const canvasTex=(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;const t=new T.CanvasTexture(c);t.colorSpace=T.NoColorSpace;t.anisotropy=8;return {c,x:c.getContext('2d'),t,key:''}};
function drawCard(ct,key,bg,lines,opt={}){if(ct.key===key)return;ct.key=key;const {x,c}=ct;x.fillStyle=bg;x.fillRect(0,0,c.width,c.height);
 if(opt.frame){x.strokeStyle=opt.frame;x.lineWidth=c.width*.02;x.strokeRect(c.width*.03,c.height*.05,c.width*.94,c.height*.9)}
 x.textAlign='center';x.textBaseline='middle';for(const L of lines){x.fillStyle=L.c||'#fff';x.font=`bold ${Math.round(c.height*L.s)}px DejaVu Sans, Arial`;x.fillText(L.t,c.width/2,c.height*L.y)}ct.t.needsUpdate=true}

// ================= APARTMENT (origin) =================
const fl=new T.Mesh(new T.PlaneGeometry(16,12),mat('#B9774F',flat));fl.rotation.x=-Math.PI/2;fl.position.set(0,0,1);sc.add(fl);
for(let i=-7;i<=7;i++)box(.012,.002,12,'#9C5F3D',i*.55,.001,1,flat);
const rug=new T.Mesh(new T.CircleGeometry(1.3,40),mat('#2DB2AE',flat));rug.rotation.x=-Math.PI/2;rug.position.set(0,.004,-1.4);rug.scale.set(1.5,1,1);sc.add(rug);
box(14,3.2,.1,'#FFD9A8',0,1.6,-3.05,flat);box(14,.9,.12,'#F2A65A',0,.45,-2.98,flat);box(14,.05,.14,'#FFF1DC',0,.92,-2.97,flat);
box(.1,3.2,10,'#FFC98E',-6,1.6,2,flat);
box(1.12,2.18,.06,'#5A3F80',-3.9,1.09,-3.0,flat);const leaf=mesh(new T.BoxGeometry(1,2.1,.06),mat('#FF6B5E'));leaf.position.set(-3.9,1.05,-2.94);sc.add(leaf);
box(.7,.5,.04,'#2DB2AE',-2.2,2.0,-2.98,flat);box(.6,.6,.04,'#F6B73C',-1.4,2.15,-2.98,flat);box(.5,.4,.04,'#7A56A0',1.5,2.05,-2.98,flat);
const win=bbox(1.6,1.1,.04,'#9FD8F0',2.9,2.0,-2.98);box(1.6,.05,.06,'#FFF1DC',2.9,2.0,-2.96,flat);box(.05,1.1,.06,'#FFF1DC',2.9,2.0,-2.96,flat);
box(.3,.35,.3,'#E4493F',1.9,.175,-2.6);const pl=mesh(new T.SphereGeometry(.32,14,10),mat('#3FA34D'));pl.position.set(1.9,.62,-2.6);sc.add(pl);
box(1.6,.92,.65,'#FFF1DC',4.2,.46,-2.62);box(1.66,.05,.7,'#7A56A0',4.2,.94,-2.62);
// desk + laptop + lamp
const DX=0,DZ=-2.55;box(1.5,.05,.62,'#8A4A3A',DX,.76,DZ);for(const a of [-.7,.7])box(.06,.76,.56,'#5A2F2A',DX+a,.38,DZ);
box(.46,.025,.32,'#2C2A49',DX,.795,DZ+.1);
const lapT=canvasTex(512,320);const lap=new T.Mesh(new T.PlaneGeometry(.44,.28),new T.MeshBasicMaterial({map:lapT.t}));lap.position.set(DX,.95,DZ-.06);lap.rotation.x=-.18;sc.add(lap);
const lapBack=box(.46,.3,.015,'#2C2A49',DX,.95,DZ-.07);lapBack.rotation.x=-.18;
box(.04,.45,.04,'#17141F',DX+.55,1.0,DZ-.1,flat);const lshade=mesh(new T.CylinderGeometry(.08,.14,.16,18,1,true),mat('#FFE7B0',{side:T.DoubleSide}));lshade.position.set(DX+.55,1.22,DZ-.1);sc.add(lshade);
const glow=new T.Mesh(new T.CircleGeometry(.6,30),new T.MeshBasicMaterial({color:'#FFD27A',transparent:true,opacity:0,depthWrite:false}));glow.rotation.x=-Math.PI/2;glow.position.set(DX+.3,.79,DZ);sc.add(glow);
// big digital wall clock above desk
const clkT=canvasTex(512,200);const clk=new T.Mesh(new T.PlaneGeometry(.9,.35),new T.MeshBasicMaterial({map:clkT.t}));clk.position.set(DX,2.05,-2.955);sc.add(clk);box(.98,.43,.04,'#17141F',DX,2.05,-3.0,flat);
const chair=chair3(sc,DX,-1.92,Math.PI);
const skip=new Person(sc,SKIP);const sSh=blob(sc,1,.5);

// ================= CONTROL ROOM ("Brain HQ") at x=40 =================
const O=40,cx=x=>O+x;
const crFloor=new T.Mesh(new T.PlaneGeometry(12,10),new T.MeshBasicMaterial({color:'#2B2F55'}));crFloor.rotation.x=-Math.PI/2;crFloor.position.set(O,0,1);sc.add(crFloor);
for(let i=-5;i<=5;i++)bbox(.02,.003,10,'#3A3F6E',cx(i*.6),.002,1);
const crWalls=[bbox(12,4,.1,'#1F2348',O,2,-3.05),bbox(.1,4,10,'#262A52',O-5,2,1),bbox(.1,4,10,'#262A52',O+5,2,1)];
const wallBase=['#1F2348','#262A52','#262A52'];
// pink brain-ish wall pattern
for(let i=0;i<9;i++){const b=new T.Mesh(new T.TorusGeometry(.35,.06,8,20,Math.PI*1.3),new T.MeshBasicMaterial({color:'#FF7FB8'}));b.position.set(cx(-4.4+i*1.1),3.4,-3.0);b.rotation.z=i*.7;sc.add(b)}
const scrT=canvasTex(1024,576);const scr=new T.Mesh(new T.PlaneGeometry(3.6,2.02),new T.MeshBasicMaterial({map:scrT.t}));scr.position.set(O,1.95,-2.93);sc.add(scr);bbox(3.8,2.2,.06,'#0d0b14',O,1.95,-3.0);
const sgT=canvasTex(512,96);drawCard(sgT,'s','#FF4FB8',[{t:'BRAIN HQ',y:.52,s:.62,c:'#1F2348'}]);const sg=new T.Mesh(new T.PlaneGeometry(1.6,.3),new T.MeshBasicMaterial({map:sgT.t}));sg.position.set(O,3.15,-2.88);sc.add(sg);
// console
const con=box(3.4,.9,.55,'#3A2F55',O,.45,-1.45);box(3.5,.06,.7,'#5C3F80',O,.92,-1.42);
const btnC=['#2DB2AE','#F6B73C','#7A56A0','#2DB2AE','#F6B73C'];for(let i=0;i<5;i++){const b=mesh(new T.CylinderGeometry(.04,.04,.03,14),mat(btnC[i]));b.position.set(cx(-1.4+i*.22),.965,-1.4);sc.add(b)}
for(let i=0;i<3;i++){const s=box(.08,.12,.02,'#9FD8F0',cx(-.5+i*.3),1.0,-1.62,flat)}
const BTN=[cx(.95),.95,-1.38];
const bBase=mesh(new T.CylinderGeometry(.16,.18,.05,24),mat('#17141F'));bBase.position.set(BTN[0],.96,BTN[2]);sc.add(bBase);
const red=mesh(new T.CylinderGeometry(.13,.13,.08,24),mat('#E4493F'));red.position.set(BTN[0],1.01,BTN[2]);sc.add(red);
const lblT=canvasTex(256,64);drawCard(lblT,'l','#FFF1DC',[{t:'NEW TAB',y:.55,s:.6,c:'#E4493F'}]);const lbl=new T.Mesh(new T.PlaneGeometry(.34,.085),new T.MeshBasicMaterial({map:lblT.t}));lbl.position.set(BTN[0],.93,BTN[2]+.3);lbl.rotation.x=-.5;sc.add(lbl);
const siren=new T.Mesh(new T.SphereGeometry(.18,16,12),new T.MeshBasicMaterial({color:'#5a1a1a'}));siren.position.set(O,3.85,-1.2);sc.add(siren);
const focus=new Person(sc,FOCUS),dopa=new Person(sc,DOPA),panic=new Person(sc,PANIC);
const fSh=blob(sc,1,.5),dSh=blob(sc,1,.5),pSh=blob(sc,1,.5);

// full-screen tint attached to the camera (night / alarm). depthWrite off so focus still reads the scene.
const tint=new T.Mesh(new T.PlaneGeometry(4,4),new T.MeshBasicMaterial({color:'#000',transparent:true,opacity:0,depthWrite:false,depthTest:false}));tint.position.set(0,0,-.2);tint.renderOrder=999;cam.add(tint);

// ================= helpers =================
function bl(t,l){for(const b of l)if(t>b&&t<b+.16)return Math.sin((t-b)/.16*Math.PI);return 0}
const sideV=y=>[Math.cos(y),-Math.sin(y)],fwdV=y=>[Math.sin(y),Math.cos(y)];
const yawTo=(a,b)=>Math.atan2(b[0]-a[0],b[1]-a[1]);
const talkW={N:[],F:[[9.2,11.72],[14.4,16.47],[26.7,27.5]],D:[[12.0,14.03],[16.8,17.4],[26.85,27.5]],P:[[25.4,26.51]]};
const talk=(t,who)=>{for(const [a,b] of talkW[who])if(t>a&&t<b)return .35+.35*Math.abs(Math.sin(t*17+a));return 0};
function stand(x,z,yaw,o={}){const S=sideV(yaw),F=fwdV(yaw),y=o.y||.72;return {pos:[x,y,z],yaw,x,z,F,S,
  feet:{l:[x+S[0]*.13,ANK,z+S[1]*.13],r:[x-S[0]*.13,ANK,z-S[1]*.13]},
  at:(side,fw,h)=>[x+S[0]*side+F[0]*fw,h,z+S[1]*side+F[1]*fw]}}
function fromWalk(q){const F=fwdV(q.yaw),S=sideV(q.yaw);return {pos:q.pos,yaw:q.yaw,x:q.x,z:q.z,F,S,feet:q.feet,hands:q.hands,walking:q.walking,at:(side,fw,h)=>[q.x+S[0]*side+F[0]*fw,h,q.z+S[1]*side+F[1]*fw]}}
const mixP=(a,b,k)=>[lerp(a[0],b[0],k),lerp(a[1],b[1],k),lerp(a[2],b[2],k)];
// circles: 2 loops around (0,0.1), r 1.0
function loopPts(ph){const P=[];for(let i=0;i<=48;i++){const a=ph+i/24*Math.PI*2;P.push([cx(Math.sin(a)*1.0),.1+Math.cos(a)*1.0])}return P}
const cF=walk3({pts:loopPts(0),t0:26.6,t1:29.8,stride:.62}),cD=walk3({pts:loopPts(2.1),t0:26.6,t1:29.8,stride:.62}),cP=walk3({pts:loopPts(4.2),t0:26.6,t1:29.8,stride:.62});
const wD=walk3({pts:[[cx(3.6),.9],[cx(2.2),0],[cx(.95),-.72]],t0:11.9,t1:13.5,stride:.6});
const wP=walk3({pts:[[cx(-4.2),.8],[cx(-2.6),0],[cx(-1.3),-.5]],t0:25.1,t1:26.2,stride:.75});
const FP=[cx(-.35),-.78],DP=[cx(.95),-.72],PP=[cx(-1.3),-.5];

// ---------- per-character poses ----------
function skipPose(t){const x=DX,z=-1.92,yaw=Math.PI,S=sideV(yaw),F=fwdV(yaw);
 const night=t>29.6,typing=night&&t<31.0?1:0;
 const ty=typing?Math.abs(Math.sin(t*26))*.05:0,ty2=typing?Math.abs(Math.cos(t*26))*.05:0;
 let lean=night?(t<37.9?.22:kf(t,[[37.9,.22],[38.6,-.12]])):.06;
 let hl=[x+S[0]*.18+F[0]*.42,.82+ty,z+S[1]*.18+F[1]*.42],hr=[x-S[0]*.18+F[0]*.42,.82+ty2,z-S[1]*.18+F[1]*.42];
 if(!night&&t>2.5&&t<5.4){const tap=Math.abs(Math.sin(t*3))*.02;hl[1]+=tap}
 if(t>37.9&&t<45.3){const k=ease(seg(t,38.1,38.8));hl=mixP(hl,[x+S[0]*.33,.7,z+S[1]*.33+.05],k);hr=mixP(hr,[x-S[0]*.33,.7,z-S[1]*.33+.05],k)}
 if(t>45.3){const w=ease(seg(t,45.5,46.0));hl=[x+S[0]*.33,.7,z+S[1]*.33+.05];hr=mixP([x-S[0]*.33,.7,z-S[1]*.33+.05],[x-S[0]*.38+.1,1.55+Math.sin(t*9)*.06,z+.15],w)}
 const hy=t>37.9?kf(t,[[37.9,0],[38.6,-.9]]):0;
 const face={mouth:kf(t,[[0,.4],[5,.4],[29.6,-.3],[31.2,.2],[37,.9]]),brow:kf(t,[[0,.1],[29.6,1],[31.3,.5],[38,.1]]),eyeS:night&&t<31.2?1.45:1,blink:bl(t,[1.4,4.1,33,40.2,44])};
 return {pos:[x,.54,z],yaw,lean,breath:t*(night?4:2.1),feet:{l:[x+S[0]*.12,ANK,z-.36],r:[x-S[0]*.12,ANK,z-.36]},hands:{l:hl,r:hr},pole:{l:[0,-1,-.6],r:[0,-1,.6]},hy,hp:night&&t<37.9?.18:.05,face}}
function focusPose(t){let b,hands,lean=.03,hy=0,hp=.05;const tk=talk(t,'F');
 if(t>=26.6){const q=fromWalk(cF.at(t));b=q;hands={l:q.at(.28,.05,1.45+Math.sin(t*13)*.08),r:q.at(-.28,.05,1.45+Math.cos(t*13)*.08)};return {...pack(b,hands,.05,0,.1),face:{open:.8,brow:1,eyeS:1.7,sad:-.3,blink:0}}}
 let yaw=kf(t,[[0,Math.PI],[14.3,Math.PI],[14.6,Math.PI+1.2],[16.9,Math.PI+1.2],[17.2,Math.PI*.95]]);
 b=stand(FP[0],FP[1],yaw);hands={l:b.at(.25,.38,.97),r:b.at(-.25,.38,.97)};
 if(t>14.4&&t<16.6){const k=ease(seg(t,14.4,14.8))*(1-ease(seg(t,16.3,16.6)));hands.l=mixP(hands.l,b.at(.5,.38,1.3),k)}
 // head on console during montage
 const slump=ease(seg(t,19.0,19.8))*(1-ease(seg(t,25.0,25.4)));lean+=.55*slump;hp+=.3*slump;
 if(slump>0){hands.l=mixP(hands.l,b.at(.3,.42,.98),slump);hands.r=mixP(hands.r,b.at(-.3,.42,.98),slump)}
 hy=kf(t,[[0,0],[9.0,0],[9.3,.5],[11.6,.5],[12.2,1.1],[14.3,1.1],[14.6,0]]);
 if(t>25.2&&t<26.6){hy=-.8;}
 const face={open:tk,mouth:kf(t,[[0,.2],[12,.2],[12.5,-.5],[17,-.8],[19,-.6]]),brow:kf(t,[[0,0],[12,0],[12.4,-.4],[16.9,.9],[17.4,.4],[25.2,1]]),sad:kf(t,[[0,0],[12,0],[12.4,-.5],[17,.2]]),eyeS:t>25.2?1.6:1,blink:bl(t,[10.5,15.5,22,23.5])};
 return {...pack(b,hands,lean,hy,hp),face}}
function dopaPose(t){let b,hands;const tk=talk(t,'D');
 if(t>=26.6){const q=fromWalk(cD.at(t));hands={l:q.at(.28,.05,1.45+Math.cos(t*13)*.08),r:q.at(-.28,.05,1.45+Math.sin(t*13)*.08)};return {...pack(q,hands,.05,0,.1),face:{open:.85,brow:1,eyeS:1.8,blink:0}}}
 if(t<11.9)return {pos:[cx(20),-5,0],yaw:0,feet:{l:[cx(20),-5,0],r:[cx(20),-5,0]},hands:{l:[cx(20),-5,0],r:[cx(20),-5,0]},face:{}};
 if(t<13.5){const q=fromWalk(wD.at(t));hands={l:q.at(.33,.2,1.0+Math.sin(t*12)*.25),r:q.at(-.33,.2,1.0+Math.cos(t*12)*.25)};return {...pack(q,hands,.12,0,.05),face:{open:tk,mouth:.9,brow:.7,eyeS:1.3}}}
 let yaw=kf(t,[[13.5,yawTo(DP,FP)],[16.2,yawTo(DP,FP)],[16.5,Math.PI]]);
 const dance=t>18.2&&t<25.2;
 if(dance)yaw=Math.PI*.9+Math.sin(t*4)*.5;
 const b2=stand(DP[0],DP[1],yaw,{y:.72-(dance?Math.abs(Math.sin(t*8))*.05:0)});
 hands={l:b2.at(.33,.05,.7),r:b2.at(-.33,.05,.7)};
 if(t<16.5){hands.l=b2.at(.35,.2,1.15+Math.sin(t*9)*.08);hands.r=b2.at(-.35,.2,1.15+Math.cos(t*9)*.08)}
 // smash
 const up=ease(seg(t,16.5,16.8)),down=ease(seg(t,16.85,16.95)),off=ease(seg(t,17.6,18.0));
 if(t>16.4&&t<18.1){let h=mixP(b2.at(-.33,.05,.7),[BTN[0]-.05,1.9,BTN[2]+.25],up);h=mixP(h,[BTN[0],1.07,BTN[2]],down);h=mixP(h,b2.at(-.33,.05,.7),off);hands.r=h}
 if(dance){hands.l=b2.at(.3,.1,1.5+Math.sin(t*8)*.15);hands.r=b2.at(-.3,.1,1.5+Math.cos(t*8)*.15)}
 return {...pack(b2,hands,dance?.05:.08,0,.05),face:{open:tk,mouth:.95,brow:kf(t,[[13.5,.6],[14.4,.2],[16.4,1]]),eyeS:t>16.8&&t<17.6?1.6:1.2,blink:bl(t,[15,20,23])}}}
function panicPose(t){let hands;
 if(t<25.1)return {pos:[cx(20),-5,0],yaw:0,feet:{l:[cx(20),-5,0],r:[cx(20),-5,0]},hands:{l:[cx(20),-5,0],r:[cx(20),-5,0]},face:{}};
 const tk=talk(t,'P');
 if(t>=26.6){const q=fromWalk(cP.at(t));hands={l:q.at(.28,.05,1.5+Math.sin(t*15)*.08),r:q.at(-.28,.05,1.5+Math.cos(t*15)*.08)};return {...pack(q,hands,.05,0,.1),face:{open:.9,brow:1,eyeS:2,blink:0}}}
 let q;if(t<26.2)q=fromWalk(wP.at(t));else q=stand(PP[0],PP[1],kf(t,[[26.2,.9],[26.4,.6]]));
 hands={l:q.at(.3,.05,1.6+Math.sin(t*14)*.06),r:q.at(-.3,.05,1.6+Math.cos(t*14)*.06)};
 return {...pack(q,hands,.1,0,.05),face:{open:Math.max(tk,.5),brow:1,eyeS:2,blink:0}}}
function pack(b,hands,lean,hy,hp){return {pos:b.pos,yaw:b.yaw,feet:b.feet,hands,lean,hy,hp,x:b.x,z:b.z}}

// ---------- cameras ----------
function camFor(s,u,t,P){const f=FP,d=DP;
 switch(s){
 case 0: return {p:[lerp(1.8,1.2,ease(u)),1.6,lerp(1.6,.9,u)],l:[lerp(.2,0,u),1.25,-2.2],fov:46,focus:3,ap:.1};
 case 1:{const k=ease(u),hd=[DX,1.42,-1.85];return {p:[lerp(DX+.9,hd[0],k),lerp(1.55,hd[1],k),lerp(-.7,hd[2]+.02,k*.985)],l:[lerp(DX,hd[0],k*.5),lerp(1.25,1.42,k),lerp(-2.2,-2.6,k)],fov:lerp(42,60,k),focus:lerp(1.4,.3,k),ap:.15};}
 case 2: return {p:[cx(lerp(0,.4,u)),lerp(2.4,2.1,u),lerp(3.2,2.4,ease(u))],l:[cx(0),1.4,-1.6],fov:48,focus:3.8,ap:.1};
 case 3: return {p:[cx(1.0),1.35,1.4],l:[P.dopa.pos[0]-.3,1.15,P.dopa.pos[2]-.2],fov:46,focus:2.2,ap:.15};
 case 4: return {p:[cx(-1.3),1.35,-.05],l:[f[0],1.35,f[1]],fov:36,focus:1.3,ap:.4};
 case 5: return {p:[cx(1.75),1.45,-.55],l:[BTN[0],1.1,BTN[2]],fov:lerp(46,40,u),focus:1.1,ap:.45};
 case 6: return {p:[cx(lerp(.5,0,u)),lerp(1.7,1.9,u),lerp(1.6,.4,ease(u))],l:[cx(0),lerp(1.4,1.85,u),-2.5],fov:42,focus:lerp(4,3.4,u),ap:.12};
 case 7: return {p:[cx(.25),1.45,.45],l:[P.panic.pos[0],1.35,P.panic.pos[2]],fov:44,focus:1.4,ap:.35};
 case 8: return {p:[cx(lerp(-.5,.5,u)),2.9,2.9],l:[cx(0),.9,.1],fov:46,focus:3.4,ap:.08};
 case 9: return {p:[lerp(DX+1.4,DX+1.0,u),1.45,lerp(-.6,-.9,u)],l:[DX-.1,1.3,-2.3],fov:42,focus:1.7,ap:.25};
 case 10: return {p:[DX+.95,1.35,-2.35],l:[DX,1.25,-1.92],fov:lerp(42,36,u),focus:1.0,ap:.4};
 default: return {p:[lerp(1.0,1.8,ease(u)),1.5,lerp(.6,1.6,ease(u))],l:[DX,1.2,-2.0],fov:44,focus:lerp(2.6,3.6,u),ap:.1};
 }}

const shotOf=f=>{let s=0;while(s<CUTS.length-2&&f>=CUTS[s+1])s++;return s};
const poseIt=(who,P,sh)=>{who.pose({pos:P.pos,yaw:P.yaw,lean:P.lean||0,breath:0,feet:P.feet,hands:P.hands,pole:P.pole||{l:[0,-1,-.6],r:[0,-1,.6]},hand:{},hy:P.hy||0,hp:P.hp||0,face:P.face||{}});sh.position.set(P.pos[0],P.pos[1]<0?-5:.006,P.pos[2])};
window.renderAt=t=>{t=clamp(t,0,DUR_-1/60);const f=Math.round(t*FPS),s=shotOf(f),u=(f-CUTS[s])/(CUTS[s+1]-CUTS[s]);
 const sp=skipPose(t);skip.pose({...sp,hand:{}});sSh.position.set(DX,.006,-1.92);
 const P={focus:focusPose(t),dopa:dopaPose(t),panic:panicPose(t)};poseIt(focus,P.focus,fSh);poseIt(dopa,P.dopa,dSh);poseIt(panic,P.panic,pSh);
 const night=t>29.6;
 // apartment screens
 drawCard(clkT,night?(t<32.6?'n1':'n2'):'d',night?'#120a1c':'#17141F',[{t:night?(t<32.6?'11:58 PM':'11:59 PM'):'9:00 AM',y:.55,s:.46,c:night?'#FF5E5E':'#7CFFB2'}]);
 if(!night||t<31.0)drawCard(lapT,'bill','#FFFFFF',[{t:'LIGHT BILL',y:.28,s:.15,c:'#2C2A49'},{t:'$142.18',y:.52,s:.17,c:'#2C2A49'},{t:'PAY NOW',y:.78,s:.12,c:'#FF6B5E'}]);
 else drawCard(lapT,'paid','#3FA34D',[{t:'PAID ✓',y:.52,s:.3,c:'#FFFFFF'}]);
 win.material.color.set(night?'#1d2350':'#9FD8F0');glow.material.opacity=night?.35:0;
 // control room screen
 let sk,bg='#0d1b3a',lines;const flick=Math.sin(t*40)>0;
 if(t<12.4){sk='bill';lines=[{t:'TODAY\'S MISSION',y:.22,s:.09,c:'#9FD8F0'},{t:'PAY THE LIGHT BILL',y:.47,s:.12,c:'#fff'},{t:'est. time: 5 minutes',y:.72,s:.07,c:'#7CFFB2'}]}
 else if(t<16.9){sk='bill2'+(t>12.4&&t<13.2&&flick?'f':'');lines=t>12.4&&t<13.2&&flick?[{t:'SHARKS??',y:.5,s:.22,c:'#fff'}]:[{t:'TODAY\'S MISSION',y:.22,s:.09,c:'#9FD8F0'},{t:'PAY THE LIGHT BILL',y:.47,s:.12,c:'#fff'},{t:'est. time: 5 minutes',y:.72,s:.07,c:'#7CFFB2'}]}
 else if(t<19.6){sk='tab';bg='#E4493F';lines=[{t:'NEW TAB',y:.45,s:.2,c:'#fff'},{t:'opening...',y:.7,s:.08,c:'#FFF1DC'}]}
 else if(t<21.4){sk='shark';bg='#1E6FB5';lines=[{t:'HOW DO SHARKS SLEEP?',y:.4,s:.1,c:'#fff'},{t:'video 37 of 40',y:.65,s:.08,c:'#FFD27A'}]}
 else if(t<23.2){sk='spice';bg='#B9774F';lines=[{t:'SPICE RACK',y:.4,s:.12,c:'#fff'},{t:'ALPHABETIZED ✓',y:.65,s:.1,c:'#7CFFB2'}]}
 else if(t<25.2){sk='uke';bg='#7A56A0';lines=[{t:'UKULELE',y:.4,s:.13,c:'#fff'},{t:'ORDER PLACED ✓',y:.65,s:.1,c:'#F6B73C'}]}
 else{const fl=Math.floor(t*4)%2;sk='due'+fl;bg=fl?'#E4493F':'#5a0d14';lines=[{t:'!! BILL DUE !!',y:.38,s:.13,c:'#fff'},{t:'MIDNIGHT',y:.64,s:.17,c:'#FFD27A'}]}
 drawCard(scrT,sk,bg,lines,{frame:'#FF4FB8'});
 // button press + alarm
 red.position.y=1.01-.035*ease(seg(t,16.9,16.95))*(1-ease(seg(t,17.3,17.5)));
 const alarm=(t>16.95&&t<19.4)||(t>25.2&&t<29.7);const pulse=alarm?.5+.5*Math.sin(t*14):0;
 siren.material.color.set(alarm?(pulse>.5?'#FF2A2A':'#7a1010'):'#5a1a1a');
 crWalls.forEach((w,i)=>w.material.color.set(alarm&&pulse>.5?'#5a1530':wallBase[i]));
 // tint
 const inCR=s>=2&&s<=8;tint.material.color.set(inCR?'#ff0000':'#0a0620');tint.material.opacity=inCR?(alarm?.18*pulse:0):(night?.22:0);
 const C=camFor(s,u,t,P);cam.fov=C.fov;cam.position.set(...C.p);cam.lookAt(...C.l);cam.updateProjectionMatrix();post.P.focus.value=C.focus;post.P.ap.value=C.ap;post.P.time.value=f*.137%17;
 // fades: open, dive into head (7.9-8.4), back out (29.6 in), end
 post.P.fade.value=Math.max(1-seg(t,0,.5),ease(seg(t,7.85,8.35))*(t<8.4?1:0),t>=8.4&&t<9.0?1-seg(t,8.4,9.0):0,t>=29.6&&t<30.2?1-seg(t,29.6,30.2):0,t>29.1&&t<29.6?seg(t,29.1,29.6):0,seg(t,DUR_-.6,DUR_-.03));
 post.render(sc,cam);
 return {t,f,sh:s,people:{},contacts:[],sym:0}};
window.CUTF=CUTS;window.DUR=DUR_;
window.EVENTS=[{t:2.6,k:'type'},{t:7.6,k:'whoosh'},{t:8.5,k:'hum'},{t:12.0,k:'zip'},{t:16.92,k:'smash'},{t:17.0,k:'alarm'},{t:19.6,k:'pop'},{t:21.4,k:'pop'},{t:23.2,k:'pop'},{t:25.2,k:'alarm2'},{t:29.3,k:'whoosh'},{t:29.7,k:'typefast'},{t:31.0,k:'ding'}];
const steps=(t0,t1,n)=>Array.from({length:n},(_,i)=>t0+(t1-t0)*(i+.5)/n);
window.PLANTS={run:[...steps(11.9,13.5,4),...steps(25.1,26.2,4),...steps(26.6,29.8,16)]};window.READY=true;
