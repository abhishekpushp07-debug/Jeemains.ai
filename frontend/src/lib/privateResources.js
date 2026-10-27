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
export function prefetchSourceAssets(paths){
 if(navigator.connection?.saveData)return;
 paths.slice(0,2).forEach(path=>{acquireSourceAsset(path).then(asset=>asset.release()).catch(()=>{});});
}
export function rememberStartedAttempt(owner,attempt){
 if(owner===userId&&attempt.status==='active')bootstrap={owner,attempt,at:performance.now()};
}
export function takeStartedAttempt(owner,id){
 const value=bootstrap;bootstrap=null;
 if(!value||owner!==userId||value.owner!==owner||value.attempt.id!==id||performance.now()-value.at>5000)return null;
 return {...value.attempt,server_now:value.attempt.server_now+(performance.now()-value.at)/1000};
}
