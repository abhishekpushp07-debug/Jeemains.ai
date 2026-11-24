import React,{useEffect,useRef,useState} from 'react';
import {RotateCw,Loader2,AlertTriangle} from 'lucide-react';
import {toast} from 'sonner';
import {post} from '../../lib/api';
import {Button} from '../ui/button';

const pct=(a,b)=>b>0?Math.min(100,Math.round(a*100/b)):0;
const mb=n=>n<1048576?`${Math.max(0,Math.round(n/1024))} KB`:`${(n/1048576).toFixed(1)} MB`;
const since=t=>Math.max(0,Math.round((Date.now()/1000-t)/60));
// The storage badge and machine panel listen for this and check again at once.
export const STORAGE_EVENT='jeelive-storage-changed';
// Many rows that change together (a page of waiting uploads) ask for one check, not one each.
let told=0;
const tell=()=>{clearTimeout(told);told=setTimeout(()=>window.dispatchEvent(new Event(STORAGE_EVENT)),200);};

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
 return b.storage_wait?null:<small>{b.message||'Shuru hone ka intezaar…'}</small>;
}

const ALERT_MIN=15;
// What the owner reads while a file is not in Supabase: Supabase away, the project blocked, only this file returned, or stuck ("Atki hai").
function waitWords(w,min){
 const why=w.reason?` Wajah: ${w.reason}.`:'',what=w.mock?`"${w.mock}" ki ek picture`:'Yeh PDF';
 if(w.retrying)return ['Dobara koshish chal rahi hai…','Nateeja kuch pal mein yahin dikhega.'];
 if(w.stuck)return [`Atki hai · ${min} min se.`,`${what} Supabase mein nahi ja rahi. File surakshit hai aur baaki kitaabein chal rahi hain; Emergent mein kuch nahi gaya.${why} ${w.next||'Har 15 minute mein apne aap phir koshish hogi.'}`];
 if(w.kind==='blocked')return [`Supabase project par rok · ${min} min se.`,`Naya kaam ruka hai, file surakshit hai; Emergent mein kuch nahi gaya.${why} ${w.next||''}`];
 if(w.kind==='file')return [`Yeh file abhi Supabase mein nahi gayi · ${min} min se.`,`Machine khud phir koshish kar rahi hai; baaki kitaabein chal rahi hain.${why}`];
 return [`Supabase ka intezaar · ${min} min se.`,`Kaam ruka hai, file surakshit hai; Emergent mein kuch nahi gaya. Supabase lautte hi yahin se apne aap aage chalega.${why}`];
}

// After 15 minutes the note turns into a loud alert, right in the upload's own progress row.
function WaitNote({b,onChanged}){
 const w=b.storage_wait,min=since(w.since),late=min>=ALERT_MIN&&!w.retrying,[lead,rest]=waitWords(w,min);
 return <div className={'admin-note upload-wait '+(late||w.stuck?'error':'warn')+(late?' is-late':'')} role={late?'alert':'status'} data-kind={w.retrying?'retrying':w.stuck?'stuck':w.kind} data-testid={'type-upload-wait-'+b.id}>
  <p>{late&&<strong className="upload-late" data-testid={'type-upload-alert-'+b.id}><AlertTriangle size={15} aria-hidden="true"/>{min} minute se {w.mock?'yeh picture':'yeh PDF'} Supabase mein nahi gayi.</strong>}<b data-testid={'type-upload-lead-'+b.id}>{lead}</b> {rest}</p>
  {!w.stuck&&!w.retrying&&<RetryStorageButton onDone={onChanged} testId={'type-upload-wait-retry-'+b.id}/>}
 </div>;
}

// Where an uploaded PDF stands: parts on the server, the original into Supabase, pages read, and any wait for Supabase.
export function UploadProgress({b,readLine,onChanged}){
 const waitSince=b.storage_wait?.since,was=useRef(waitSince);
 // A wait that starts or ends: the badge and machine panel check again at once.
 useEffect(()=>{if(waitSince||was.current)tell();was.current=waitSince;},[waitSince]);
 useEffect(()=>()=>{if(was.current)tell();},[]);
 return <>
  <Stage b={b} readLine={readLine}/>
  {b.storage_wait&&<WaitNote b={b} onChanged={onChanged}/>}
 </>;
}
