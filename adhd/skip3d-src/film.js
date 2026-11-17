// SKIP: "ADHD vs Finding Your Keys" (3D). 46 s, one world: a small apartment.
import * as T from 'three';
import {clamp,lerp,ease,seg,kf,V,mesh,mat,Person,makeRenderer,makePost,SKIP,ANK} from './lib3d.js';
import {blob,walk3} from './world3d.js';
const FPS=30,DUR_=46,W_=1920,H_=1080;
// cut frames (30 fps)
const CUTS=[0,147,237,342,510,666,750,936,1206,1380];
const R=makeRenderer(),post=makePost(R),sc=new T.Scene(),cam=new T.PerspectiveCamera(35,W_/H_,.05,60);
sc.background=new T.Color('#2a1b3d');

// ---------- the apartment (fixed world) ----------
const box=(w,h,d,c,x,y,z,o)=>{const m=mesh(new T.BoxGeometry(w,h,d),mat(c,o));m.position.set(x,y,z);sc.add(m);return m};
const flat={form:0};
// floor (warm wood) + rug
const fl=new T.Mesh(new T.PlaneGeometry(16,12),mat('#B9774F',flat));fl.rotation.x=-Math.PI/2;fl.position.set(0,0,1);sc.add(fl);
for(let i=-7;i<=7;i++)box(.012,.002,12,'#9C5F3D',i*.55,.001,1,flat);
const rug=new T.Mesh(new T.CircleGeometry(1.3,40),mat('#2DB2AE',flat));rug.rotation.x=-Math.PI/2;rug.position.set(0,.004,-.6);rug.scale.set(1.5,1,1);sc.add(rug);
// walls
box(14,3.2,.1,'#FFD9A8',0,1.6,-3.05,flat);              // back wall
box(14,.9,.12,'#F2A65A',0,.45,-2.98,flat);              // wainscot
box(14,.05,.14,'#FFF1DC',0,.92,-2.97,flat);
box(.1,3.2,10,'#FFC98E',-6,1.6,2,flat);                 // left wall
// front door on back wall (hinged on its left edge)
box(1.12,2.18,.06,'#5A3F80',-3.9,1.09,-3.0,flat);      // frame
const door=new T.Group();door.position.set(-4.4,0,-2.94);sc.add(door);
const leaf=mesh(new T.BoxGeometry(1,2.1,.06),mat('#FF6B5E'));leaf.position.set(.5,1.05,0);door.add(leaf);
const knob=mesh(new T.SphereGeometry(.04,12,10),mat('#F2C14E'));knob.position.set(.88,1.0,.05);door.add(knob);
// framed pictures + window
box(.7,.5,.04,'#2DB2AE',-.9,2.1,-2.98,flat);box(.6,.6,.04,'#F6B73C',.3,2.15,-2.98,flat);box(.5,.4,.04,'#7A56A0',1.3,2.05,-2.98,flat);
box(1.6,1.1,.04,'#9FD8F0',2.9,2.0,-2.98,flat);box(1.6,.05,.06,'#FFF1DC',2.9,2.0,-2.96,flat);box(.05,1.1,.06,'#FFF1DC',2.9,2.0,-2.96,flat);
// entry table + the bowl (sitting there the whole time)
const ET=[-2.6,-2.45];
box(.9,.05,.45,'#8A4A3A',ET[0],.86,ET[1]);for(const dx of [-.4,.4])for(const dz of [-.18,.18])box(.04,.86,.04,'#5A2F2A',ET[0]+dx,.43,ET[1]+dz);
const bowl=mesh(new T.CylinderGeometry(.14,.08,.07,24,1,true),mat('#2DB2AE',{side:T.DoubleSide}));bowl.position.set(ET[0]+.22,.92,ET[1]);sc.add(bowl);
const bowlB=mesh(new T.CircleGeometry(.08,20),mat('#187E86'));bowlB.rotation.x=-Math.PI/2;bowlB.position.set(ET[0]+.22,.887,ET[1]);sc.add(bowlB);
// couch
const CX=0,CZ=-2.35;
box(2.2,.42,.85,'#3A5C9A',CX,.32,CZ);box(2.2,.7,.22,'#2F4C82',CX,.75,CZ-.34);
for(const s of [-1,1])box(.22,.58,.85,'#2F4C82',CX+s*1.0,.4,CZ);
const cush=[box(.95,.14,.7,'#4C6FB5',CX-.5,.6,CZ+.04),box(.95,.14,.7,'#4C6FB5',CX+.5,.6,CZ+.04)];
// lamp + plant
box(.04,1.5,.04,'#17141F',-1.6,.75,-2.6,flat);const sh=mesh(new T.CylinderGeometry(.16,.26,.3,20,1,true),mat('#FFE7B0',{side:T.DoubleSide}));sh.position.set(-1.6,1.6,-2.6);sc.add(sh);
box(.3,.35,.3,'#E4493F',1.7,.175,-2.6);const pl=mesh(new T.SphereGeometry(.32,14,10),mat('#3FA34D'));pl.position.set(1.7,.62,-2.6);sc.add(pl);
// kitchen: counter + fridge (door hinged at its right edge, opens toward camera)
box(1.6,.92,.65,'#FFF1DC',3.3,.46,-2.62);box(1.66,.05,.7,'#7A56A0',3.3,.94,-2.62);
const FX=4.75,FZ=-2.55;box(.85,1.85,.7,'#E8EEF2',FX,.925,FZ);
const fIn=box(.75,1.7,.02,'#FFF6D6',FX,.925,FZ+.34,flat);
box(.3,.2,.2,'#F6B73C',FX-.15,1.2,FZ+.1);box(.18,.3,.18,'#FF6B5E',FX+.2,.75,FZ+.1);box(.6,.02,.55,'#CFE3EA',FX,1.0,FZ+.05,flat);
const fdoor=new T.Group();fdoor.position.set(FX+.425,0,FZ+.36);sc.add(fdoor);
const fl2=mesh(new T.BoxGeometry(.85,1.85,.05),mat('#DDE6EC'));fl2.position.set(-.425,.925,0);fdoor.add(fl2);
const fh=mesh(new T.BoxGeometry(.03,.5,.04),mat('#9AA6B0'));fh.position.set(-.78,1.2,.05);fdoor.add(fh);
// keys prop: ring + two keys
const keys=new T.Group();sc.add(keys);keys.scale.setScalar(1.7);
const gold=mat('#F2C14E'),silv=mat('#C9D2DA');
const ring=mesh(new T.TorusGeometry(.035,.007,8,20),silv);keys.add(ring);
const k1=mesh(new T.BoxGeometry(.018,.085,.006),gold);k1.position.set(.012,-.075,0);k1.rotation.z=.25;keys.add(k1);
const k2=mesh(new T.BoxGeometry(.018,.075,.006),silv);k2.position.set(-.015,-.07,.004);k2.rotation.z=-.3;keys.add(k2);
const tag=mesh(new T.BoxGeometry(.04,.03,.006),mat('#FF6B5E'));tag.position.set(0,-.045,-.006);keys.add(tag);

const skip=new Person(sc,SKIP);const shadow=blob(sc,1.1,.55);

// ---------- timeline ----------
const P0=[ET[0],-1.85];                         // standing at entry table
const PC=[CX-.3,-1.45];                          // in front of couch
const PF=[FX-.55,-1.55];                         // in front of fridge
const wC=walk3({pts:[P0,[-1.4,-1.35],PC],t0:8.0,t1:10.9,stride:.6});
const wF=walk3({pts:[PC,[2.2,-1.25],PF],t0:14.0,t1:16.9,stride:.62});
const wB=walk3({pts:[PF,[1.5,-1.2],[-1.2,-1.5],P0],t0:31.6,t1:36.0,stride:.64});
const wD=walk3({pts:[P0,[-3.5,-2.1],[-3.9,-3.6]],t0:42.4,t1:45.6,stride:.6});
const GRAB=[2.0,2.7],DROP=[36.6,37.4],REGRAB=[41.4,42.0];
function bl(t,l){for(const b of l)if(t>b&&t<b+.16)return Math.sin((t-b)/.16*Math.PI);return 0}
const yawTo=(a,b)=>Math.atan2(b[0]-a[0],b[1]-a[1]);
const sideV=yaw=>[Math.cos(yaw),-Math.sin(yaw)],fwdV=yaw=>[Math.sin(yaw),Math.cos(yaw)];

function state(t){
 // base position / walk
 let q=null,base,yaw;
 if(t<8){base=P0;yaw=kf(t,[[0,Math.PI],[3.2,Math.PI],[4.6,0]]);}            // facing table, then turns to camera
 else if(t<11.2){q=wC.at(t);}
 else if(t<14){base=PC;yaw=Math.PI;}                                     // facing couch
 else if(t<17.2){q=wF.at(t);}
 else if(t<31.6){base=PF;yaw=kf(t,[[0,Math.PI*.82],[17.2,Math.PI*.82],[22.3,Math.PI*.82],[23,0.15]]);}  // facing fridge, then turns out
 else if(t<36.3){q=wB.at(t);}
 else if(t<42.4){base=P0;yaw=kf(t,[[0,Math.PI],[38.4,Math.PI],[39.2,.25],[41.0,.25],[41.3,Math.PI]]);}
 else {q=wD.at(t);}
 let p;
 if(q){p={pos:q.pos,yaw:q.yaw,feet:q.feet,hands:{l:q.hands.l,r:q.hands.r},x:q.x,z:q.z,walking:q.walking};}
 else{const S=sideV(yaw),y=.72;p={pos:[base[0],y,base[1]],yaw,x:base[0],z:base[1],walking:0,
   feet:{l:[base[0]+S[0]*.13,ANK,base[1]+S[1]*.13],r:[base[0]-S[0]*.13,ANK,base[1]-S[1]*.13]}};
   p.hands={l:[base[0]+S[0]*.33,.69,base[1]+S[1]*.33],r:[base[0]-S[0]*.33,.69,base[1]-S[1]*.33]};}
 const S=sideV(p.yaw),F=fwdV(p.yaw),X=p.x,Z=p.z;
 const at=(side,fw,y)=>[X+S[0]*side+F[0]*fw,y,Z+S[1]*side+F[1]*fw];
 // lean
 let lean=.03;
 lean+=.42*ease(seg(t,11.6,12.2))*(1-ease(seg(t,13.2,13.8)));   // dig in couch
 lean+=.25*ease(seg(t,18.0,18.6))*(1-ease(seg(t,21.4,22.0)));   // peek in fridge
 lean+=.18*ease(seg(t,36.3,36.7))*(1-ease(seg(t,37.4,37.8)));   // drop in bowl
 lean+=.18*ease(seg(t,41.2,41.5))*(1-ease(seg(t,42.0,42.3)));
 // keys holder: 'table' | 'r' (right hand) | 'bowl'
 let kh='table';if(t>GRAB[1]-.25)kh='r';if(t>DROP[1]-.2)kh='bowl';if(t>REGRAB[1]-.2)kh='r';if(t>45.5)kh='r';
 // right hand (holds keys) — default carried low at the side, slightly forward
 const hold=at(-.3,.08,.66+.02*Math.sin(t*1.7));
 let r=p.walking>.01?[lerp(hold[0],p.hands.r[0],.4),.66,lerp(hold[2],p.hands.r[2],.4)]:hold;
 // grab from table
 const tableK=[ET[0]-.1,.9,ET[1]+.05];
 const g1=ease(seg(t,GRAB[0],GRAB[0]+.4))*(1-ease(seg(t,GRAB[1],GRAB[1]+.5)));
 r=[lerp(r[0],tableK[0],g1),lerp(r[1],tableK[1]+.02,g1),lerp(r[2],tableK[2],g1)];
 // raise keys to face (reveal)
 const lift=ease(seg(t,25.6,26.4))*(1-ease(seg(t,30.6,31.4)));
 const face=at(-.12,.3,1.32);r=[lerp(r[0],face[0],lift),lerp(r[1],face[1],lift),lerp(r[2],face[2],lift)];
 // drop into bowl + regrab
 const bowlP=[ET[0]+.22,.95,ET[1]];
 const d1=ease(seg(t,DROP[0]-.3,DROP[0]+.2))*(1-ease(seg(t,DROP[1],DROP[1]+.4)));
 const d2=ease(seg(t,REGRAB[0]-.3,REGRAB[0]+.1))*(1-ease(seg(t,REGRAB[1],REGRAB[1]+.4)));
 const dd=Math.max(d1,d2);r=[lerp(r[0],bowlP[0],dd),lerp(r[1],bowlP[1]+.03,dd),lerp(r[2],bowlP[2],dd)];
 // left hand: pocket pats, couch dig, fridge, chest
 let l=p.hands.l;
 const pat=ease(seg(t,5.2,5.5))*(1-ease(seg(t,7.6,8.0)));
 if(pat>0){const ph=t<6.1?0:t<6.9?1:2,spots=[at(.2,.12,.62),at(.19,-.02,.95),at(-.05,.14,.62)];const sp=spots[ph],bob=Math.abs(Math.sin(t*14))*.025;l=[lerp(l[0],sp[0],pat),lerp(l[1],sp[1]+bob,pat),lerp(l[2],sp[2],pat)];}
 const dig=ease(seg(t,11.7,12.2))*(1-ease(seg(t,13.2,13.6)));
 if(dig>0){const dp=[CX-.5+.15*Math.sin(t*6),.72,CZ+.25];l=[lerp(l[0],dp[0],dig),lerp(l[1],dp[1],dig),lerp(l[2],dp[2],dig)];}
 const fr=ease(seg(t,17.3,17.8))*(1-ease(seg(t,21.6,22.1)));
 if(fr>0){const fp=[FX+.1,1.15,FZ+.55];l=[lerp(l[0],fp[0],fr),lerp(l[1],fp[1],fr),lerp(l[2],fp[2],fr)];}
 const head=ease(seg(t,19.0,19.4))*(1-ease(seg(t,21.0,21.4)));   // hand on head (panic) while peeking
 if(head>0){const hp=at(.12,.05,1.5);l=[lerp(l[0],hp[0],head),lerp(l[1],hp[1],head),lerp(l[2],hp[2],head)];}
 // face
 const fc={mouth:kf(t,[[0,.5],[5,.5],[6.8,.4],[7.3,-.2],[11,-.3],[12,.1],[16,-.4],[18,-.5],[21,-.7],[24.5,-.6],[25.5,.15],[26.5,.2],[29,.6],[33,.7],[39.2,.85],[41,.85],[44,.7]]),
  brow:kf(t,[[0,.1],[6.8,.1],[7.3,.9],[11,.6],[17,.5],[19,.2],[22.6,.3],[25.5,1],[28,.7],[31,.2]]),
  sad:kf(t,[[0,0],[16,0],[18,-.4],[22,-.5],[24,-.3],[26,0]]),
  look:kf(t,[[0,0],[7,0],[7.3,-.3],[8,0]]),blink:bl(t,[1.5,9.5,15.2,24.2,33.5,40.4])};
 let hy=kf(t,[[0,0],[1.4,0],[1.8,.15],[3,.15],[3.4,0],[6.2,-.3],[6.6,.3],[7.0,0]]);
 let hp=kf(t,[[0,.05],[1.7,.05],[2.1,.35],[2.9,.35],[3.2,.05],[25.2,.05],[25.6,.45],[26.3,.15],[35.9,.1],[36.4,.4],[37.6,.4],[38,.05],[41,.05],[41.3,.35],[42,.05]]);
 return {p,r,l,lean,fc,hy,hp,kh,tableK,bowlP};
}

// camera per shot: u = 0..1 through the shot
function camFor(s,u,t,st){
 const X=st.p.x,Z=st.p.z;
 switch(s){
 case 0: return {p:[lerp(-.6,-1.0,ease(u)),1.55,lerp(3.0,2.6,u)],l:[lerp(-1.9,-2.3,ease(u)),1.0,-2.0],fov:44,focus:4.3,ap:.08};          // wide: room + table
 case 1: return {p:[X+.25,1.3,Z+2.7],l:[X,1.0,Z],fov:36,focus:2.7,ap:.28};                                                                 // medium front: pat-down
 case 2: return {p:[X+.4,1.3,Z+2.6],l:[X,1.0,Z-.2],fov:38,focus:2.6,ap:.18};                                                                // tracking to couch
 case 3: return {p:[lerp(1.0,1.6,u),1.45,1.8],l:[lerp(.2,2.6,ease(seg(u,.35,1))),.95,-2.0],fov:42,focus:3.6,ap:.1};                         // couch dig, pan to kitchen
 case 4: return {p:[FX+.12,1.32,FZ+.3],l:[X,1.4,Z],fov:54,focus:1.2,ap:.3};                                                     // fridge
 case 5:{const a=lerp(1.0,-0.95,ease(u)),rad=lerp(2.1,1.0,ease(u)),cy=lerp(1.5,.95,ease(u));                                   // 3D ORBIT reveal
   return {p:[X+Math.sin(a)*rad,cy,Z+Math.cos(a)*rad],l:[lerp(X,st.r[0],ease(u)),lerp(1.1,st.r[1],ease(u)),lerp(Z,st.r[2],ease(u))],fov:lerp(38,30,u),focus:rad,ap:.45};}
 case 6:{const F=fwdV(st.p.yaw);return {p:[X+F[0]*1.25+.15,1.4,Z+F[1]*1.25],l:[X,1.32,Z],fov:30,focus:1.25,ap:.6};}                          // close-up face + keys
 case 7: return {p:[lerp(.8,-1.5,ease(u)),lerp(1.5,1.35,u),lerp(2.4,-1.3,ease(seg(u,.45,1)))],l:[lerp(X,ET[0]+.1,ease(seg(u,.55,1))),1.0,lerp(Z,ET[1]+.2,ease(seg(u,.55,1)))],fov:lerp(42,34,u),focus:lerp(3.4,2.4,u),ap:.2}; // walk back + bowl
 default: return {p:[-1.2,1.35,lerp(1.4,1.7,u)],l:[-3.0,1.05,-2.2],fov:40,focus:3.2,ap:.15};                                            // exit
 }
}

const shotOf=f=>{let s=0;while(s<CUTS.length-2&&f>=CUTS[s+1])s++;return s};
window.renderAt=t=>{t=clamp(t,0,DUR_-1/60);const f=Math.round(t*FPS),s=shotOf(f),u=(f-CUTS[s])/(CUTS[s+1]-CUTS[s]);
 const st=state(t),p=st.p;
 skip.pose({pos:p.pos,yaw:p.yaw,lean:st.lean,breath:t*2.3,feet:p.feet,hands:{l:st.l,r:st.r},pole:{l:[0,-1,-.6],r:[0,-1,.6]},hand:{r:'fist'},hy:st.hy,hp:st.hp,face:st.fc});
 shadow.position.set(p.x,.006,p.z);
 // keys
 if(st.kh=='table'){keys.position.set(...st.tableK);keys.rotation.set(-Math.PI/2,0,.6);}
 else if(st.kh=='bowl'){keys.position.set(st.bowlP[0],st.bowlP[1]-.03,st.bowlP[2]);keys.rotation.set(-Math.PI/2+.3,0,1.1);}
 else{const lf=ease(seg(t,25.6,26.4))*(1-ease(seg(t,30.6,31.4)));keys.position.set(st.r[0],st.r[1]-.02+lf*.13,st.r[2]+lf*.05);keys.rotation.set(0,p.yaw,.15*Math.sin(t*5));}
 // couch cushion lift, fridge door, front door
 cush[0].position.y=.6+.12*ease(seg(t,11.9,12.3))*(1-ease(seg(t,13.0,13.4)));cush[0].rotation.x=-.25*ease(seg(t,11.9,12.3))*(1-ease(seg(t,13.0,13.4)));
 fdoor.rotation.y=ease(seg(t,17.4,17.9))*1.55*(1-ease(seg(t,21.7,22.2)));
 door.rotation.y=-ease(seg(t,42.8,43.6))*1.6;
 fIn.visible=s!=4; const C=camFor(s,u,t,st);
 cam.fov=C.fov;cam.position.set(...C.p);cam.lookAt(...C.l);cam.updateProjectionMatrix();post.P.focus.value=C.focus;post.P.ap.value=C.ap;post.P.time.value=f*.137%17;post.P.fade.value=Math.max(1-seg(t,0,.5),seg(t,DUR_-.6,DUR_-.03));post.render(sc,cam);
 return {t,f,sh:s,people:{},contacts:[],sym:0}};
const steps=(t0,t1,n)=>Array.from({length:n},(_,i)=>t0+.25+(t1-t0-.5)*(i+.5)/n);
window.CUTF=CUTS;window.DUR=DUR_;
window.EVENTS=[{t:GRAB[0]+.35,k:'keys'},{t:5.3,k:'pat'},{t:5.7,k:'pat'},{t:6.2,k:'pat'},{t:6.5,k:'pat'},{t:7.0,k:'pat'},{t:12.0,k:'cushion'},{t:13.1,k:'cushion'},{t:17.45,k:'fridge'},{t:21.9,k:'fridgeshut'},{t:22.4,k:'heart'},{t:23.2,k:'heart'},{t:25.7,k:'keys'},{t:DROP[0]+.1,k:'bowl'},{t:REGRAB[0]+.1,k:'keys'},{t:42.9,k:'door'}];
window.PLANTS={skip:[...steps(8,10.9,5),...steps(14,16.9,5),...steps(31.6,36,8),...steps(42.4,45.6,5)]};window.READY=true;
