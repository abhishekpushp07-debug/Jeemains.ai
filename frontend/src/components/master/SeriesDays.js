import React,{useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {CalendarDays,ListOrdered,X,Settings2,PencilLine,Wrench,Eraser} from 'lucide-react';
import {api,post,put} from '../../lib/api';
import {Button} from '../ui/button';
import {Input} from '../ui/input';
import {Switch} from '../ui/switch';
import {Skeleton} from '../ui/skeleton';
import {Select,SelectTrigger,SelectValue,SelectContent,SelectItem} from '../ui/select';
import {Dialog,DialogContent,DialogTitle,DialogDescription} from '../ui/dialog';
import {ErrorBox} from '../Shared';
import {StatusChip,ConfirmDialog} from '../admin/AdminShared';
import {Field,dayIST,clock,plural} from './MasterShared';
import {toast} from 'sonner';

const STATE={upcoming:['Upcoming','scheduled'],live:['Open today','live'],start_closed:['Starts closed','live'],ended:['Day ended','ended'],archive:['Practice','hidden']};

function Settings({open,onClose,data,onSaved}){
 const [v,setV]=useState({});
 useEffect(()=>{if(open)setV({first_date:data.first_date,days:data.total,open_time:data.open_time,last_start:data.last_start,title:data.title});},[open,data]);
 async function save(){try{const r=await put('/admin/master/series/'+data.id,{title:v.title.trim(),first_date:v.first_date,days:Math.round(Number(v.days)),open_time:v.open_time,last_start:v.last_start});toast.success(r.message);onSaved();onClose();}catch(e){toast.error(e.message);}}
 const set=k=>e=>setV({...v,[k]:e.target.value});
 return <Dialog open={open} onOpenChange={x=>!x&&onClose()}><DialogContent className="tejas-dialog admin-dialog" data-testid="series-settings-dialog">
  <DialogTitle>Series dates and times</DialogTitle><DialogDescription>Days that have opened never change. Future days follow the new dates and times.</DialogDescription>
  <form className="admin-form" onSubmit={e=>{e.preventDefault();save();}}>
   <Field label="Series name" id="ss-title"><Input id="ss-title" value={v.title||''} maxLength={80} onChange={set('title')} data-testid="series-settings-title"/></Field>
   <div className="master-field-row">
    <Field label="First day" id="ss-first"><Input id="ss-first" type="date" value={v.first_date||''} onChange={set('first_date')} data-testid="series-settings-first"/></Field>
    <Field label="Number of days" id="ss-days"><Input id="ss-days" type="number" min={1} max={366} value={v.days||''} onChange={set('days')} data-testid="series-settings-days"/></Field>
    <Field label="Opens daily (IST)" id="ss-open"><Input id="ss-open" type="time" value={v.open_time||''} onChange={set('open_time')} data-testid="series-settings-open"/></Field>
    <Field label="Last start (IST)" id="ss-last"><Input id="ss-last" type="time" value={v.last_start||''} onChange={set('last_start')} data-testid="series-settings-last"/></Field>
   </div>
   <div className="button-row"><Button type="button" variant="outline" onClick={onClose} data-testid="series-settings-cancel">Cancel</Button><Button type="submit" data-testid="series-settings-save">Save</Button></div>
  </form>
 </DialogContent></Dialog>;
}

function Paper({c,free,busy,onAssign}){
 const link=c.kind==='written'?'/super-admin/write/'+c.id:c.kind==='book_mock'?`/super-admin/fix/${c.book_id}/${c.id}${c.held?'':'?all=1'}`:null;
 return <li className="admin-row" data-testid={'series-paper-'+c.id}>
  <div className="admin-row-main"><strong>{c.title}</strong><small>{[c.book,plural(c.count,'question'),c.kind==='written'?'Written':c.kind==='set'?'Built, no day':'From PDF'].filter(Boolean).join(' · ')}</small>{c.problem&&<p className="admin-reason">{c.problem}</p>}</div>
  {link&&<Button asChild size="sm" variant={c.held||c.problem?'default':'outline'}><Link to={link} data-testid={'series-paper-open-'+c.id}>{c.held?<><Wrench size={15}/>Fix</>:<><PencilLine size={15}/>Edit</>}</Link></Button>}
  {!c.problem&&free.length>0&&<Select value="" onValueChange={d=>onAssign(c,d)} disabled={busy}><SelectTrigger className="admin-move-select" aria-label={'Give '+c.title+' a day'} data-testid={'series-paper-day-'+c.id}><SelectValue placeholder="Give a day…"/></SelectTrigger><SelectContent>{free.map(s=><SelectItem key={s.date} value={s.date}>Day {s.day} · {dayIST(s.date)}</SelectItem>)}</SelectContent></Select>}
 </li>;
}

export function SeriesDays({section,reloadKey,onChanged}){
 const [data,setData]=useState(null),[error,setError]=useState(''),[reload,setReload]=useState(0),[busy,setBusy]=useState(false),[dialog,setDialog]=useState(null);
 useEffect(()=>{api('/admin/master/series/'+section.series_id).then(d=>{setData(d);setError('');}).catch(e=>setError(e.message));},[section.series_id,reload,reloadKey]);
 async function run(fn){setBusy(true);try{const r=await fn();toast.success(r.message||'Saved.');setReload(n=>n+1);onChanged?.();}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 if(error)return <ErrorBox error={error} retry={()=>setReload(n=>n+1)}/>;
 if(!data)return <Skeleton className="h-64"/>;
 const free=data.slots.filter(s=>!s.paper&&!s.opened),assigned=data.slots.filter(s=>s.paper).length;
 return <>
  <section className="admin-panel master-series-head" data-testid="series-settings">
   <div className="admin-panel-head"><div><h2>{data.title}</h2><p data-testid="series-dates"><CalendarDays size={15}/>{dayIST(data.first_date)} – {dayIST(data.last_date)} · {data.total} days · opens {clock(data.open_time)} · last start {clock(data.last_start)} IST</p></div>
    <div className="admin-actions">{!data.builtin&&<Button variant="outline" onClick={()=>setDialog('settings')} data-testid="series-edit-settings"><Settings2 size={16}/>Dates & times</Button>}</div></div>
   {data.builtin?<p className="admin-note" data-testid="series-builtin-note">The JEE Main series keeps its 62 days and its Home banner exactly as students know it. Give its future days papers here.</p>
    :<label className="master-switch-row" data-testid="series-home-label"><Switch checked={data.shown} disabled={busy} onCheckedChange={v=>run(()=>put('/admin/master/series/'+data.id,{shown:v}))} data-testid="series-show-home"/><span><strong>Show on Home</strong><small>{data.shown?(data.exam_shown?'Its own card is on Home and the opening page.':`Card is on, but ${data.exam.name} itself is still hidden from students.`):'Students do not see this series yet.'}</small></span></label>}
   {data.pattern?.count&&<p className="master-hint">Every paper: {data.pattern.count} questions · {data.pattern.minutes} min · +{data.pattern.correct} / {data.pattern.wrong}.</p>}
  </section>
  <section className="admin-panel" data-testid="series-papers">
   <div className="admin-panel-head"><div><h2>Papers without a day ({data.candidates.length})</h2><p>Made with Upload PDF or Write above. A paper is never shown before its day.</p></div>
    <div className="admin-actions"><Button disabled={busy||!free.length||!data.candidates.some(c=>!c.problem)} onClick={()=>run(()=>post(`/admin/master/series/${data.id}/fill`))} data-testid="series-fill"><ListOrdered size={16}/>Fill days in order</Button></div></div>
   {data.candidates.length?<ul className="admin-list">{data.candidates.map(c=><Paper key={c.kind+c.id} c={c} free={free} busy={busy} onAssign={(c,date)=>run(()=>post(`/admin/master/series/${data.id}/assign`,{kind:c.kind,id:c.id,date}))}/>)}</ul>:<p className="admin-empty" data-testid="series-no-papers">Every paper has a day. Upload or write more.</p>}
  </section>
  <section className="admin-panel" data-testid="series-days">
   <div className="admin-panel-head"><div><h2>Days</h2><p>{assigned} of {data.total} days have a paper.</p></div><Button variant="outline" disabled={busy||!data.slots.some(s=>s.paper&&!s.opened)} onClick={()=>setDialog('clear')} data-testid="series-clear"><Eraser size={16}/>Free all future days</Button></div>
   <ol className="master-days" data-testid="series-day-list">{data.slots.map(s=>{const [label,tone]=STATE[s.state]||STATE.upcoming;return <li key={s.date} className={'master-day'+(s.paper?' has-paper':'')+(s.opened?' is-opened':'')} data-testid={'series-day-'+s.day}>
    <span className="master-day-num">Day {s.day}</span><span className="master-day-date">{dayIST(s.date)}</span>
    <strong className="master-day-title">{s.paper?s.paper.title:'Free'}{s.paper?.pending&&<small> · being prepared</small>}</strong>
    {s.paper?.kind==='set'&&<label className={'master-live-switch'+(s.paper.off?'':' is-on')}><Switch checked={!s.paper.off} disabled={busy} onCheckedChange={v=>run(()=>post(`/admin/master/series/${data.id}/live`,{id:s.paper.id,live:v}))} aria-label={(s.paper.off?'Make Live ':'Switch off ')+'day '+s.day} data-testid={'series-day-live-'+s.day}/><span data-testid={'series-day-live-word-'+s.day}>{s.paper.off?'Off':'Live'}</span></label>}
    <StatusChip state={tone==='live'?'live':tone} label={label} testId={'series-day-state-'+s.day}/>
    {s.paper&&!s.opened&&<Button size="icon" variant="ghost" disabled={busy} aria-label={'Free day '+s.day} onClick={()=>run(()=>post(`/admin/master/series/${data.id}/unassign`,{kind:s.paper.kind,id:s.paper.id}))} data-testid={'series-day-free-'+s.day}><X size={15}/></Button>}
   </li>;})}</ol>
  </section>
  <Settings open={dialog==='settings'} onClose={()=>setDialog(null)} data={data} onSaved={()=>setReload(n=>n+1)}/>
  <ConfirmDialog open={dialog==='clear'} onClose={()=>setDialog(null)} busy={busy} testId="series-clear-confirm" title="Free every future day?" text="Papers go back to the list without a day. Opened days do not change." button="Free future days" onConfirm={()=>{setDialog(null);run(()=>post(`/admin/master/series/${data.id}/clear`));}}/>
 </>;
}
