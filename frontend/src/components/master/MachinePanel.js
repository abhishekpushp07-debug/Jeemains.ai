import React,{useCallback,useEffect,useState} from 'react';
import {RotateCw,Loader2} from 'lucide-react';
import {toast} from 'sonner';
import {api,post} from '../../lib/api';
import {RetryStorageButton,STORAGE_EVENT} from './UploadProgress';

const GB=1024*1024*1024;
const gb=b=>`${(b/GB).toFixed(1)} GB`;
const KIND={book_step:'PDF padhna',ai_solution:'AI solution',grade:'grading',regrade:'regrade',report:'report',extract:'extract',smart_prepare:'import',smart_page:'import',cohort:'rank',class_stats:'class ginti'};
export const lowDisk=d=>!!d&&d.disk.total>0&&d.disk.free<d.disk.total*0.05;
const SAYS=[[/^Processing interrupted/i,'Kaam beech mein ruk gaya. Dobara chalao dabane par save hue page se aage chalega; dobara upload nahi karna.'],[/^Book processing lease expired|^This book changed/i,'Ek aur kaam isi PDF par chal raha tha. Dobara chalao dabaiye; save hua kaam rakha gaya hai.']];
const said=t=>(SAYS.find(([re])=>re.test(t||''))||[])[1]||t;
export const ago=t=>{if(!t)return '';const s=Math.max(0,Math.round(Date.now()/1000-t));return s<60?`${s} s pehle`:s<3600?`${Math.round(s/60)} min pehle`:s<172800?`${Math.round(s/3600)} ghante pehle`:`${Math.round(s/86400)} din pehle`;};
const STORE={supabase:'Supabase',emergent:'Emergent'};
const ROUTE={small:'chhoti file ka raasta',big:'badi file ka raasta',read:'padhna',save:'save karna',check:'jaanch'};

// The last 20 storage failures: when, which file, which store, which route, why. Open by itself when the newest is under an hour old.
function StorageErrors({rows}){
 if(!rows.length)return null;
 return <details className="machine-errors" open={Date.now()/1000-rows[0].at<3600} data-testid="machine-storage-errors">
  <summary data-testid="machine-storage-errors-toggle">Storage ki aakhri {rows.length} galtiyan</summary>
  <ul className="machine-error-list">{rows.map((e,i)=><li key={e.at+'-'+i} data-testid={'machine-storage-error-'+i}>
   <strong>{e.file}</strong><small>{ago(e.at)} · {STORE[e.store]||e.store} · {ROUTE[e.route]||e.route}{e.n>1?` · ${e.n} baar`:''}</small><span>{e.reason}</span>
  </li>)}</ul>
 </details>;
}

// Asks the server once a minute while the tab is visible, so the top bar can light up when something needs the owner.
export function useMachineStatus(){
 const [data,setData]=useState(null);
 const load=useCallback(()=>api('/admin/machine/status').then(setData).catch(()=>{}),[]);
 useEffect(()=>{load();const t=setInterval(()=>{if(document.visibilityState==='visible')load();},60000);window.addEventListener(STORAGE_EVENT,load);return()=>{clearInterval(t);window.removeEventListener(STORAGE_EVENT,load);};},[load]);
 return {data,load};
}

function Line({ok,label,value,testId}){
 return <div className="machine-row" data-testid={testId}><i className={'storage-dot '+(ok?'ok':'bad')} aria-hidden="true"/><strong>{label}</strong><em className="machine-value" data-testid={testId+'-value'}>{value}</em></div>;
}

function BookLine({b,stuck,busy,onRetry}){
 return <li className="machine-book" data-testid={(stuck?'machine-stuck-':'machine-failed-')+b.id}>
  <div className="machine-book-main"><strong>{b.title||'Bina naam ki PDF'}</strong><small>{stuck?`${b.read_pages} / ${b.pages} page · ${b.minutes} min se ruki hai`:(said(b.message)||'Kaam beech mein ruk gaya.')}</small></div>
  <button type="button" className="machine-retry" disabled={busy} onClick={()=>onRetry(b)} data-testid={'machine-retry-'+b.id}>{busy?<Loader2 size={14} className="spin" aria-hidden="true"/>:<RotateCw size={14} aria-hidden="true"/>}Dobara chalao</button>
 </li>;
}

// A file Supabase keeps returning ("Atki hai"): only it stopped; it says why and can be tried again at once.
function StuckFile({b,busy,onRetry}){
 const hang=b.kind==='hang',what=b.mock?`"${b.mock}"${b.more?` aur ${b.more} doosre mock ki pictures`:' ki ek picture'}`:'Yeh PDF';
 return <li className="machine-book" data-testid={(hang?'machine-hung-':'machine-storage-stuck-')+b.id}>
  <div className="machine-book-main"><strong>{b.title||'Bina naam ki PDF'}</strong><small>Atki hai · {b.waiting_minutes} min se. {hang?'Is PDF ka kaam baar-baar beech mein latak gaya, isliye machine ne ise rok diya.':`${what} Supabase mein nahi ja rahi.`}{b.reason?` Wajah: ${b.reason}.`:''} {hang?(b.next||''):'Har 15 minute mein apne aap phir koshish hoti hai.'}</small></div>
  <button type="button" className="machine-retry" disabled={busy} onClick={()=>onRetry(b)} data-testid={'machine-retry-'+b.id}>{busy?<Loader2 size={14} className="spin" aria-hidden="true"/>:<RotateCw size={14} aria-hidden="true"/>}Dobara chalao</button>
 </li>;
}

function Waiting({data,onReload}){
 const books=data.storage_waiting||[];
 if(!books.length&&!data.storage_waiting_jobs)return null;
 return <div className="machine-waiting" data-testid="machine-waiting-list">
  <ul className="machine-books">{books.map(b=><li key={b.id} className="machine-book is-waiting" data-testid={'machine-waiting-'+b.id}>
   <div className="machine-book-main"><strong>{b.title||'Bina naam ki PDF'}</strong><small>{b.pages?`${b.read_pages} / ${b.pages} page · `:''}{b.waiting_minutes} min se Supabase ka intezaar. File surakshit hai, apne aap aage chalegi.{b.reason?` Wajah: ${b.reason}.`:''}</small></div>
  </li>)}</ul>
  <RetryStorageButton onDone={onReload} testId="machine-storage-retry"/>
 </div>;
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
 const c=data.cron,books=[...data.stuck.map(b=>[b,true]),...data.failed_books.map(b=>[b,false])],returned=data.storage_stuck||[];
 const hung=data.hung_books||[],hangs=data.step_hangs||{day:0},lastHang=hangs.last;
 const errs=data.storage_errors||[],errDay=errs.length>0&&Date.now()/1000-errs[0].at<86400;
 const cron=!c.configured?'set nahi hai':c.minutes_ago==null?'abhi tak nahi chali':`${c.minutes_ago} min pehle chali`;
 const kinds=Object.entries(data.failed_jobs||{}).map(([k,n])=>`${KIND[k]||k} ${n}`).join(' · ');
 const alert=data.attention||lowDisk(data);
 return <section className="machine-panel" data-testid="machine-panel">
  <h3 className={alert?'is-alert':''} data-testid="machine-title">{alert?'Machine: dhyan dijiye':'Machine: sab theek hai'}</h3>
  <Line ok={!c.late} label="Scheduled jaanch" value={cron} testId="machine-cron"/>
  <Line ok={!data.failed_total} label="Fail kaam (24 ghante)" value={data.failed_total?`${data.failed_total} · ${kinds}`:'0'} testId="machine-failed-jobs"/>
  <Line ok={!(data.storage_waiting||[]).length&&!data.storage_waiting_jobs} label="Supabase ka intezaar" value={`${(data.storage_waiting||[]).length} PDF · ${data.storage_waiting_jobs||0} kaam`} testId="machine-storage-waiting"/>
  <Line ok={!returned.length} label="Supabase mein atki file" value={String(returned.length)} testId="machine-storage-stuck"/>
  <Line ok={!data.stuck.length} label="15 min se atki PDF" value={String(data.stuck.length)} testId="machine-stuck"/>
  <Line ok={!hangs.day&&!hung.length} label="Latke kadam (24 ghante)" value={String(hangs.day||0)} testId="machine-step-hangs"/>
  <Line ok={!data.failed_books.length} label="Fail PDF" value={String(data.failed_books.length)} testId="machine-failed"/>
  <Line ok={!data.delete_pending?.count} label="Delete ki safai baaki" value={String(data.delete_pending?.count||0)} testId="machine-delete-pending"/>
  {(data.delete_pending?.items||[]).filter(x=>x.error).slice(0,1).map(x=><p key={x.title} className="storage-meta" data-testid="machine-delete-note">Safai ruki hai: {x.title} · {x.error} Har 15 minute mein apne aap phir koshish hoti hai; row list se hat chuki hai.</p>)}
  <Line ok={!errDay} label="Storage ki galtiyan (aakhri 20)" value={errs.length?`${errs.length} · aakhri ${ago(errs[0].at)}`:'0'} testId="machine-storage-errors-count"/>
  <StorageErrors rows={errs}/>
  <Line ok={!lowDisk(data)} label="Disk khali" value={`${gb(data.disk.free)} / ${gb(data.disk.total)}`} testId="machine-disk"/>
  <Waiting data={data} onReload={onReload}/>
  {returned.length>0&&<ul className="machine-books" data-testid="machine-storage-stuck-list">{returned.map(b=><StuckFile key={b.id} b={b} busy={busy===b.id} onRetry={retry}/>)}</ul>}
  {hung.length>0&&<ul className="machine-books" data-testid="machine-hung-list">{hung.map(b=><StuckFile key={b.id} b={b} busy={busy===b.id} onRetry={retry}/>)}</ul>}
  {lastHang&&<p className="storage-meta" data-testid="machine-step-hang-last">Aakhri latka kadam: {lastHang.title||'Bina naam ki PDF'} · machine ne use chhod kar save hui jagah se dobara chalaya. Jagah: {lastHang.where}</p>}
  {books.length>0&&<ul className="machine-books" data-testid="machine-book-list">{books.map(([b,stuck])=><BookLine key={b.id} b={b} stuck={stuck} busy={busy===b.id} onRetry={retry}/>)}</ul>}
  <p className="storage-meta" data-testid="machine-files">Kul save hui file: {data.files_saved.toLocaleString('en-IN')}</p>
 </section>;
}
