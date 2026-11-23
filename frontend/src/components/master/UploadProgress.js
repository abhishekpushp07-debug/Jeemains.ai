import React,{useEffect,useState} from 'react';
import {RotateCw,Loader2} from 'lucide-react';
import {toast} from 'sonner';
import {post} from '../../lib/api';
import {Button} from '../ui/button';

const pct=(a,b)=>b>0?Math.min(100,Math.round(a*100/b)):0;
const mb=n=>n<1048576?`${Math.max(0,Math.round(n/1024))} KB`:`${(n/1048576).toFixed(1)} MB`;
const since=t=>Math.max(0,Math.round((Date.now()/1000-t)/60));
// The storage badge and machine panel listen for this and check again at once.
export const STORAGE_EVENT='jeelive-storage-changed';
const tell=()=>window.dispatchEvent(new Event(STORAGE_EVENT));

// "Abhi phir try karo": the server checks Supabase now; if it answers, every waiting job runs at once.
export async function retryStorage(){
 try{
  const r=await post('/admin/storage/retry');
  if(r.mode==='waiting')toast.error('Supabase abhi bhi jawab nahi de raha. Kaam surakshit hai; apne aap phir koshish hoti rahegi.');
  else toast.success(r.woke?`Supabase wapas aa gaya. ${r.woke} ruka hua kaam phir chal pada.`:'Supabase theek hai.');
  tell();
  return r;
 }catch(e){toast.error(e.message);return null;}
}

export function RetryStorageButton({onDone,testId}){
 const [busy,setBusy]=useState(false);
 const go=async()=>{setBusy(true);await retryStorage();setBusy(false);onDone?.();};
 return <Button size="sm" variant="outline" disabled={busy} onClick={go} data-testid={testId}>{busy?<Loader2 size={14} className="spin" aria-hidden="true"/>:<RotateCw size={14} aria-hidden="true"/>}Abhi phir try karo</Button>;
}

function Bar({value,max,text,testId}){
 return <div className="admin-progress" role="status"><progress value={value} max={max||1}/><small data-testid={testId}>{text}</small></div>;
}

function Stage({b,readLine}){
 if(b.parts)return <Bar value={b.parts.got} max={b.parts.total} testId={'type-upload-parts-'+b.id}
  text={`Server par pahunchi: ${pct(b.parts.got,b.parts.total)}% · ${b.parts.total} mein se ${b.parts.got} hisse`}/>;
 if(b.transfer)return <Bar value={b.transfer.sent} max={b.transfer.size} testId={'type-upload-transfer-'+b.id}
  text={`Original Supabase mein: ${pct(b.transfer.sent,b.transfer.size)}% · ${mb(b.transfer.sent)} / ${mb(b.transfer.size)}`}/>;
 if(b.pages>0)return <Bar value={b.read_pages} max={b.pages} text={readLine(b)} testId={'type-upload-progress-'+b.id}/>;
 return <small>{b.message||'Shuru hone ka intezaar…'}</small>;
}

// Where an uploaded PDF stands: parts on the server, the original into Supabase, pages read, and any wait for Supabase.
export function UploadProgress({b,readLine,onChanged}){
 const waitSince=b.storage_wait?.since;
 useEffect(()=>{if(waitSince)tell();},[waitSince]);
 return <>
  <Stage b={b} readLine={readLine}/>
  {b.storage_wait&&<div className="admin-note warn upload-wait" role="status" data-testid={'type-upload-wait-'+b.id}>
   <p>Supabase ka intezaar · {since(b.storage_wait.since)} min se. Kaam ruka hai, file surakshit hai; Emergent mein kuch nahi gaya. Supabase lautte hi yahin se apne aap aage chalega.</p>
   <RetryStorageButton onDone={onChanged} testId={'type-upload-wait-retry-'+b.id}/>
  </div>}
 </>;
}
