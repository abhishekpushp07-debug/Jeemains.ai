import React,{useCallback,useEffect,useState} from 'react';
import {HardDrive,RefreshCw,Loader2,AlertTriangle} from 'lucide-react';
import {Popover,PopoverTrigger,PopoverContent} from '../ui/popover';
import {api} from '../../lib/api';
import {useMachineStatus,MachinePanel,lowDisk} from './MachinePanel';
import {RetryStorageButton,STORAGE_EVENT} from './UploadProgress';
import {LegacyMove} from './LegacyMove';

const LOOK={supabase:['ok','Storage: Supabase','Nayi files Supabase mein ja rahi hain.'],slow:['warn','Storage: Supabase (slow)','Supabase dheere jawab de raha hai; files phir bhi Supabase mein ja rahi hain.'],
 waiting:['bad','Storage: Supabase ka intezaar','Supabase abhi file nahi le raha. Naya kaam ruka hai aur surakshit hai; Emergent mein kuch nahi ja raha. Supabase lautte hi kaam wahin se apne aap aage chalega.'],
 emergent:['warn','Storage: Emergent','Nayi files Emergent storage mein save ho rahi hain.'],down:['bad','Storage band','Dono storage abhi jawab nahi de rahe. Upload ke baad book save nahi ho payegi.']};
const NOT_SET='Supabase set nahi hai. Nayi files Emergent storage mein save ho rahi hain.';
const UPLOAD={supabase:'Storage theek hai: nayi files Supabase mein jayengi. Upload aaram se kar sakte hain.',slow:'Supabase thoda dheere hai, par files save hongi. Upload kar sakte hain.',
 waiting:'Supabase abhi ruka hai. Upload kar sakte hain: PDF server par surakshit rahegi aur Supabase lautte hi apne aap aage badhegi. Emergent mein kuch nahi jayega.'};
const leadText=d=>d?.mode==='emergent'&&d.supabase?.configured===false?NOT_SET:(LOOK[d?.mode]||[])[2];
const ms=s=>s?.ok?`${(s.write_ms||0)+(s.read_ms||0)} ms`:'band';
const ago=t=>{if(!t)return '';const s=Math.max(0,Math.round(Date.now()/1000-t));return s<60?`${s} s pehle`:`${Math.round(s/60)} min pehle`;};

// Asks the server once a minute while the tab is visible; the server itself checks the stores at most once a minute.
export function useStorageHealth(){
 const [data,setData]=useState(null),[busy,setBusy]=useState(false);
 const load=useCallback((fresh=false)=>{setBusy(true);return api('/admin/storage/health'+(fresh?'?fresh=true':'')).then(setData).catch(()=>setData(d=>d||{mode:'unknown'})).finally(()=>setBusy(false));},[]);
 useEffect(()=>{load();const t=setInterval(()=>{if(document.visibilityState==='visible')load();},60000);const now=()=>load(true);window.addEventListener(STORAGE_EVENT,now);return()=>{clearInterval(t);window.removeEventListener(STORAGE_EVENT,now);};},[load]);
 return {data,busy,load};
}

function Row({name,s,extra,testId}){
 return <div className="storage-row" data-testid={testId}><span className={'storage-dot '+(s?.ok?'ok':'bad')}/><strong>{name}</strong><span>{s?.configured===false?'set nahi hai':ms(s)}</span>{extra&&<small>{extra}</small>}{s&&!s.ok&&s.error&&<small className="storage-error">{s.error}</small>}</div>;
}

export function StorageBadge(){
 const {data,busy,load}=useStorageHealth();
 const machine=useMachineStatus();
 const alert=!!machine.data&&(machine.data.attention||lowDisk(machine.data));
 const [tone,label,text]=LOOK[data?.mode]||['wait','Storage…','Check ho raha hai.'];
 return <Popover onOpenChange={open=>{if(open)machine.load();}}><PopoverTrigger asChild><button type="button" className={'storage-badge '+tone} data-testid="storage-badge" aria-label={label+(alert?' · Machine par dhyan dijiye':'')}>
  <span className={'storage-dot '+tone}/><HardDrive size={14} aria-hidden="true"/><span data-testid="storage-badge-label">{label}</span>{data?.mode==='supabase'&&<small>{ms(data.supabase)}</small>}
  {alert&&<i className="machine-alert-dot" data-testid="machine-attention-dot" aria-hidden="true"/>}
 </button></PopoverTrigger>
 <PopoverContent align="end" collisionPadding={12} className="storage-pop" data-testid="storage-details">
  <p className="storage-lead" data-testid="storage-mode-text">{leadText(data)||text}</p>
  <Row name="Supabase (pehli pasand)" s={data?.supabase} extra={data?.supabase?.bucket?'bucket '+data.supabase.bucket:''} testId="storage-row-supabase"/>
  <Row name={data?.supabase?.configured===false?'Emergent':'Emergent (sirf purani files)'} s={data?.emergent} testId="storage-row-emergent"/>
  {data?.mode==='waiting'&&<div className="storage-foot" data-testid="storage-waiting-actions"><small>Supabase ke lautne par ruka kaam apne aap chalega.</small><RetryStorageButton onDone={()=>{load();machine.load();}} testId="storage-retry-now"/></div>}
  {data?.writes&&<p className="storage-meta" data-testid="storage-writes">Server shuru hone ke baad save hui files: Supabase {data.writes.supabase} · Emergent {data.writes.emergent}</p>}
  {data?.last_failover&&<p className="storage-meta" data-testid="storage-last-failover">Aakhri baar file ko Supabase ka intezaar karna pada: {ago(data.last_failover.at)}. Wajah: {data.last_failover.reason}</p>}
  <div className="storage-foot"><small>{data?.checked_at?'Jaancha: '+ago(data.checked_at):''}</small><button type="button" onClick={()=>{load(true);machine.load();}} disabled={busy} data-testid="storage-check-now">{busy?<Loader2 size={13} className="spin"/>:<RefreshCw size={13}/>}Abhi check karo</button></div>
  {data?.supabase?.configured!==false&&<LegacyMove/>}
  <MachinePanel data={machine.data} onReload={machine.load}/>
 </PopoverContent></Popover>;
}

// Super Admin home: a loud line once Supabase has been missing for 10 minutes (new work waits for it, nothing goes to Emergent).
export function StorageAlert(){
 const {data}=useStorageHealth();
 const b=data?.backup;
 if(!b?.alert)return null;
 const min=Math.max(10,Math.round((Date.now()/1000-b.since)/60));
 return <div className="storage-alert" role="alert" data-testid="storage-alert"><AlertTriangle size={18} aria-hidden="true"/><div>
  <strong data-testid="storage-alert-title">{min} minute se Supabase jawab nahi de raha: naya kaam ruka hai</strong>
  <small data-testid="storage-alert-text">Koi file Emergent mein nahi gayi ({b.writes} baar file ko rukna pada). Kaam surakshit hai; Supabase lautte hi wahin se apne aap aage chalega.{data.supabase?.error?' Wajah: '+data.supabase.error:''}</small>
 </div></div>;
}

// The upload dialog says where the PDF will be kept, so the owner knows before sending a big file.
export function StorageNotice(){
 const {data}=useStorageHealth();
 if(!data||!LOOK[data.mode])return null;
 const tone={supabase:'ok',slow:'warn',waiting:'warn',emergent:'warn',down:'error'}[data.mode];
 return <p className={'admin-note '+tone} data-testid="upload-storage-notice">{UPLOAD[data.mode]||leadText(data)+(data.mode==='down'?' Thodi der baad upload kijiye.':' Upload aaram se kar sakte hain.')}</p>;
}
