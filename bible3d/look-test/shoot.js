const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1920,height:1080}});
p.on('console',m=>console.log('C:',m.text()));p.on('pageerror',e=>console.log('E:',e.message));
for(const s of ['wide','low']){await p.goto('http://127.0.0.1:8765/index.html?shot='+s);await p.waitForFunction(()=>window.DONE,null,{timeout:60000});await p.locator('#c').screenshot({path:'bible3d-'+s+'.png'});}
await b.close()})();
