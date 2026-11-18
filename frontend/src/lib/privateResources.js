import {fetchWithSession} from './api';

const LIMIT=12*1024*1024, entries=new Map(), flights=new Map(), waiters=[], controllers=new Set();
let bytes=0, epoch=0, userId=null, active=0, bootstrap=null;
function retire(key, entry){
 if(entries.get(key)===entry){entries.delete(key);bytes-=entry.size;}
 entry.retired=true;if(!entry.refs)URL.revokeObjectURL(entry.url);
}
function trim(){
 for(const [key,entry] of entries){if(bytes<=LIMIT)break;if(!entry.refs)retire(key,entry);}
}
export function resetPrivateResources(nextUser=null){
 epoch+=1;userId=nextUser;bootstrap=null;
 for(const controller of controllers)controller.abort();
 for(const [key,entry] of entries){retire(key,entry);URL.revokeObjectURL(entry.url);}
 flights.clear();
}
window.addEventListener('tejas-session-lost',()=>resetPrivateResources(userId));
async function load(path, generation){
 if(active>=4)await new Promise(resolve=>waiters.push(resolve));else active+=1;
 const controller=new AbortController();controllers.add(controller);
 try{
  if(generation!==epoch||!userId)throw new DOMException('Session changed','AbortError');
  const res=await fetchWithSession(path,{cache:'no-store',signal:controller.signal});
  if(!res.ok){const error=new Error(res.status===429||res.status===503?'Source is temporarily busy. Please retry shortly.':'This source image could not load.');error.status=res.status;error.retryAfterMs=Number(res.headers.get('Retry-After')||0)*1000;throw error;}
  if(!(res.headers.get('Content-Type')||'').startsWith('image/'))throw new Error('Source image response is invalid.');
  const blob=await res.blob();
  if(generation!==epoch||!userId)throw new DOMException('Session changed','AbortError');
  const entry={url:URL.createObjectURL(blob),size:blob.size,refs:0,retired:false};
  entries.set(path,entry);bytes+=entry.size;return entry;
 }finally{controllers.delete(controller);if(waiters.length)waiters.shift()();else active-=1;}
}
export async function acquireSourceAsset(path,{reload=false}={}){
 if(!userId)throw new Error('Sign in to view the original source.');
 const generation=epoch;
 if(reload&&entries.has(path))retire(path,entries.get(path));
 let entry=entries.get(path);
 if(entry){entries.delete(path);entries.set(path,entry);}
 else{
  let pending=flights.get(path);
  if(!pending){pending=load(path,epoch);flights.set(path,pending);pending.finally(()=>{if(flights.get(path)===pending)flights.delete(path);}).catch(()=>{});}
  entry=await pending;
 }
 if(generation!==epoch)throw new DOMException('Session changed','AbortError');
 entry.refs+=1;trim();let released=false;
 return {url:entry.url,release:()=>{if(released)return;released=true;entry.refs-=1;if(entry.retired&&!entry.refs)URL.revokeObjectURL(entry.url);trim();}};
}
function hold(entry){
 entry.refs+=1;let released=false;
 return ()=>{if(released)return;released=true;entry.refs-=1;if(entry.retired&&!entry.refs)URL.revokeObjectURL(entry.url);trim();};
}
function keep(path,blob){
 let entry=entries.get(path);
 if(!entry){entry={url:URL.createObjectURL(blob),size:blob.size,refs:0,retired:false};entries.set(path,entry);bytes+=entry.size;}
 return hold(entry);
}
const PACK=12, pause=ms=>new Promise(resolve=>setTimeout(resolve,ms)), BACKEND=process.env.REACT_APP_BACKEND_URL;
// Loads every question picture of an active attempt in a few requests and keeps them in memory until stop().
// Parts come first from public CDN links (same for every student, no cookies), then the private pack, then picture by picture.
// A part that fails is retried until it loads; loading never gives up while the test is open.
export function preloadPaper(attemptId,paths,onProgress){
 const generation=epoch, held=new Map(), controller=new AbortController();
 controllers.add(controller);
 let stopped=false, next=0;
 const live=()=>!stopped&&generation===epoch&&!!userId;
 const missing=list=>list.filter(path=>!held.has(path));
 const report=()=>{if(live())onProgress(held.size,paths.length);};
 const linked=!paths.length?Promise.resolve(null):fetchWithSession(`/attempts/${attemptId}/assets/links`,{cache:'no-store',signal:controller.signal})
  .then(res=>res.ok?res.json():null).then(body=>{const d=body?.data??body;return d&&d.limit===PACK&&d.total===paths.length&&Array.isArray(d.parts)?d.parts:null;})
  .catch(()=>null);
 async function pack(offset,link){
  const res=link?await fetch(link.startsWith('/')?BACKEND+link:link,{credentials:'omit',signal:controller.signal})
   :await fetchWithSession(`/attempts/${attemptId}/assets/pack?offset=${offset}&limit=${PACK}`,{cache:'no-store',signal:controller.signal});
  if(!res.ok)throw new Error('Paper part '+res.status);
  const buffer=await res.arrayBuffer(), size=new DataView(buffer).getUint32(0);
  const head=JSON.parse(new TextDecoder().decode(new Uint8Array(buffer,4,size)));
  let at=4+size;
  for(const item of head.items){
   const path=`/attempts/${attemptId}/questions/${item.question_id}/asset/question/${item.index}`;
   if(live()&&!held.has(path))held.set(path,keep(path,new Blob([new Uint8Array(buffer,at,item.size)],{type:'image/png'})));
   at+=item.size;
  }
 }
 async function part(offset){
  const want=paths.slice(offset,offset+PACK), parts=await linked;
  for(let failures=0;live()&&missing(want).length;){
   for(const path of missing(want))if(entries.has(path))held.set(path,hold(entries.get(path)));
   if(!missing(want).length)break;
   if(!navigator.onLine){await pause(2000);continue;}
   try{
    if(failures<3)await pack(offset,failures<2?parts?.[offset/PACK]:null);
    else for(const path of missing(want)){const asset=await acquireSourceAsset(path);if(live()&&!held.has(path))held.set(path,asset.release);else asset.release();}
   }catch(e){if(e?.name==='AbortError')return;}
   report();
   // A failing CDN link gets a quick second try, then the private pack; later failures back off.
   if(missing(want).length){const quick=parts&&failures<2;failures+=1;await pause(quick?500+Math.random()*500:Math.min(15000,1000*2**Math.min(failures,4))+Math.random()*800);}
  }
 }
 async function worker(){while(live()&&next<paths.length){const offset=next;next+=PACK;await part(offset);}}
 report();
 Promise.all([worker(),worker()]).finally(()=>controllers.delete(controller));
 return ()=>{stopped=true;controller.abort();controllers.delete(controller);for(const release of held.values())release();held.clear();};
}
export function rememberStartedAttempt(owner,attempt){
 if(owner===userId&&attempt.status==='active')bootstrap={owner,attempt,at:performance.now()};
}
export function takeStartedAttempt(owner,id){
 const value=bootstrap;bootstrap=null;
 if(!value||owner!==userId||value.owner!==owner||value.attempt.id!==id||performance.now()-value.at>5000)return null;
 return {...value.attempt,server_now:value.attempt.server_now+(performance.now()-value.at)/1000};
}
