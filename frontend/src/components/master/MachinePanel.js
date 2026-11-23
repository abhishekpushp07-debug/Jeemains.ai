import React,{useCallback,useEffect,useState} from 'react';
import {RotateCw,Loader2} from 'lucide-react';
import {toast} from 'sonner';
import {api,post} from '../../lib/api';

const GB=1024*1024*1024;
const gb=b=>`${(b/GB).toFixed(1)} GB`;
const KIND={book_step:'PDF padhna',ai_solution:'AI solution',grade:'grading',regrade:'regrade',report:'report',extract:'extract',smart_prepare:'import',smart_page:'import',cohort:'rank',class_stats:'class ginti'};
export const lowDisk=d=>!!d&&d.disk.total>0&&d.disk.free<d.disk.total*0.05;

// Asks the server once a minute while the tab is visible, so the top bar can light up when something needs the owner.
export function useMachineStatus(){
 const [data,setData]=useState(null);
 const load=useCallback(()=>api('/admin/machine/status').then(setData).catch(()=>{}),[]);
 useEffect(()=>{load();const t=setInterval(()=>{if(document.visibilityState==='visible')load();},60000);return()=>clearInterval(t);},[load]);
 return {data,load};
}

function Line({ok,label,value,testId}){
 return <div className="machine-row" data-testid={testId}><i className={'storage-dot '+(ok?'ok':'bad')} aria-hidden="true"/><strong>{label}</strong><em className="machine-value" data-testid={testId+'-value'}>{value}</em></div>;
}

function BookLine({b,stuck,busy,onRetry}){
 return <li className="machine-book" data-testid={(stuck?'machine-stuck-':'machine-failed-')+b.id}>
  <div className="machine-book-main"><strong>{b.title||'Bina naam ki PDF'}</strong><small>{stuck?`${b.read_pages} / ${b.pages} page · ${b.minutes} min se ruki hai`:(b.message||'Kaam beech mein ruk gaya.')}</small></div>
  <button type="button" className="machine-retry" disabled={busy} onClick={()=>onRetry(b)} data-testid={'machine-retry-'+b.id}>{busy?<Loader2 size={14} className="spin" aria-hidden="true"/>:<RotateCw size={14} aria-hidden="true"/>}Dobara chalao</button>
 </li>;
}

export function MachinePanel({data,onReload}){
 const [busy,setBusy]=useState('');
 if(!data)return <p className="storage-meta" data-testid="machine-loading">Machine ki haalat check ho rahi hai…</p>;
 async function retry(b){
  setBusy(b.id);
  try{await post(`/admin/books/${b.id}/control`,{revision:b.revision,action:'retry'});toast.success('Phir se shuru. Jo page padhe ja chuke hain woh rakhe gaye hain.');}
  catch(e){toast.error(e.message);}
  finally{setBusy('');onReload();}
 }
 const c=data.cron,books=[...data.stuck.map(b=>[b,true]),...data.failed_books.map(b=>[b,false])];
 const cron=!c.configured?'set nahi hai':c.minutes_ago==null?'abhi tak nahi chali':`${c.minutes_ago} min pehle chali`;
 const kinds=Object.entries(data.failed_jobs||{}).map(([k,n])=>`${KIND[k]||k} ${n}`).join(' · ');
 const alert=data.attention||lowDisk(data);
 return <section className="machine-panel" data-testid="machine-panel">
  <h3 className={alert?'is-alert':''} data-testid="machine-title">{alert?'Machine: dhyan dijiye':'Machine: sab theek hai'}</h3>
  <Line ok={!c.late} label="Scheduled jaanch" value={cron} testId="machine-cron"/>
  <Line ok={!data.failed_total} label="Fail kaam (24 ghante)" value={data.failed_total?`${data.failed_total} · ${kinds}`:'0'} testId="machine-failed-jobs"/>
  <Line ok={!data.stuck.length} label="15 min se atki PDF" value={String(data.stuck.length)} testId="machine-stuck"/>
  <Line ok={!data.failed_books.length} label="Fail PDF" value={String(data.failed_books.length)} testId="machine-failed"/>
  <Line ok={!lowDisk(data)} label="Disk khali" value={`${gb(data.disk.free)} / ${gb(data.disk.total)}`} testId="machine-disk"/>
  {books.length>0&&<ul className="machine-books" data-testid="machine-book-list">{books.map(([b,stuck])=><BookLine key={b.id} b={b} stuck={stuck} busy={busy===b.id} onRetry={retry}/>)}</ul>}
  <p className="storage-meta" data-testid="machine-files">Kul save hui file: {data.files_saved.toLocaleString('en-IN')}</p>
 </section>;
}
