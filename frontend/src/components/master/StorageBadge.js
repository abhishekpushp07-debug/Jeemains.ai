import React,{useCallback,useEffect,useState} from 'react';
import {HardDrive,RefreshCw,Loader2} from 'lucide-react';
import {Popover,PopoverTrigger,PopoverContent} from '../ui/popover';
import {api} from '../../lib/api';

const LOOK={supabase:['ok','Storage theek','Nayi files Supabase mein ja rahi hain.'],slow:['warn','Storage slow','Supabase dheere jawab de raha hai; files phir bhi Supabase mein ja rahi hain.'],
 emergent:['warn','Backup storage','Supabase abhi file nahi le raha. Nayi files Emergent storage mein save ho rahi hain.'],down:['bad','Storage band','Dono storage abhi jawab nahi de rahe. Upload ke baad book save nahi ho payegi.']};
const ms=s=>s?.ok?`${(s.write_ms||0)+(s.read_ms||0)} ms`:'band';
const ago=t=>{if(!t)return '';const s=Math.max(0,Math.round(Date.now()/1000-t));return s<60?`${s} s pehle`:`${Math.round(s/60)} min pehle`;};

// Asks the server once a minute while the tab is visible; the server itself checks the stores at most once a minute.
export function useStorageHealth(){
 const [data,setData]=useState(null),[busy,setBusy]=useState(false);
 const load=useCallback((fresh=false)=>{setBusy(true);return api('/admin/storage/health'+(fresh?'?fresh=true':'')).then(setData).catch(()=>setData(d=>d||{mode:'unknown'})).finally(()=>setBusy(false));},[]);
 useEffect(()=>{load();const t=setInterval(()=>{if(document.visibilityState==='visible')load();},60000);return()=>clearInterval(t);},[load]);
 return {data,busy,load};
}

function Row({name,s,extra,testId}){
 return <div className="storage-row" data-testid={testId}><span className={'storage-dot '+(s?.ok?'ok':'bad')}/><strong>{name}</strong><span>{s?.configured===false?'set nahi hai':ms(s)}</span>{extra&&<small>{extra}</small>}{s&&!s.ok&&s.error&&<small className="storage-error">{s.error}</small>}</div>;
}

export function StorageBadge(){
 const {data,busy,load}=useStorageHealth();
 const [tone,label,text]=LOOK[data?.mode]||['wait','Storage…','Check ho raha hai.'];
 return <Popover><PopoverTrigger asChild><button type="button" className={'storage-badge '+tone} data-testid="storage-badge" aria-label={'Storage: '+label}>
  <span className={'storage-dot '+tone}/><HardDrive size={14} aria-hidden="true"/><span data-testid="storage-badge-label">{label}</span>{data?.mode==='supabase'&&<small>{ms(data.supabase)}</small>}
 </button></PopoverTrigger>
 <PopoverContent align="end" className="storage-pop" data-testid="storage-details">
  <p className="storage-lead" data-testid="storage-mode-text">{text}</p>
  <Row name="Supabase (pehli pasand)" s={data?.supabase} extra={data?.supabase?.bucket?'bucket '+data.supabase.bucket:''} testId="storage-row-supabase"/>
  <Row name="Emergent (backup)" s={data?.emergent} testId="storage-row-emergent"/>
  {data?.writes&&<p className="storage-meta" data-testid="storage-writes">Server shuru hone ke baad save hui files: Supabase {data.writes.supabase} · Emergent {data.writes.emergent}</p>}
  {data?.last_failover&&<p className="storage-meta" data-testid="storage-last-failover">Aakhri baar Emergent ne file li: {ago(data.last_failover.at)}. Wajah: {data.last_failover.reason}</p>}
  <div className="storage-foot"><small>{data?.checked_at?'Jaancha: '+ago(data.checked_at):''}</small><button type="button" onClick={()=>load(true)} disabled={busy} data-testid="storage-check-now">{busy?<Loader2 size={13} className="spin"/>:<RefreshCw size={13}/>}Abhi check karo</button></div>
 </PopoverContent></Popover>;
}

// Shown in the upload dialog only when something is not right, so the owner knows before sending a big PDF.
export function StorageNotice(){
 const {data}=useStorageHealth();
 if(!data||!['emergent','down'].includes(data.mode))return null;
 return <p className={'admin-note '+(data.mode==='down'?'error':'warn')} data-testid="upload-storage-notice">{LOOK[data.mode][2]}{data.mode==='down'?' Thodi der baad upload kijiye.':' Upload aaram se kar sakte hain.'}</p>;
}
