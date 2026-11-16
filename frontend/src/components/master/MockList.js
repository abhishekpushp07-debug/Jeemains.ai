import React,{useState} from 'react';
import {Link} from 'react-router-dom';
import {ChevronDown,Wrench,PencilLine,Eye,Pencil,RefreshCw,Archive,Radio,CalendarClock,EyeOff,Lock} from 'lucide-react';
import {post,patch} from '../../lib/api';
import {invalidateCatalog} from '../../lib/catalog';
import {Button} from '../ui/button';
import {Switch} from '../ui/switch';
import {DropdownMenu,DropdownMenuTrigger,DropdownMenuContent,DropdownMenuItem,DropdownMenuSeparator} from '../ui/dropdown-menu';
import {TextDialog,ConfirmDialog} from '../admin/AdminShared';
import {ScheduleDialog} from './ScheduleDialog';
import {StatusLabel,SOURCE,fixLink,fmtIST,plural} from './MasterShared';
import {TryAsStudent} from './TryAsStudent';
import {toast} from 'sonner';

const key=m=>m.kind+':'+m.id;

function LiveSwitch({m,busy,onPick}){
 const on=['live','scheduled','publishing'].includes(m.status);
 const blocked=busy||m.status==='publishing'||m.status==='ended'||(!on&&(m.to_fix>0||m.empty));
 const word={scheduled:'Scheduled',publishing:'Going live',ended:'Ended'}[m.status]||(on?'Live':'Off');
 return <label className={'master-live-switch'+(on?' is-on':'')} title={m.to_fix>0&&!on?'Fix its marked questions first':undefined}>
  <Switch checked={on} disabled={blocked} onCheckedChange={v=>onPick(v?'live':'off',[m])} aria-label={(on?'Switch off ':'Make Live ')+m.title} data-testid={'mock-live-switch-'+m.id}/>
  <span data-testid={'mock-live-word-'+m.id}>{word}</span>
 </label>;
}

function StatusMenu({m,busy,onPick}){
 const [label,tone]=StatusLabel({m});
 const blocked=m.to_fix>0||m.empty;
 return <DropdownMenu><DropdownMenuTrigger asChild disabled={busy||m.status==='publishing'}><button type="button" className={'admin-chip master-status tone-'+tone} data-testid={'mock-status-'+m.id} aria-label={`Status ${label}. Change status of ${m.title}`}><span className="master-status-caption">Status</span><i aria-hidden="true"/>{label}<ChevronDown size={13} aria-hidden="true"/></button></DropdownMenuTrigger>
  <DropdownMenuContent align="end" className="master-menu">
   <DropdownMenuItem disabled={blocked||m.status==='live'} onSelect={()=>onPick('live',[m])} data-testid={'mock-make-live-'+m.id}><Radio size={15}/>Make Live</DropdownMenuItem>
   <DropdownMenuItem disabled={blocked||m.locked} onSelect={()=>onPick('scheduled',[m])} data-testid={'mock-schedule-'+m.id}><CalendarClock size={15}/>Schedule…</DropdownMenuItem>
   <DropdownMenuItem disabled={m.status==='draft'||m.status==='off'} onSelect={()=>onPick('off',[m])} data-testid={'mock-off-'+m.id}><EyeOff size={15}/>Switch Off</DropdownMenuItem>
   <DropdownMenuSeparator/>
   <DropdownMenuItem disabled={m.locked} onSelect={()=>onPick('library',[m])} data-testid={'mock-library-'+m.id}><Archive size={15}/>Move to Library</DropdownMenuItem>
  </DropdownMenuContent></DropdownMenu>;
}

function MockRow({m,i,checked,onCheck,busy,onPick,onRename}){
 if(m.kind==='import')return <li className="admin-test-row master-mock-row" data-testid={'mock-row-'+m.id}><span className="admin-test-index" aria-hidden="true">{String(i+1).padStart(2,'0')}</span><div className="admin-row-main"><strong>{m.title}</strong><small>{plural(m.count,'question')} · Older paper upload</small></div><span className="admin-chip tone-hidden"><i aria-hidden="true"/>Draft</span><div className="admin-test-actions"><Button asChild size="sm" variant="outline"><Link to={'/studio/imports/'+m.id} data-testid={'mock-open-import-'+m.id}>Open</Link></Button></div></li>;
 const facts=[m.subject,m.year,plural(m.count,'question'),m.minutes?`${m.minutes} min`:null,m.written?'Written':m.book?`From PDF · ${m.book}`:SOURCE[m.source],m.key_only>0?(m.key_only===m.count?'Answer key only, no solutions':`${m.key_only} without a solution`):null,
  m.status==='scheduled'&&m.start_at?`Opens ${fmtIST(m.start_at)}`:null,m.live_exam?'Live exam':null].filter(Boolean).join(' · ');
 const main=m.to_fix>0?<Button asChild size="sm"><Link to={fixLink(m)} data-testid={'mock-fix-'+m.id}><Wrench size={15}/>Fix</Link></Button>
  :m.written?<Button asChild size="sm" variant="outline"><Link to={'/super-admin/write/'+m.id} data-testid={'mock-edit-'+m.id}><PencilLine size={15}/>Edit</Link></Button>
  :m.kind==='book_mock'&&m.status==='draft'?<Button asChild size="sm" variant="outline"><Link to={`/super-admin/fix/${m.book_id}/${m.id}?all=1`} data-testid={'mock-edit-questions-'+m.id}><PencilLine size={15}/>Edit</Link></Button>
  :m.kind==='set'&&m.status!=='draft'?<Button asChild size="icon" variant="ghost"><Link to={'/sets/'+m.id} aria-label={'See '+m.title+' as a student'} data-testid={'mock-student-'+m.id}><Eye size={16}/></Link></Button>:null;
 return <li className="admin-test-row master-mock-row" data-testid={'mock-row-'+m.id}>
  <input type="checkbox" className="admin-row-check" checked={checked} onChange={e=>onCheck(m,e.target.checked)} aria-label={'Select '+m.title} data-testid={'mock-select-'+m.id}/>
  <span className="admin-test-index" aria-hidden="true">{String(i+1).padStart(2,'0')}</span>
  <div className="admin-row-main"><strong data-testid={'mock-title-'+m.id}>{m.locked&&<Lock size={13} className="master-lock" aria-label="Locked"/>}{m.title}</strong><small>{facts}</small>{m.replace_pending&&<small className="admin-replacing">Being replaced by “{m.replace_pending}”. It moves to the Library when that goes Live.</small>}</div>
  <div className="master-row-status"><LiveSwitch m={m} busy={busy} onPick={onPick}/><StatusMenu m={m} busy={busy} onPick={onPick}/></div>
  <div className="admin-test-actions">{m.status==='draft'&&m.count>0&&<TryAsStudent m={m}/>}{main}{m.kind==='set'&&!m.locked&&<Button size="icon" variant="ghost" aria-label={'Rename '+m.title} disabled={busy} onClick={()=>onRename(m)} data-testid={'mock-rename-'+m.id}><Pencil size={15}/></Button>}</div>
 </li>;
}

export function MockList({items,onChanged,onReplace}){
 const [picked,setPicked]=useState(new Map()),[busy,setBusy]=useState(false),[schedule,setSchedule]=useState(null),[library,setLibrary]=useState(null),[rename,setRename]=useState(null);
 function check(m,on){setPicked(p=>{const n=new Map(p);on?n.set(key(m),m):n.delete(key(m));return n;});}
 async function run(to,list,extra={}){setBusy(true);try{
  const r=await post('/admin/master/status',{items:list.map(m=>({kind:m.kind,id:m.id})),to,...extra});invalidateCatalog();
  if(r.done)toast.success(r.message);
  if(r.skipped.length)toast.message(`${plural(r.skipped.length,'mock')} not changed`,{description:r.skipped.slice(0,3).map(s=>`${s.title}: ${s.reason}`).join('\n')});
  setPicked(new Map());onChanged();
 }catch(e){toast.error(e.message);}finally{setBusy(false);}}
 function pick(to,list){if(to==='scheduled')setSchedule(list);else if(to==='library')setLibrary(list);else run(to,list);}
 const pickable=items.filter(m=>m.kind!=='import');
 const chosen=[...picked.values()];
 const replaceable=chosen.filter(m=>m.kind==='set'&&!m.locked);
 if(!items.length)return <div className="admin-empty" data-testid="mock-list-empty"><p>No mocks here yet. Use Upload PDF or Write to make the first one.</p></div>;
 return <>
  <div className="admin-select-bar master-bulk" data-testid="mock-select-bar">
   <label className="admin-check"><input type="checkbox" className="admin-row-check" checked={picked.size>0&&picked.size===pickable.length} onChange={e=>setPicked(e.target.checked?new Map(pickable.map(m=>[key(m),m])):new Map())} data-testid="mock-select-all"/><span data-testid="mock-selected-count">{picked.size?`${picked.size} selected`:'Select all'}</span></label>
   {picked.size>0&&<div className="admin-actions">
    <Button size="sm" disabled={busy} onClick={()=>run('live',chosen)} data-testid="bulk-live"><Radio size={15}/>Make Live</Button>
    <Button size="sm" variant="outline" disabled={busy} onClick={()=>setSchedule(chosen)} data-testid="bulk-schedule"><CalendarClock size={15}/>Schedule</Button>
    <Button size="sm" variant="outline" disabled={busy} onClick={()=>run('off',chosen)} data-testid="bulk-off"><EyeOff size={15}/>Off</Button>
    <Button size="sm" variant="outline" disabled={busy} onClick={()=>setLibrary(chosen)} data-testid="bulk-library"><Archive size={15}/>Library</Button>
    {replaceable.length>0&&<Button size="sm" variant="outline" onClick={()=>onReplace(replaceable.map(m=>m.id).join(','))} data-testid="bulk-replace"><RefreshCw size={15}/>Replace with new PDF</Button>}
    <Button size="sm" variant="ghost" onClick={()=>setPicked(new Map())} data-testid="bulk-clear">Clear</Button>
   </div>}
  </div>
  <ol className="admin-list admin-test-list" data-testid="mock-list">{items.map((m,i)=><MockRow key={key(m)} m={m} i={i} checked={picked.has(key(m))} onCheck={check} busy={busy} onPick={pick} onRename={setRename}/>)}</ol>
  <ScheduleDialog open={!!schedule} count={schedule?.length||0} onClose={()=>setSchedule(null)} onSave={(at,live_exam)=>{const list=schedule;setSchedule(null);run('scheduled',list,{at,live_exam});}}/>
  <ConfirmDialog open={!!library} onClose={()=>setLibrary(null)} busy={busy} testId="library-confirm" title={`Move ${plural(library?.length||0,'mock')} to the Library?`} text="Students stop seeing them on the website and the app. Everyone keeps their old scores. You can restore them from Library any time. Verified PYQ papers stay where they are." button="Move to Library" onConfirm={()=>{const list=library;setLibrary(null);run('library',list);}}/>
  <TextDialog open={!!rename} onClose={()=>setRename(null)} title="Rename mock" label="Name students see" value={rename?.title} testId="mock-rename-dialog" onSave={title=>patch('/admin/catalog/tests/'+rename.id,{title}).then(()=>{invalidateCatalog();toast.success('Name saved.');onChanged();})}/>
 </>;
}
