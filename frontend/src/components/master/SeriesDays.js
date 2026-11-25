import React,{useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {CalendarDays,ListOrdered,X,Settings2,PencilLine,Wrench,Eraser,Trash2} from 'lucide-react';
import {DeleteUploadDialog} from './DeleteUploadDialog';
import {api,post,put} from '../../lib/api';
import {Button} from '../ui/button';
import {Input} from '../ui/input';
import {Switch} from '../ui/switch';
import {Skeleton} from '../ui/skeleton';
import {Select,SelectTrigger,SelectValue,SelectContent,SelectItem} from '../ui/select';
import {Dialog,DialogContent,DialogTitle,DialogDescription} from '../ui/dialog';
import {ErrorBox} from '../Shared';
import {StatusChip,ConfirmDialog} from '../admin/AdminShared';
import {Field,dayIST,clock} from './MasterShared';
import {toast} from 'sonner';

const STATE={upcoming:['Aane wala','scheduled'],live:['Aaj khula','live'],start_closed:['Start band','live'],ended:['Din khatam','ended'],archive:['Practice','hidden']};

function Settings({open,onClose,data,onSaved}){
 const [v,setV]=useState({});
 useEffect(()=>{if(open)setV({first_date:data.first_date,days:data.total,open_time:data.open_time,last_start:data.last_start,title:data.title});},[open,data]);
 async function save(){try{const r=await put('/admin/master/series/'+data.id,{title:v.title.trim(),first_date:v.first_date,days:Math.round(Number(v.days)),open_time:v.open_time,last_start:v.last_start});toast.success(r.message);onSaved();onClose();}catch(e){toast.error(e.message);}}
 const set=k=>e=>setV({...v,[k]:e.target.value});
 return <Dialog open={open} onOpenChange={x=>!x&&onClose()}><DialogContent className="tejas-dialog admin-dialog" data-testid="series-settings-dialog">
  <DialogTitle>Series ki dates aur time</DialogTitle><DialogDescription>Jo din khul chuke hain woh kabhi nahi badalte. Aage ke din nayi dates aur time follow karenge.</DialogDescription>
  <form className="admin-form" onSubmit={e=>{e.preventDefault();save();}}>
   <Field label="Series ka naam" id="ss-title"><Input id="ss-title" value={v.title||''} maxLength={80} onChange={set('title')} data-testid="series-settings-title"/></Field>
   <div className="master-field-row">
    <Field label="Pehla din" id="ss-first"><Input id="ss-first" type="date" value={v.first_date||''} onChange={set('first_date')} data-testid="series-settings-first"/></Field>
    <Field label="Kitne din" id="ss-days"><Input id="ss-days" type="number" min={1} max={366} value={v.days||''} onChange={set('days')} data-testid="series-settings-days"/></Field>
    <Field label="Roz khulega (IST)" id="ss-open"><Input id="ss-open" type="time" value={v.open_time||''} onChange={set('open_time')} data-testid="series-settings-open"/></Field>
    <Field label="Aakhri start (IST)" id="ss-last"><Input id="ss-last" type="time" value={v.last_start||''} onChange={set('last_start')} data-testid="series-settings-last"/></Field>
   </div>
   <div className="button-row"><Button type="button" variant="outline" onClick={onClose} data-testid="series-settings-cancel">Cancel</Button><Button type="submit" data-testid="series-settings-save">Save</Button></div>
  </form>
 </DialogContent></Dialog>;
}

function Paper({c,free,busy,onAssign,onRemove}){
 const link=c.kind==='written'?'/super-admin/write/'+c.id:c.kind==='book_mock'?`/super-admin/fix/${c.book_id}/${c.id}${c.held?'':'?all=1'}`:null;
 return <li className="admin-row" data-testid={'series-paper-'+c.id}>
  <div className="admin-row-main"><strong>{c.title}</strong><small>{[c.book,`${c.count} sawaal`,c.kind==='written'?'Likha hua':c.kind==='set'?'Bana hua, din nahi':'PDF se'].filter(Boolean).join(' · ')}</small>{c.problem&&<p className="admin-reason">{c.problem}</p>}</div>
  {link&&<Button asChild size="sm" variant={c.held||c.problem?'default':'outline'}><Link to={link} data-testid={'series-paper-open-'+c.id}>{c.held?<><Wrench size={15}/>Fix</>:<><PencilLine size={15}/>Edit</>}</Link></Button>}
  {!c.problem&&free.length>0&&<Select value="" onValueChange={d=>onAssign(c,d)} disabled={busy}><SelectTrigger className="admin-move-select" aria-label={c.title+' ko din do'} data-testid={'series-paper-day-'+c.id}><SelectValue placeholder="Din do…"/></SelectTrigger><SelectContent>{free.map(s=><SelectItem key={s.date} value={s.date}>Din {s.day} · {dayIST(s.date)}</SelectItem>)}</SelectContent></Select>}
  {c.kind==='book_mock'&&c.upload_deletable&&<Button size="icon" variant="ghost" className="master-danger-icon" disabled={busy} aria-label={'Is PDF ko delete karo: '+c.book} onClick={()=>onRemove({id:c.book_id,title:c.book})} data-testid={'series-paper-delete-'+c.id}><Trash2 size={15}/></Button>}
 </li>;
}

export function SeriesDays({section,reloadKey,onChanged}){
 const [data,setData]=useState(null),[error,setError]=useState(''),[reload,setReload]=useState(0),[busy,setBusy]=useState(false),[dialog,setDialog]=useState(null);
 useEffect(()=>{api('/admin/master/series/'+section.series_id).then(d=>{setData(d);setError('');}).catch(e=>setError(e.message));},[section.series_id,reload,reloadKey]);
 async function run(fn){setBusy(true);try{const r=await fn();toast.success(r.message||'Save ho gaya.');setReload(n=>n+1);onChanged?.();}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 if(error)return <ErrorBox error={error} retry={()=>setReload(n=>n+1)}/>;
 if(!data)return <Skeleton className="h-64"/>;
 const free=data.slots.filter(s=>!s.paper&&!s.opened),assigned=data.slots.filter(s=>s.paper).length;
 return <>
  <section className="admin-panel master-series-head" data-testid="series-settings">
   <div className="admin-panel-head"><div><h2>{data.title}</h2><p data-testid="series-dates"><CalendarDays size={15}/>{dayIST(data.first_date)} – {dayIST(data.last_date)} · {data.total} din · khulta hai {clock(data.open_time)} · aakhri start {clock(data.last_start)} IST</p></div>
    <div className="admin-actions">{!data.builtin&&<Button variant="outline" onClick={()=>setDialog('settings')} data-testid="series-edit-settings"><Settings2 size={16}/>Dates aur time</Button>}</div></div>
   {data.builtin?<p className="admin-note" data-testid="series-builtin-note">JEE Main series apne 50 din (9 Dec 2026 – 27 Jan 2027) aur apna Home banner bilkul waise hi rakhti hai jaise students jaante hain. Iske aage ke dinon ko yahan paper dijiye.</p>
    :<label className="master-switch-row" data-testid="series-home-label"><Switch checked={data.shown} disabled={busy} onCheckedChange={v=>run(()=>put('/admin/master/series/'+data.id,{shown:v}))} data-testid="series-show-home"/><span><strong>Students ke liye khula</strong><small>{data.shown?(data.exam_shown?`Students ise ${data.exam.name} → All India Test Series mein kholte hain. Alag Home card nahi; woh sirf JEE Main ka hai.`:`On hai, par ${data.exam.name} khud abhi students se chhupa hai.`):'Students abhi yeh series nahi khol sakte.'}</small></span></label>}
   {data.pattern?.count&&<p className="master-hint">Har paper: {data.pattern.count} sawaal · {data.pattern.minutes} min · +{data.pattern.correct} / {data.pattern.wrong}.</p>}
  </section>
  <section className="admin-panel" data-testid="series-papers">
   <div className="admin-panel-head"><div><h2>Bina din wale paper ({data.candidates.length})</h2><p>Upar Upload PDF ya Write se bane. Koi paper apne din se pehle kabhi nahi dikhta.</p></div>
    <div className="admin-actions"><Button disabled={busy||!free.length||!data.candidates.some(c=>!c.problem)} onClick={()=>run(()=>post(`/admin/master/series/${data.id}/fill`))} data-testid="series-fill"><ListOrdered size={16}/>Din order se bharo</Button></div></div>
   {data.candidates.length?<ul className="admin-list">{data.candidates.map(c=><Paper key={c.kind+c.id} c={c} free={free} busy={busy} onRemove={t=>setDialog({remove:t})} onAssign={(c,date)=>run(()=>post(`/admin/master/series/${data.id}/assign`,{kind:c.kind,id:c.id,date}))}/>)}</ul>:<p className="admin-empty" data-testid="series-no-papers">Har paper ko din mil gaya hai. Aur upload kijiye ya likhiye.</p>}
  </section>
  <section className="admin-panel" data-testid="series-days">
   <div className="admin-panel-head"><div><h2>Din</h2><p>{data.total} mein se {assigned} din mein paper hai.</p></div><Button variant="outline" disabled={busy||!data.slots.some(s=>s.paper&&!s.opened)} onClick={()=>setDialog('clear')} data-testid="series-clear"><Eraser size={16}/>Aage ke saare din khali karo</Button></div>
   <ol className="master-days" data-testid="series-day-list">{data.slots.map(s=>{const [label,tone]=STATE[s.state]||STATE.upcoming;return <li key={s.date} className={'master-day'+(s.paper?' has-paper':'')+(s.opened?' is-opened':'')} data-testid={'series-day-'+s.day}>
    <span className="master-day-num">Din {s.day}</span><span className="master-day-date">{dayIST(s.date)}</span>
    <strong className="master-day-title">{s.paper?s.paper.title:'Khali'}{s.paper?.pending&&<small> · taiyaar ho raha hai</small>}</strong>
    {s.paper?.kind==='set'&&<label className={'master-live-switch'+(s.paper.off?'':' is-on')}><Switch checked={!s.paper.off} disabled={busy} onCheckedChange={v=>run(()=>post(`/admin/master/series/${data.id}/live`,{id:s.paper.id,live:v}))} aria-label={(s.paper.off?'Live karo: din ':'Off karo: din ')+s.day} data-testid={'series-day-live-'+s.day}/><span data-testid={'series-day-live-word-'+s.day}>{s.paper.off?'Off':'Live'}</span></label>}
    <StatusChip state={tone==='live'?'live':tone} label={label} testId={'series-day-state-'+s.day}/>
    {s.paper&&!s.opened&&<Button size="icon" variant="ghost" disabled={busy} aria-label={'Din '+s.day+' khali karo'} onClick={()=>run(()=>post(`/admin/master/series/${data.id}/unassign`,{kind:s.paper.kind,id:s.paper.id}))} data-testid={'series-day-free-'+s.day}><X size={15}/></Button>}
   </li>;})}</ol>
  </section>
  <DeleteUploadDialog target={dialog?.remove||null} onClose={()=>setDialog(null)} onDone={()=>{setReload(n=>n+1);onChanged?.();}}/>
  <Settings open={dialog==='settings'} onClose={()=>setDialog(null)} data={data} onSaved={()=>setReload(n=>n+1)}/>
  <ConfirmDialog open={dialog==='clear'} onClose={()=>setDialog(null)} busy={busy} testId="series-clear-confirm" title="Aage ke saare din khali karein?" text="Paper wapas bina din wali list mein chale jayenge. Jo din khul chuke hain woh nahi badlenge." button="Aage ke din khali karo" onConfirm={()=>{setDialog(null);run(()=>post(`/admin/master/series/${data.id}/clear`));}}/>
 </>;
}
