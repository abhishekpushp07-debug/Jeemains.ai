import React,{useState} from 'react';
import {Link} from 'react-router-dom';
import {ChevronDown,Wrench,PencilLine,Eye,Pencil,RefreshCw,Archive,Radio,CalendarClock,EyeOff,Lock,Loader2,Trash2} from 'lucide-react';
import {DeleteUploadDialog} from './DeleteUploadDialog';
import {post,patch} from '../../lib/api';
import {invalidateCatalog} from '../../lib/catalog';
import {Button} from '../ui/button';
import {Switch} from '../ui/switch';
import {DropdownMenu,DropdownMenuTrigger,DropdownMenuContent,DropdownMenuItem,DropdownMenuSeparator} from '../ui/dropdown-menu';
import {TextDialog,ConfirmDialog} from '../admin/AdminShared';
import {ScheduleDialog} from './ScheduleDialog';
import {StatusLabel,SOURCE,fixLink,fmtIST,stuckLine} from './MasterShared';
import {TryAsStudent} from './TryAsStudent';
import {DuplicateNote} from './Duplicates';
import {toast} from 'sonner';

const key=m=>m.kind+':'+m.id;
const REREAD='PDF dobara padhi ja rahi hai. Padhai poori hone ke baad Live kar sakte hain.';

function LiveSwitch({m,busy,onPick}){
 const on=['live','scheduled','publishing'].includes(m.status);
 const blocked=busy||m.status==='publishing'||m.status==='ended'||(!on&&(m.to_fix>0||m.empty||!!m.rereading));
 const word=m.stuck?'Atki hai':{scheduled:'Scheduled',publishing:'Live ho raha hai',ended:'Khatam'}[m.status]||(on?'Live':'Off');
 const why=on?undefined:m.rereading?REREAD:m.to_fix>0?'Pehle iske marked sawaal fix kijiye':undefined;
 return <label className={'master-live-switch'+(on?' is-on':'')} title={why}>
  <Switch checked={on} disabled={blocked} onCheckedChange={v=>onPick(v?'live':'off',[m])} aria-label={(on?'Off karo: ':'Live karo: ')+m.title} data-testid={'mock-live-switch-'+m.id}/>
  <span data-testid={'mock-live-word-'+m.id}>{word}</span>
 </label>;
}

function StatusMenu({m,busy,onPick}){
 const [label,tone]=StatusLabel({m});
 const blocked=m.to_fix>0||m.empty||!!m.rereading;
 return <DropdownMenu><DropdownMenuTrigger asChild disabled={busy||m.status==='publishing'}><button type="button" className={'admin-chip master-status tone-'+tone} data-testid={'mock-status-'+m.id} aria-label={`Status ${label}. ${m.title} ka status badlo`}><span className="master-status-caption">Status</span><i aria-hidden="true"/>{label}<ChevronDown size={13} aria-hidden="true"/></button></DropdownMenuTrigger>
  <DropdownMenuContent align="end" className="master-menu">
   <DropdownMenuItem disabled={blocked||m.status==='live'} onSelect={()=>onPick('live',[m])} data-testid={'mock-make-live-'+m.id}><Radio size={15}/>Live karo</DropdownMenuItem>
   <DropdownMenuItem disabled={blocked||m.locked} onSelect={()=>onPick('scheduled',[m])} data-testid={'mock-schedule-'+m.id}><CalendarClock size={15}/>Schedule karo…</DropdownMenuItem>
   <DropdownMenuItem disabled={m.status==='draft'||m.status==='off'} onSelect={()=>onPick('off',[m])} data-testid={'mock-off-'+m.id}><EyeOff size={15}/>Off karo</DropdownMenuItem>
   <DropdownMenuSeparator/>
   <DropdownMenuItem disabled={m.locked} onSelect={()=>onPick('library',[m])} data-testid={'mock-library-'+m.id}><Archive size={15}/>Library mein bhejo</DropdownMenuItem>
   {m.kind==='book_mock'&&m.status==='draft'&&m.upload_deletable&&<DropdownMenuItem className="master-menu-danger" onSelect={()=>onPick('delete_upload',[m])} data-testid={'mock-delete-upload-'+m.id}><Trash2 size={15}/>Is PDF ko delete karo…</DropdownMenuItem>}
  </DropdownMenuContent></DropdownMenu>;
}

function facts(m){
 const cut=m.cut?.total?[`${m.cut.clean} saaf kate`,m.cut.held?`${m.cut.held} par aapki nazar chahiye`:null,m.cut.whole?`${m.cut.whole} poori picture`:null].filter(Boolean).join(' · '):null;
 return [m.subject,m.year,`${m.count} sawaal`,cut,m.minutes?`${m.minutes} min`:null,m.written?'Likha hua':m.book?`PDF se · ${m.book}`:SOURCE[m.source],m.key_only>0?(m.key_only===m.count?'Sirf answer key, solution nahi':`${m.key_only} bina solution`):null,
  m.status==='scheduled'&&m.start_at?`Khulega ${fmtIST(m.start_at)}`:null,m.live_exam?'Live exam':null,
  m.status==='publishing'&&m.publish_progress?.total?`Picture ${m.publish_progress.done}/${m.publish_progress.total} save hui`:null].filter(Boolean).join(' · ');
}

function MainAction({m}){
 if(m.rereading)return null;
 if(m.to_fix>0)return <Button asChild size="sm"><Link to={fixLink(m)} data-testid={'mock-fix-'+m.id}><Wrench size={15}/>Fix</Link></Button>;
 if(m.written)return <Button asChild size="sm" variant="outline"><Link to={'/super-admin/write/'+m.id} data-testid={'mock-edit-'+m.id}><PencilLine size={15}/>Edit</Link></Button>;
 if(m.kind==='book_mock'&&m.status==='draft')return <Button asChild size="sm" variant="outline"><Link to={`/super-admin/fix/${m.book_id}/${m.id}?all=1`} data-testid={'mock-edit-questions-'+m.id}><PencilLine size={15}/>Edit</Link></Button>;
 if(m.kind==='set'&&m.status!=='draft')return <Button asChild size="icon" variant="ghost"><Link to={'/sets/'+m.id} aria-label={'Student ki tarah dekho: '+m.title} data-testid={'mock-student-'+m.id}><Eye size={16}/></Link></Button>;
 return null;
}

function MockRow({m,i,checked,onCheck,busy,onPick,onRename}){
 if(m.kind==='import')return <li className="admin-test-row master-mock-row" data-testid={'mock-row-'+m.id}><span className="admin-test-index" aria-hidden="true">{String(i+1).padStart(2,'0')}</span><div className="admin-row-main"><strong>{m.title}</strong><small>{m.count} sawaal · Purane paper ka upload</small></div><span className="admin-chip tone-hidden"><i aria-hidden="true"/>Draft</span><div className="admin-test-actions"><Button asChild size="sm" variant="outline"><Link to={'/studio/imports/'+m.id} data-testid={'mock-open-import-'+m.id}>Kholo</Link></Button></div></li>;
 return <li className="admin-test-row master-mock-row" data-testid={'mock-row-'+m.id}>
  <label className="master-check-hit"><input type="checkbox" className="admin-row-check" checked={checked} disabled={!!m.rereading} onChange={e=>onCheck(m,e.target.checked)} aria-label={'Chuno: '+m.title} data-testid={'mock-select-'+m.id}/></label>
  <span className="admin-test-index" aria-hidden="true">{String(i+1).padStart(2,'0')}</span>
  <div className="admin-row-main"><strong data-testid={'mock-title-'+m.id}>{m.locked&&<Lock size={13} className="master-lock" aria-label="Locked"/>}{m.title}</strong><small>{facts(m)}</small>
   {m.pictures&&<small className="master-proof" data-testid={'mock-pictures-'+m.id}>Pictures: {m.pictures.proven} / {m.pictures.total} · Storage: {m.pictures.store==='supabase'?'Supabase':'Emergent'}</small>}
   {m.rereading&&<small className="master-reread" data-testid={'mock-rereading-'+m.id}><Loader2 size={13} className="spin" aria-hidden="true"/>dobara padhi ja rahi hai · {m.rereading.read_pages}/{m.rereading.pages} page</small>}
   {m.stuck&&<small className="admin-reason" data-testid={'mock-stuck-'+m.id}>{stuckLine(m.stuck)}</small>}
   {m.replace_pending&&<small className="admin-replacing">“{m.replace_pending}” isko replace karega. Woh Live hote hi yeh Library mein chala jayega.</small>}<DuplicateNote m={m}/></div>
  <div className="master-row-status"><LiveSwitch m={m} busy={busy} onPick={onPick}/><StatusMenu m={m} busy={busy} onPick={onPick}/></div>
  <div className="admin-test-actions">{m.status==='draft'&&m.count>0&&!m.rereading&&<TryAsStudent m={m}/>}<MainAction m={m}/>{m.kind==='set'&&!m.locked&&<Button size="icon" variant="ghost" aria-label={'Naam badlo: '+m.title} disabled={busy} onClick={()=>onRename(m)} data-testid={'mock-rename-'+m.id}><Pencil size={15}/></Button>}</div>
 </li>;
}

export function MockList({items,onChanged,onReplace}){
 const [picked,setPicked]=useState(new Map()),[busy,setBusy]=useState(false),[schedule,setSchedule]=useState(null),[library,setLibrary]=useState(null),[rename,setRename]=useState(null);
 function check(m,on){setPicked(p=>{const n=new Map(p);on?n.set(key(m),m):n.delete(key(m));return n;});}
 async function run(to,list,extra={}){setBusy(true);try{
  const r=await post('/admin/master/status',{items:list.map(m=>({kind:m.kind,id:m.id})),to,...extra});invalidateCatalog();
  if(r.done)toast.success(r.message);
  if(r.skipped.length)toast.message(`${r.skipped.length} mock nahi badle`,{description:r.skipped.slice(0,3).map(s=>`${s.title}: ${s.reason}`).join('\n')});
  setPicked(new Map());onChanged();
 }catch(e){toast.error(e.message);}finally{setBusy(false);}}
 const [remove,setRemove]=useState(null);
 function pick(to,list){if(to==='scheduled')setSchedule(list);else if(to==='library')setLibrary(list);else if(to==='delete_upload')setRemove({id:list[0].book_id,title:list[0].book});else run(to,list);}
 const pickable=items.filter(m=>m.kind!=='import'&&!m.rereading);
 const chosen=[...picked.values()];
 const replaceable=chosen.filter(m=>m.kind==='set'&&!m.locked);
 if(!items.length)return <div className="admin-empty" data-testid="mock-list-empty"><p>Yahan abhi koi mock nahi hai. Pehla mock banane ke liye Upload PDF ya Write dabaiye.</p></div>;
 return <>
  <div className="admin-select-bar master-bulk" data-testid="mock-select-bar">
   <label className="admin-check master-check-all"><input type="checkbox" className="admin-row-check" checked={picked.size>0&&picked.size===pickable.length} onChange={e=>setPicked(e.target.checked?new Map(pickable.map(m=>[key(m),m])):new Map())} data-testid="mock-select-all"/><span data-testid="mock-selected-count">{picked.size?`${picked.size} chune`:'Sab chuno'}</span></label>
   {picked.size>0&&<div className="admin-actions">
    <Button size="sm" disabled={busy} onClick={()=>run('live',chosen)} data-testid="bulk-live"><Radio size={15}/>Live karo</Button>
    <Button size="sm" variant="outline" disabled={busy} onClick={()=>setSchedule(chosen)} data-testid="bulk-schedule"><CalendarClock size={15}/>Schedule</Button>
    <Button size="sm" variant="outline" disabled={busy} onClick={()=>run('off',chosen)} data-testid="bulk-off"><EyeOff size={15}/>Off</Button>
    <Button size="sm" variant="outline" disabled={busy} onClick={()=>setLibrary(chosen)} data-testid="bulk-library"><Archive size={15}/>Library</Button>
    {replaceable.length>0&&<Button size="sm" variant="outline" onClick={()=>onReplace(replaceable.map(m=>m.id).join(','))} data-testid="bulk-replace"><RefreshCw size={15}/>Naye PDF se badlo</Button>}
    <Button size="sm" variant="ghost" onClick={()=>setPicked(new Map())} data-testid="bulk-clear">Hatao</Button>
   </div>}
  </div>
  <ol className="admin-list admin-test-list" data-testid="mock-list">{items.map((m,i)=><MockRow key={key(m)} m={m} i={i} checked={picked.has(key(m))} onCheck={check} busy={busy} onPick={pick} onRename={setRename}/>)}</ol>
  <ScheduleDialog open={!!schedule} count={schedule?.length||0} onClose={()=>setSchedule(null)} onSave={(at,live_exam)=>{const list=schedule;setSchedule(null);run('scheduled',list,{at,live_exam});}}/>
  <ConfirmDialog open={!!library} onClose={()=>setLibrary(null)} busy={busy} testId="library-confirm" title={`${library?.length||0} mock Library mein bhejein?`} text="Students ko website aur app par yeh dikhna band ho jayega. Sabke purane score rahenge. Library se kabhi bhi wapas la sakte hain. Verified PYQ papers jahan hain wahin rahenge." button="Library mein bhejo" onConfirm={()=>{const list=library;setLibrary(null);run('library',list);}}/>
  <DeleteUploadDialog target={remove} onClose={()=>setRemove(null)} onDone={()=>{invalidateCatalog();onChanged();}}/>
  <TextDialog open={!!rename} onClose={()=>setRename(null)} title="Mock ka naam badlo" label="Students ko dikhne wala naam" value={rename?.title} testId="mock-rename-dialog" onSave={title=>patch('/admin/catalog/tests/'+rename.id,{title}).then(()=>{invalidateCatalog();toast.success('Naam save ho gaya.');onChanged();})}/>
 </>;
}
