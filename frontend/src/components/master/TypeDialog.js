import React,{useEffect,useState} from 'react';
import {Loader2} from 'lucide-react';
import {Dialog,DialogContent,DialogTitle,DialogDescription} from '../ui/dialog';
import {Button} from '../ui/button';
import {Input} from '../ui/input';
import {post,patch} from '../../lib/api';
import {invalidateCatalog} from '../../lib/catalog';
import {Field} from './MasterShared';
import {toast} from 'sonner';

const KINDS=[['pyq','PYQ','Papers by year','PYQ Papers'],['mocks','Mock','A straight list of full papers','Mock Tests'],['chapters','Chapter-wise','Subject › chapter','Chapter-wise Tests'],['aits','All India Test Series','One paper a day with rank and its own Home card','All India Test Series'],['custom','Own type','You name it, for example Revision Tests','']];
const RULES={'jee-main':[180,4,-1],bitsat:[180,3,-1],comedk:[180,1,0]};

function Marks({v,set}){
 return <div className="master-field-row">
  <Field label="Time (minutes)" id="type-minutes"><Input id="type-minutes" type="number" min={1} max={1440} value={v.minutes} onChange={e=>set({...v,minutes:e.target.value})} data-testid="type-minutes"/></Field>
  <Field label="Marks if right" id="type-correct"><Input id="type-correct" type="number" step="0.25" min={0.25} value={v.correct} onChange={e=>set({...v,correct:e.target.value})} data-testid="type-correct"/></Field>
  <Field label="Marks if wrong" id="type-wrong"><Input id="type-wrong" type="number" step="0.25" max={0} value={v.wrong} onChange={e=>set({...v,wrong:e.target.value})} data-testid="type-wrong"/></Field>
 </div>;
}
const nums=v=>({minutes:Math.round(Number(v.minutes)),correct:Number(v.correct),wrong:Number(v.wrong)});
const validMarks=v=>Number(v.minutes)>0&&Number(v.correct)>0&&Number(v.wrong)<=0;

export function TypeDialog({open,onClose,exam,onCreated}){
 const taken=new Set(exam.sections.map(s=>s.kind));
 const base=RULES[exam.slug]||[180,4,-1];
 const [kind,setKind]=useState(''),[name,setName]=useState(''),[layout,setLayout]=useState('list'),[rules,setRules]=useState({minutes:base[0],correct:base[1],wrong:base[2]});
 const [series,setSeries]=useState({first_date:'',days:30,open_time:'00:01',last_start:'20:59'}),[busy,setBusy]=useState(false);
 useEffect(()=>{if(open){setKind('');setName('');}},[open]);
 function pick(k){setKind(k);const d=KINDS.find(x=>x[0]===k);setName(d[3]);setRules({minutes:k==='chapters'?60:base[0],correct:base[1],wrong:base[2]});}
 const ok=kind&&name.trim().length>=2&&validMarks(rules)&&(kind!=='aits'||(series.first_date&&Number(series.days)>0));
 async function save(){setBusy(true);try{
  const s=await post(`/admin/catalog/exams/${exam.slug}/sections`,{name:name.trim(),description:'',layout:kind==='chapters'?'chapters':kind==='custom'?layout:'list',kind,...nums(rules),
   ...(kind==='aits'?{first_date:series.first_date,days:Math.round(Number(series.days)),open_time:series.open_time,last_start:series.last_start}:{})});
  invalidateCatalog();toast.success(`${s.name} added to ${exam.name}. Students see it once it has a live mock.`);onCreated(s);onClose();
 }catch(e){toast.error(e.message);}finally{setBusy(false);}}
 return <Dialog open={open} onOpenChange={v=>!v&&onClose()}><DialogContent className="tejas-dialog admin-dialog master-dialog" data-testid="type-dialog">
  <DialogTitle>Add a mock type to {exam.name}</DialogTitle><DialogDescription>PYQ, Mock, Chapter-wise and All India Test Series come once per exam. Add as many of your own types as you like.</DialogDescription>
  <div className="master-kind-grid" role="radiogroup">{KINDS.map(([k,l,h])=>{const off=k!=='custom'&&taken.has(k);return <button type="button" role="radio" aria-checked={kind===k} key={k} disabled={off} className={'admin-choice'+(kind===k?' is-picked':'')} onClick={()=>pick(k)} data-testid={'type-kind-'+k}><strong>{l}</strong><small>{off?'Already in this exam':h}</small></button>;})}</div>
  {kind&&<form className="admin-form" onSubmit={e=>{e.preventDefault();if(ok&&!busy)save();}}>
   <Field label="Name students see" id="type-name"><Input id="type-name" value={name} maxLength={60} onChange={e=>setName(e.target.value)} data-testid="type-name"/></Field>
   {kind==='custom'&&<fieldset className="admin-layouts"><legend>How mocks are listed</legend>{[['list','Straight list','Like Mock Tests'],['chapters','Subject › chapter','Like Chapter-wise']].map(([v,l,h])=><label key={v} className={layout===v?'is-picked':''} data-testid={'type-layout-'+v}><input type="radio" name="type-layout" checked={layout===v} onChange={()=>setLayout(v)}/><strong>{l}</strong><small>{h}</small></label>)}</fieldset>}
   <p className="master-hint">Default time and marks for new mocks here. A PDF that prints its own rules keeps them.</p>
   <Marks v={rules} set={setRules}/>
   {kind==='aits'&&<div className="master-field-row">
    <Field label="First day" id="series-first"><Input id="series-first" type="date" value={series.first_date} onChange={e=>setSeries({...series,first_date:e.target.value})} data-testid="series-first-date"/></Field>
    <Field label="Number of days" id="series-days"><Input id="series-days" type="number" min={1} max={366} value={series.days} onChange={e=>setSeries({...series,days:e.target.value})} data-testid="series-days"/></Field>
    <Field label="Opens daily (IST)" id="series-open"><Input id="series-open" type="time" value={series.open_time} onChange={e=>setSeries({...series,open_time:e.target.value})} data-testid="series-open-time"/></Field>
    <Field label="Last start (IST)" id="series-last"><Input id="series-last" type="time" value={series.last_start} onChange={e=>setSeries({...series,last_start:e.target.value})} data-testid="series-last-start"/></Field>
   </div>}
   <div className="button-row"><Button type="button" variant="outline" onClick={onClose} data-testid="type-dialog-cancel">Cancel</Button><Button type="submit" disabled={!ok||busy} data-testid="type-dialog-save">{busy&&<Loader2 size={16} className="spin"/>}Add mock type</Button></div>
  </form>}
 </DialogContent></Dialog>;
}

export function TypeSettings({open,onClose,type,onSaved}){
 const d=type?.defaults||{minutes:180,correct:4,wrong:-1};
 const [name,setName]=useState(''),[rules,setRules]=useState(d),[busy,setBusy]=useState(false);
 useEffect(()=>{if(open&&type){setName(type.name);setRules(type.defaults||{minutes:180,correct:4,wrong:-1});}},[open,type]);
 async function save(){setBusy(true);try{await patch('/admin/catalog/sections/'+type.id,{...(name.trim()!==type.name?{name:name.trim()}:{}),...nums(rules)});invalidateCatalog();toast.success('Mock type saved.');onSaved();onClose();}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 return <Dialog open={open} onOpenChange={v=>!v&&onClose()}><DialogContent className="tejas-dialog admin-dialog" data-testid="type-settings-dialog">
  <DialogTitle>{type?.name}</DialogTitle><DialogDescription>Name and the default time and marks for new mocks. Mocks already made keep their own.</DialogDescription>
  <form className="admin-form" onSubmit={e=>{e.preventDefault();if(!busy)save();}}>
   <Field label="Name students see" id="type-settings-name"><Input id="type-settings-name" value={name} maxLength={60} onChange={e=>setName(e.target.value)} data-testid="type-settings-name"/></Field>
   <Marks v={rules} set={setRules}/>
   <div className="button-row"><Button type="button" variant="outline" onClick={onClose} data-testid="type-settings-cancel">Cancel</Button><Button type="submit" disabled={busy||name.trim().length<2||!validMarks(rules)} data-testid="type-settings-save">Save</Button></div>
  </form>
 </DialogContent></Dialog>;
}
