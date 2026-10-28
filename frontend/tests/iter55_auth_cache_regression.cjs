/* Iter55 actual client/provider/cache/hook modules; only platform/transport/React host dependencies isolated. */
const assert = require('assert');
const fs = require('fs');
const {loadTsModule, mkClientModule, response, wait, withFastTimeouts, mkStorage} = require('./iter49_frontend_isolated_tests.cjs');
const results = [];
const tests = [];
const test = (name, fn) => tests.push({name, fn});
const defer = () => { let resolve; const promise = new Promise(r => resolve=r); return {promise,resolve}; };
const user = {id:'TEST_A',name:'Test',role:'student'};
const session = () => response({body:{user}});

// Deterministic hook host executes real supplied hooks/providers and commit/cleanup ordering, not source regexes.
function host() {
  const slots=[], pending=[]; let cursor=0, renderFn, value, dirty=false;
  const depsEqual=(a,b)=>a&&b&&a.length===b.length&&a.every((x,i)=>Object.is(x,b[i]));
  const React={
    useState(init){const i=cursor++; if(!slots[i]) slots[i]={v:typeof init==='function'?init():init}; return [slots[i].v,v=>{slots[i].v=typeof v==='function'?v(slots[i].v):v;dirty=true;}];},
    useRef(v){const i=cursor++; return (slots[i] ||= {current:v});},
    useEffect(fn,deps){const i=cursor++;if(!depsEqual(slots[i]?.deps,deps)) {pending.push(()=>{slots[i]?.cleanup?.();slots[i]={deps,cleanup:fn()};});}},
    useMemo(fn,deps){const i=cursor++;if(!depsEqual(slots[i]?.deps,deps))slots[i]={deps,v:fn()};return slots[i].v;},
    useCallback(fn,deps){return React.useMemo(()=>fn,deps);},
    createContext(){return {Provider:'Provider'};},useContext(){return value;}
  };
  const jsx={jsx:(type,props)=>{if(type==='Provider')value=props.value;return props;},jsxs:(type,props)=>props};
  return {React,jsx,get value(){return value;},render(fn=renderFn,commit=true){renderFn=fn;cursor=0;dirty=false;const v=fn();if(commit)while(pending.length)pending.shift()();return v;},async flush(){for(let n=0;n<8;n++){await wait();if(dirty)this.render();}},unmount(){slots.forEach(s=>s?.cleanup?.());}};
}
function provider(client) {
  const h=host(), storage=mkStorage(), listeners=new Set();
  const auth=loadTsModule('/app/frontend/src/auth.tsx',{'react':h.React,'react/jsx-runtime':h.jsx,'react-native':{AppState:{addEventListener:(_,f)=>{listeners.add(f);return {remove:()=>listeners.delete(f)};}}},'@/src/api/client':client,'@/src/utils/storage':{storage},'@/src/drafts':{draftIndex:async()=>[],discardAllDrafts:async()=>{}}});
  return {h,storage,listeners,mount:()=>h.render(()=>auth.AuthProvider({children:null}))};
}
async function clientTest(fn) {const c=mkClientModule();try {await fn(c);}finally{c.resetFetch();}}

test('multiple data401 requests share one refresh; late401 reuses token revision',()=>clientTest(async c=>{
  let n=0, refreshed=false;const late=defer();c.setFetch(async url=>{
    if(url.endsWith('/auth/refresh')){n++;await wait(5);refreshed=true;return response();}
    if(url.endsWith('/late')&&!refreshed){await late.promise;return response({status:401});}
    return response({status:refreshed?200:401,body:{ok:refreshed}});
  });
  const slow=c.mod.api('/late');await wait();const vals=await Promise.all([c.mod.api('/one'),c.mod.api('/two')]);late.resolve();assert.deepStrictEqual(await slow,{ok:true});assert(vals.every(v=>v.ok));assert.equal(n,1);
}));
test('rotating session GET and data401 refresh never overlap',()=>clientTest(async c=>{
  const entered=defer(), release=defer();let active=0,max=0;
  c.setFetch(async url=>{if(url.endsWith('/auth/session')){active++;max=Math.max(max,active);entered.resolve();await release.promise;active--;return session();}if(url.endsWith('/auth/refresh')){active++;max=Math.max(max,active);active--;release.resolve();return response();}return response({status:401,body:{detail:'expired access'}});});
  const probe=c.mod.api('/auth/session');await entered.promise;const read=c.mod.api('/one').catch(()=>{});await wait(10);release.resolve();await Promise.all([probe,read]);assert.equal(max,1,'GET/session cookie rotation overlapped POST/refresh');
}));
test('null session receives one refresh then verified user',()=>clientTest(async c=>{let n=0;c.setFetch(async url=>url.endsWith('/auth/refresh')?(n++,response()):n?session():response({body:{user:null}}));assert.deepStrictEqual(await c.mod.api('/auth/session'),{user});assert.equal(n,1);}));
test('mounted good user survives session/data401 rotation collision',()=>clientTest(async c=>{
 c.setFetch(async()=>session());const p=provider(c.mod);p.mount();await p.h.flush();assert.equal(p.h.value.user.id,user.id);
 const entered=defer(),release=defer();let rotating=false,revoked=false,sessionCalls=0;
 c.setFetch(async url=>{
   if(url.endsWith('/auth/session')){sessionCalls++;if(sessionCalls===1){rotating=true;entered.resolve();await release.promise;rotating=false;}return response({body:{user:revoked?null:user}});}
   if(url.endsWith('/auth/refresh')){if(rotating)revoked=true;release.resolve();return response({status:revoked?401:200,body:revoked?{detail:'refresh token reused'}:{ok:true}});}
   return response({status:401,body:{detail:'access expired'}});
 });
 const probe=p.h.value.checkSession();await entered.promise;const reads=Promise.allSettled([c.mod.api('/one'),c.mod.api('/two')]);await wait(10);release.resolve();await Promise.allSettled([probe,reads]);await p.h.flush();const actual=p.h.value.user?.id;p.h.unmount();assert.equal(actual,user.id,'concurrent rotation revoked isolated cookie fixture and forgot good user');
}));
test('confirmed anonymous concurrent requests clear auth exactly once',()=>clientTest(async c=>{let lost=0;c.mod.setAuthLostHandler(()=>lost++);c.setFetch(async url=>url.endsWith('/auth/session')?response({body:{user:null}}):response({status:401,body:{detail:'expired'}}));await Promise.allSettled([c.mod.api('/a'),c.mod.api('/b')]);assert.equal(lost,1);}));
test('PIN/signup/logout/changePIN submissions are never automatically replayed',()=>clientTest(async c=>{c.setFetch(async url=>url.endsWith('/auth/refresh')?response():url.endsWith('/auth/session')?session():response({status:401,body:{detail:'no'}}));for(const path of ['/auth/phone','/auth/phone/signup','/auth/logout','/auth/pin']){c.fetchCalls.length=0;await c.mod.post(path,{}).catch(()=>{});assert.equal(c.fetchCalls.filter(x=>x.url.endsWith(path)).length,1,`${path} replayed`);assert.equal(c.fetchCalls.filter(x=>x.url.endsWith('/auth/refresh')).length,0,`${path} triggered refresh`);}}));
test('old account epoch response is ignored',()=>clientTest(async c=>{const d=defer();c.setFetch(async()=>{await d.promise;return session();});const p=c.mod.api('/auth/session');await wait();c.mod.advanceAuthEpoch();d.resolve();await assert.rejects(p,e=>e.name==='AbortError');}));
test('full body deadline remains bounded with caller signal',()=>clientTest(async c=>{c.setFetch(async()=>({...response(),json:()=>new Promise(()=>{})}));await withFastTimeouts(()=>assert.rejects(c.mod.api('/a',{signal:new AbortController().signal}),e=>e.status===503));}));
test('invalid cached profile never authenticates bootstrap',()=>clientTest(async c=>{c.setFetch(async()=>{throw new Error('offline');});const p=provider(c.mod);await p.storage.setItem('jl_user',JSON.stringify(user));p.mount();await p.h.flush();assert.equal(p.h.value.user,null);assert.equal(p.h.value.ready,true);assert(p.h.value.sessionError);p.h.unmount();}));
for(const variant of ['session503','sessionHTML401','sessionMalformed200','refresh503','refreshTimeout','refreshNull401','refreshMalformed401']){
 test(`verified mounted user survives ${variant}`,()=>clientTest(async c=>{
   c.setFetch(async()=>session());const p=provider(c.mod);p.mount();await p.h.flush();assert.equal(p.h.value.user.id,user.id);
   c.setFetch(async url=>{
     if(url.endsWith('/auth/session')) {
       if(variant.startsWith('refresh'))return response({body:{user:null}});
       if(variant==='session503')return response({status:503});
       if(variant==='sessionHTML401')return {...response({status:401,headers:{'content-type':'text/html'}}),json:async()=>{throw new Error('html');}};
       return response({body:{unexpected:true}});
     }
     if(variant==='refresh503')return response({status:503});
     if(variant==='refreshTimeout')return new Promise((_,reject)=>{});
     if(variant==='refreshNull401')return response({status:401,body:null,headers:{'content-type':'application/json'}});
     return {...response({status:401,headers:{'content-type':'application/json'}}),json:async()=>{throw new Error('malformed');}};
   });
   // Timeout test must honor AbortSignal like native fetch.
   if(variant==='refreshTimeout')c.setFetch(async(url,opts)=>url.endsWith('/auth/session')?response({body:{user:null}}):new Promise((_,reject)=>opts.signal.addEventListener('abort',()=>reject(Object.assign(new Error('aborted'),{name:'AbortError'})))));
   await withFastTimeouts(()=>p.h.value.checkSession());await p.h.flush();assert.equal(p.h.value.user?.id,user.id,'transient/unverified failure logged out verified user');assert.equal(p.h.value.ready,true);p.h.unmount();
 }));
}
test('provider account-switch stale bootstrap cannot resurrect prior account',()=>clientTest(async c=>{const d=defer();c.setFetch(async url=>url.endsWith('/auth/phone')?response({body:{...user,id:'TEST_B'}}):(await d.promise,session()));const p=provider(c.mod);p.mount();await wait();await p.h.value.signIn('TEST_PHONE','TEST_PIN');d.resolve();await p.h.flush();assert.equal(p.h.value.user.id,'TEST_B');p.h.unmount();}));
test('ResourceCache academic TTL10s, explicit force, private counts always revalidate',async()=>{const {ResourceCache}=loadTsModule('/app/frontend/src/resourceCache.ts');const c=new ResourceCache();let n=0,now=Date.now();const real=Date.now;Date.now=()=>now;try{for(const key of ['u.A.pyq.jee-main','u.A./exam-navigation/bitsat/catalogue?kind=mocks']){await c.request(key,async()=>++n);const before=n;now+=9999;await c.request(key,async()=>++n);assert.equal(n,before);now+=2;await c.request(key,async()=>++n);assert.equal(n,before+1);await c.request(key,async()=>++n,false,true);assert.equal(n,before+2);}const before=n;await c.request('u.A.tests.tab=completed',async()=>++n);await c.request('u.A.tests.tab=completed',async()=>++n);assert.equal(n,before+2);}finally{Date.now=real;}});
test('actual useCached warm initial, key/account-null isolation, dedup, 503 retains data',async()=>{
 const {ResourceCache}=loadTsModule('/app/frontend/src/resourceCache.ts');const resources=new ResourceCache(),storage=mkStorage(),h=host();const {useCached}=loadTsModule('/app/frontend/src/useCached.ts',{'react':h.React,'@/src/utils/storage':{storage},'@/src/resourceCache':{resources}});
 let key='u.A.pyq.jee-main',calls=0;await resources.request(key,async()=>({owner:'A'}));let fetcher=async()=>{calls++;return {owner:'B'};};let v=h.render(()=>useCached(key,fetcher,false));assert.equal(v.data.owner,'A');assert.equal(v.loading,false);await h.flush();assert.equal(calls,0);
 key='u.B.pyq.jee-main';const d=defer();fetcher=async()=>{calls++;await d.promise;return {owner:'B'};};v=h.render();assert.equal(v.data,null);assert.equal(v.dataKey,key);await wait();const other=resources.request(key,fetcher);d.resolve();await other;await h.flush();v=h.render();assert.equal(v.data.owner,'B');assert.equal(calls,1);
 fetcher=async()=>{throw new Error('503 unavailable');};h.render();v.reload();await h.flush();v=h.render();assert.equal(v.data.owner,'B');assert(v.error.includes('503'));assert(!v.loading&&!v.refreshing);
 key=null;v=h.render();assert.equal(v.data,null);assert.equal(v.dataKey,null);assert.equal(v.loading,false);h.unmount();
});
test('actual useListFocus avoids mount duplicate; focus/foreground revalidate and cleanup',()=>{const h=host();let focus,cleanup,calls=0,active=new Set();const {useListFocus}=loadTsModule('/app/frontend/src/useListFocus.ts',{'react':h.React,'expo-router':{useFocusEffect:f=>{focus=f;}},'react-native':{AppState:{addEventListener:(_,f)=>{active.add(f);return{remove:()=>active.delete(f)};}}}});const revalidate=()=>calls++;h.render(()=>useListFocus(revalidate));cleanup=focus();assert.equal(calls,0);active.forEach(f=>f('background'));assert.equal(calls,0);active.forEach(f=>f('active'));assert.equal(calls,1);cleanup();assert.equal(active.size,0);cleanup=focus();assert.equal(calls,2);cleanup();});
async function run(){for(const t of tests){try{await t.fn();results.push({name:t.name,passed:true});console.log('PASS',t.name);}catch(e){results.push({name:t.name,passed:false,error:e.message});console.log('FAIL',t.name,e.message);}}fs.mkdirSync('/app/test_reports/artifacts_iter55',{recursive:true});fs.writeFileSync('/app/test_reports/artifacts_iter55/isolated_results.json',JSON.stringify(results,null,2));console.log(`${results.filter(r=>r.passed).length}/${results.length} PASS`);if(results.some(r=>!r.passed))process.exitCode=1;}
run();