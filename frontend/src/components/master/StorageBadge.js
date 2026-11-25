import React,{useCallback,useEffect,useState} from 'react';
import {HardDrive,RefreshCw,Loader2,AlertTriangle,Upload} from 'lucide-react';
import {toast} from 'sonner';
import {Popover,PopoverTrigger,PopoverContent} from '../ui/popover';
import {api,post} from '../../lib/api';
import {useMachineStatus,MachinePanel,lowDisk,ago} from './MachinePanel';
import {RetryStorageButton,STORAGE_EVENT} from './UploadProgress';
import {LegacyMove} from './LegacyMove';

const LABEL={supabase:'Storage: Supabase',slow:'Storage: Supabase (slow)',waiting:'Storage: Supabase ka intezaar',emergent:'Storage: Emergent',down:'Storage band'};
// The colour comes from the server's one shared record: green, yellow or red, each with its reasons.
const TONE={green:'ok',yellow:'warn',red:'bad'};
const NOT_SET='Supabase set nahi hai. Nayi files Emergent storage mein save ho rahi hain.';
const UPLOAD={supabase:'Storage theek hai: nayi files Supabase mein jayengi. Upload aaram se kar sakte hain.',slow:'Supabase thoda dheere hai, par files save hongi. Upload kar sakte hain.',
 waiting:'Supabase abhi ruka hai. Upload kar sakte hain: PDF server par surakshit rahegi aur Supabase lautte hi apne aap aage badhegi. Emergent mein kuch nahi jayega.'};
const BIG_BAD='Supabase chhoti files le raha hai, par badi file (6 MB se badi PDF) ka raasta pichhli baar nahi chala. Upload kar sakte hain: PDF server par surakshit rahegi aur machine khud phir koshish karegi.';
const took=s=>(s?.write_ms||0)+(s?.read_ms||0);
const ms=s=>s?.ok?(took(s)>0?`${took(s)} ms`:'theek'):'band';
const sec=n=>`${(n/1000).toFixed(1)} second`;
const mbs=n=>`${(n/1048576).toFixed(1)} MB`;
const spd=s=>s?.n?`aam taur par ${s.median_ms} ms (${s.min_ms} se ${s.max_ms} ms, ${s.n} jaanch)`:'abhi koi reading nahi';
const smallNote=s=>!s?.at?'':s.how==='file'?`Asli file save hui: ${ago(s.at)}`:`Jaancha: ${ago(s.at)} · naye naam ki jaanch file likhi, wapas padhi, hatayi`;
function bigNote(b){
 if(!b?.at)return 'Abhi tak jaancha nahi gaya.';
 const what=(b.how==='pdf'?'Asli PDF':'Test file')+(b.size?` (${mbs(b.size)})`:'');
 if(b.state==='bad')return `${what} nahi gayi · ${ago(b.at)}`;
 return b.how==='pdf'?`${what} ${b.via==='one'?'ek request mein':'tukdon mein'} save hui · ${ago(b.at)}`:`${what} tukdon mein gayi, wapas padhi gayi, hatayi gayi · ${ago(b.at)}`;
}

// Asks the server once a minute while the tab is visible; the server itself checks the stores at most once a minute.
export function useStorageHealth(){
 const [data,setData]=useState(null),[busy,setBusy]=useState(false);
 const load=useCallback((fresh=false)=>{setBusy(true);return api('/admin/storage/health'+(fresh?'?fresh=true':'')).then(setData).catch(()=>setData(d=>d||{mode:'unknown'})).finally(()=>setBusy(false));},[]);
 useEffect(()=>{load();const t=setInterval(()=>{if(document.visibilityState==='visible')load();},60000);const now=()=>load(true);window.addEventListener(STORAGE_EVENT,now);return()=>{clearInterval(t);window.removeEventListener(STORAGE_EVENT,now);};},[load]);
 return {data,busy,load,setData};
}

function Row({name,tone,value,note,error,testId,children}){
 return <div className="storage-row" data-testid={testId}><span className={'storage-dot '+tone}/><strong>{name}</strong><span data-testid={testId+'-value'}>{value}</span>
  {note&&<small data-testid={testId+'-note'}>{note}</small>}{error&&<small className="storage-error" data-testid={testId+'-error'}>{error}</small>}{children}</div>;
}

// "Badi file ka test": about 7 MB goes by the real piece route, is read back and removed. It says how long it took, or why it failed.
function BigTest({running,onDone}){
 const [busy,setBusy]=useState(false);
 const on=busy||running;
 async function go(){
  setBusy(true);
  try{
   const r=await post('/admin/storage/big-test'),t=r.big_test;
   if(!t)toast.message('Badi file ka test abhi chal raha hai (Supabase dheema hai). Nateeja yahin dikhega.');
   else if(t.ok)toast.success(`Badi file ka raasta theek hai: ${mbs(t.size)} ki test file ${sec(t.ms)} mein gayi, wapas padhi gayi aur hata di gayi.`);
   else toast.error(`Badi file ka test fail hua. Wajah: ${t.reason}.`);
   onDone(r);
  }catch(e){toast.error(e.message);onDone(null);}
  finally{setBusy(false);}
 }
 return <button type="button" onClick={go} disabled={on} data-testid="storage-big-test">{on?<Loader2 size={13} className="spin" aria-hidden="true"/>:<Upload size={13} aria-hidden="true"/>}{on?'Test chal raha hai…':'Badi file ka test'}</button>;
}

export function StorageBadge(){
 const {data,busy,load,setData}=useStorageHealth();
 const machine=useMachineStatus();
 const alert=!!machine.data&&(machine.data.attention||lowDisk(machine.data));
 const tone=TONE[data?.level]||'wait',label=LABEL[data?.mode]||'Storage…';
 const reasons=data?.reasons||[data?'Storage ki haalat abhi nahi mil payi. "Abhi check karo" dabaiye.':'Check ho raha hai.'];
 const sb=data?.supabase||{},big=data?.big||{},em=data?.emergent||{},set=sb.configured!==false;
 // While a big-file test runs (here or on another server) the record is read again every 5 s, so its result shows by itself.
 useEffect(()=>{if(!big.running)return undefined;const t=setTimeout(()=>load(),5000);return()=>clearTimeout(t);},[data,big.running,load]);
 return <Popover onOpenChange={open=>{if(open)machine.load();}}><PopoverTrigger asChild><button type="button" className={'storage-badge '+tone} data-testid="storage-badge" data-level={data?.level||''} aria-label={label+(alert?' · Machine par dhyan dijiye':'')}>
  <span className={'storage-dot '+tone}/><HardDrive size={14} aria-hidden="true"/><span data-testid="storage-badge-label">{label}</span>{data?.mode==='supabase'&&sb.ok===true&&took(sb)>0&&<small>{ms(sb)}</small>}
  {alert&&<i className="machine-alert-dot" data-testid="machine-attention-dot" aria-hidden="true"/>}
 </button></PopoverTrigger>
 <PopoverContent align="end" collisionPadding={12} className="storage-pop" data-testid="storage-details">
  <div className={'storage-reasons '+tone} data-testid="storage-reasons">{reasons.map((r,i)=><p key={i} className="storage-lead" data-testid={i?'storage-reason-'+i:'storage-mode-text'}>{r}</p>)}</div>
  {data?.level&&<>
   <Row name={set?'Supabase · Pictures (chhoti file)':'Supabase'} tone={sb.ok?(data.mode==='slow'?'warn':'ok'):sb.state==='warn'?'warn':'bad'} value={set?(sb.ok?ms(sb):sb.state==='warn'?'jaanch fail':'band'):'set nahi hai'} note={set?smallNote(sb):''} error={set&&!sb.ok?sb.error:''} testId="storage-row-supabase"/>
   {set&&<Row name="Supabase · PDF (badi file)" tone={big.state==='ok'?'ok':big.state==='bad'?'bad':'warn'} value={big.state==='ok'?(big.ms?`theek · ${sec(big.ms)}`:'theek'):big.state==='bad'?'fail':'jaancha nahi'} note={bigNote(big)} error={big.error} testId="storage-row-big">
    <div className="storage-foot storage-row-act"><BigTest running={big.running} onDone={r=>{if(r)setData(r);else load();machine.load();}}/></div>
   </Row>}
   <Row name={set?'Emergent (fallback)':'Emergent'} tone={em.ok?'ok':set?'warn':'bad'} value={ms(em)} note={em.at?`Jaancha: ${ago(em.at)} · ek hi naam ki jaanch file (Emergent mein file hatai nahi ja sakti)`:''} error={em.ok?'':em.error} testId="storage-row-emergent"/>
   <p className="storage-meta" data-testid="storage-speed">Aakhri 20 jaanch ki speed (likhna + padhna). Supabase: {spd(data.speed?.supabase)}. Emergent: {spd(data.speed?.emergent)}.</p>
  </>}
  {data?.mode==='waiting'&&<div className="storage-foot" data-testid="storage-waiting-actions"><small>Supabase ke lautne par ruka kaam apne aap chalega.</small><RetryStorageButton onDone={()=>{load();machine.load();}} testId="storage-retry-now"/></div>}
  <div className="storage-foot"><small data-testid="storage-checked">{data?.checked_at?'Jaancha: '+ago(data.checked_at):''}{set&&sb.bucket?` · bucket ${sb.bucket}`:''}</small><button type="button" onClick={()=>{load(true);machine.load();}} disabled={busy} data-testid="storage-check-now">{busy?<Loader2 size={13} className="spin"/>:<RefreshCw size={13}/>}Abhi check karo</button></div>
  {set&&<LegacyMove/>}
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
 if(!data||!LABEL[data.mode])return null;
 const bigBad=(data.mode==='supabase'||data.mode==='slow')&&data.big?.state==='bad';
 const tone=bigBad?'warn':{supabase:'ok',slow:'warn',waiting:'warn',emergent:'warn',down:'error'}[data.mode];
 const text=bigBad?BIG_BAD:UPLOAD[data.mode]||(data.mode==='emergent'?(data.supabase?.configured===false?NOT_SET:'Nayi files Emergent storage mein save ho rahi hain.')+' Upload aaram se kar sakte hain.'
  :'Dono storage abhi jawab nahi de rahe. Upload ke baad book save nahi ho payegi. Thodi der baad upload kijiye.');
 return <p className={'admin-note '+tone} data-testid="upload-storage-notice">{text}</p>;
}
