import * as T from 'three';
import {V,mat,mesh,Person,makeRenderer,makePost} from './lib3d.js';
const shot=new URLSearchParams(location.search).get('shot')||'wide';
const R=makeRenderer(),post=makePost(R),sc=new T.Scene();
const cam=new T.PerspectiveCamera(35,16/9,.05,200);sc.add(cam);
// sky: big inverted sphere with vertical gradient
const skyTex=(()=>{const c=document.createElement('canvas');c.width=4;c.height=512;const x=c.getContext('2d');const g=x.createLinearGradient(0,0,0,512);g.addColorStop(0,'#5BA8E0');g.addColorStop(.55,'#F7C98B');g.addColorStop(1,'#F29A6B');x.fillStyle=g;x.fillRect(0,0,4,512);const t=new T.CanvasTexture(c);t.colorSpace=T.NoColorSpace;return t})();
const sky=new T.Mesh(new T.SphereGeometry(90,32,16),new T.MeshBasicMaterial({map:skyTex,side:T.BackSide}));sc.add(sky);
const sun=new T.Mesh(new T.CircleGeometry(4,40),new T.MeshBasicMaterial({color:'#FFE7A8'}));sun.position.set(-18,14,-70);sc.add(sun);
const flat={form:0};
const ground=new T.Mesh(new T.PlaneGeometry(200,200),mat('#D9A766',flat));ground.rotation.x=-Math.PI/2;sc.add(ground);
// valley hills both sides (armies' hills) and far hills
const hill=(x,z,sx,sy,sz,c)=>{const h=mesh(new T.SphereGeometry(1,28,16),mat(c));h.scale.set(sx,sy,sz);h.position.set(x,0,z);sc.add(h);return h};
hill(-16,-30,22,7,10,'#C98E55');hill(18,-34,24,8,11,'#BF8550');hill(0,-60,40,12,10,'#E3B47A');
hill(-14,-6,8,3.2,6,'#B97D48');hill(15,-8,9,3.6,6,'#B97D48');
// brook stones
for(let i=0;i<9;i++){const s=mesh(new T.SphereGeometry(.12+Math.random()*.08,10,8),mat('#8E8A93'));s.scale.y=.55;s.position.set(-2.5+i*.65,.04,1.2+Math.sin(i)*.3);sc.add(s)}
const brook=new T.Mesh(new T.PlaneGeometry(40,.9),mat('#6FB7D8',flat));brook.rotation.x=-Math.PI/2;brook.position.set(0,.01,1.6);sc.add(brook);
// tiny armies on far hills (tents + spears silhouette)
for(const [side,col] of [[-1,'#7A56A0'],[1,'#8E2F2C']])for(let i=0;i<14;i++){const t=mesh(new T.ConeGeometry(.5,.9,6),mat(col));t.position.set(side*(10+i*.9),4.2+Math.sin(i)*.6,-24-i*.4);sc.add(t)}
// DAVID: small, shepherd tunic, sling
const DAVID={skin:'#C68E5E',cloth:'#E8D8B0',hood:'#B98B4E',face:'#1c1a2b',leg:'#8A5A3A',shoe:'#5A3A22',bun:'#2A1A12'};
const d=new Person(sc,DAVID);
// GOLIATH: same rig, scaled up, bronze armor + helmet with crest
const GOL={skin:'#B5835A',cloth:'#B5874A',hood:'#7F5A2A',face:'#1c1a2b',leg:'#4A3A2A',shoe:'#2A1E14'};
const g=new Person(sc,GOL);g.g.scale.setScalar(2.35);
const bronze=mat('#C9963F');const helm=mesh(new T.SphereGeometry(.248,28,16,0,Math.PI*2,0,Math.PI*.4),bronze);helm.position.y=.03;g.head.add(helm);
const crest=mesh(new T.BoxGeometry(.04,.12,.34),mat('#B0302C'));crest.position.set(0,.27,-.02);g.head.add(crest);
const shieldM=mesh(new T.CylinderGeometry(.42,.42,.05,32),bronze);
// poses
const P=(o)=>Object.assign({breath:0,lean:0,face:{}},o);
const dz=2.6,gz=-1.4;
const dOut=d.pose(P({pos:[0,.72,dz],yaw:Math.PI,feet:{l:[.16,.07,dz+.08],r:[-.14,.07,dz-.16]},hands:{r:[-.32,1.75,dz+.12],l:[.3,1.0,dz-.2]},hand:{r:'fist',l:'fist'},hp:-.25,face:{mouth:.2,brow:.3}}));
// sling cord from raised hand
const hR=dOut.r.hand;const sl=new T.Mesh(new T.CylinderGeometry(.008,.008,.55,6),mat('#5A3A22',flat));sl.position.set(hR.x-.06,hR.y-.26,hR.z);sl.rotation.z=.25;sc.add(sl);
const stone=mesh(new T.SphereGeometry(.05,12,10),mat('#8E8A93'));stone.position.set(hR.x-.13,hR.y-.53,hR.z);sc.add(stone);
const G=gz/2.35;const gOut=g.pose(P({pos:[0,.72,G],yaw:0,feet:{l:[.2,.07,G+.05],r:[-.2,.07,G-.05]},hands:{r:[-.42,1.15,G+.22],l:[.34,1.0,G+.25]},hand:{r:'fist',l:'fist'},face:{mouth:-.4,brow:-.6}}));
// spear in Goliath's hand (world coords)
g.g.updateMatrixWorld();const fw=g.g.localToWorld(gOut.l.foot.clone());g.g.position.y-=fw.y-.07*2.35+.12;g.g.updateMatrixWorld();console.log('footY',fw.y);const gr=g.g.localToWorld(gOut.r.hand.clone()),gl=g.g.localToWorld(gOut.l.hand.clone());const spear=mesh(new T.CylinderGeometry(.04,.04,6.2,10),mat('#6B4A2A'));spear.position.set(gr.x,gr.y+.6,gr.z);sc.add(spear);
const tip=mesh(new T.ConeGeometry(.1,.45,8),mat('#B8B8C0'));tip.position.set(gr.x,gr.y+3.9,gr.z);sc.add(tip);
shieldM.rotation.x=Math.PI/2;shieldM.position.set(gl.x+.15,gl.y+.1,gl.z+.12);sc.add(shieldM);
const blobS=(x,z,r)=>{const b=new T.Mesh(new T.CircleGeometry(r,32),new T.MeshBasicMaterial({color:'#7a4a2a',transparent:true,opacity:.35,depthWrite:false}));b.rotation.x=-Math.PI/2;b.position.set(x,.02,z);b.scale.y=.6;sc.add(b)};
blobS(0,dz,.35);blobS(0,gz,.85);
if(shot==='wide'){cam.position.set(3.4,1.5,8.2);cam.lookAt(-.2,2.0,0);post.P.focus.value=6;post.P.ap.value=.25}
else{cam.position.set(.9,1.0,4.4);cam.lookAt(-.2,2.9,-1.2);post.P.focus.value=3.5;post.P.ap.value=.4}
post.render(sc,cam);window.DONE=true;
