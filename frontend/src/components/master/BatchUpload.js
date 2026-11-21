import React from 'react';
import {CheckCircle2,Loader2,XCircle,Clock3} from 'lucide-react';
import {sendBook} from './uploadBook';

export const yearOf=name=>(String(name).match(/(?:19|20)\d{2}/)||[''])[0];
export const newRows=files=>files.map((file,i)=>({key:i+':'+file.name,file,year:yearOf(file.name),state:'waiting',msg:'',progress:0}));

// Many PDFs, one after another: each becomes its own upload, and one failing never stops the rest.
export async function runBatch(rows,setRows,{sectionId,subject,pyq,stopped}){
 const update=(key,change)=>setRows(list=>list.map(r=>r.key===key?{...r,...change}:r));
 let ok=0,failed=0,paused=false;
 for(const r of rows){
  if(r.state==='done'){ok+=1;continue;}
  if(stopped.current)break;
  update(r.key,{state:'sending',msg:'Starting…',progress:0});
  try{
   await sendBook({file:r.file,title:r.file.name.replace(/\.pdf$/i,'').slice(0,160),sectionId,replace:'',year:pyq?Number(r.year):null,subject,stopped,
    onProgress:(msg,progress)=>update(r.key,{msg,progress})});
   update(r.key,{state:'done',msg:'Sent. Reading in the background.',progress:1});ok+=1;
  }catch(e){
   // A pause is not a failure: the parts already sent are kept and the next Upload carries on from them.
   if(stopped.current){update(r.key,{state:'waiting',msg:'Paused. Press Upload to carry on from the parts already sent.'});paused=true;break;}
   update(r.key,{state:'failed',msg:e.message});failed+=1;}
 }
 return {ok,failed,paused};
}

const ICON={waiting:Clock3,sending:Loader2,done:CheckCircle2,failed:XCircle};
export function BatchRows({rows,setRows,pyq,busy}){
 return <ol className="batch-list" data-testid="upload-batch-list">{rows.map((r,i)=>{const I=ICON[r.state];return <li key={r.key} className={'batch-row is-'+r.state} data-testid={'upload-batch-row-'+i}>
  <I size={16} className={r.state==='sending'?'spin':''} aria-hidden="true"/>
  <div className="batch-main"><strong>{r.file.name}</strong><small data-testid={'upload-batch-status-'+i}>{r.msg||`${(r.file.size/1024/1024).toFixed(1)} MB · waiting`}</small>{r.state==='sending'&&<progress value={r.progress} max={1}/>}</div>
  {pyq&&<input className="batch-year" inputMode="numeric" maxLength={4} value={r.year} placeholder="Year" disabled={busy||r.state==='done'} aria-label={'Year of '+r.file.name}
   onChange={e=>{const year=e.target.value.replace(/\D/g,'');setRows(list=>list.map(x=>x.key===r.key?{...x,year}:x));}} data-testid={'upload-batch-year-'+i}/>}
 </li>;})}</ol>;
}
