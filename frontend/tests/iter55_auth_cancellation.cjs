/* Additional actual-client edge tests; isolated transport only, no live requests. */
const assert=require('assert');
const fs=require('fs');
const {mkClientModule,response,wait}=require('./iter49_frontend_isolated_tests.cjs');
const results=[];
async function check(name,fn){const c=mkClientModule();try{await fn(c);console.log('PASS',name);results.push({name,passed:true});}catch(e){console.log('FAIL',name,e.message);results.push({name,passed:false,error:e.message});}finally{c.resetFetch();}}
async function run(){
 await check('caller abort promptly cancels auth refresh recovery',async c=>{
   let entered,release;const started=new Promise(r=>entered=r),gate=new Promise(r=>release=r);
   c.setFetch(async url=>url.endsWith('/auth/refresh')?(entered(),await gate,response()):response({status:401,body:{detail:'access expired'}}));
   const ctl=new AbortController();const request=c.mod.api('/my/tests',{signal:ctl.signal}).then(()=> 'success',e=>e.name);
   await started;ctl.abort();const result=await Promise.race([request,wait(15).then(()=> 'pending')]);release();await request;
   assert.equal(result,'AbortError','caller cancellation waits for independent refresh instead of stopping request');
 });
 await check('HTML401 refresh is transient, not auth loss',async c=>{let lost=0;c.mod.setAuthLostHandler(()=>lost++);c.setFetch(async url=>url.endsWith('/auth/refresh')?response({status:401,headers:{'content-type':'text/html'}}):response({status:401,body:{detail:'expired'}}));await assert.rejects(c.mod.api('/my/tests'),e=>e.status===503);assert.equal(lost,0);});
 await check('malformed session401 does not refresh or clear auth',async c=>{let lost=0;c.mod.setAuthLostHandler(()=>lost++);c.setFetch(async()=>({...response({status:401}),json:async()=>{throw new Error('invalid JSON');}}));await assert.rejects(c.mod.api('/auth/session'),e=>e.status===503);assert.equal(lost,0);assert.equal(c.fetchCalls.length,1);});
 fs.writeFileSync('/app/test_reports/artifacts_iter55/auth_extra_results.json',JSON.stringify(results,null,2));if(results.some(r=>!r.passed))process.exitCode=1;
}
run();