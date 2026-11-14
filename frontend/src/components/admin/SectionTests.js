import React,{useEffect,useState} from 'react';
import {Link,useNavigate} from 'react-router-dom';
import {ArrowUp,ArrowDown,Pencil,ExternalLink,Eye,Plus,RefreshCw,Archive} from 'lucide-react';
import {api,post,patch} from '../../lib/api';
import {invalidateCatalog} from '../../lib/catalog';
import {Button} from '../ui/button';
import {Switch} from '../ui/switch';
import {Skeleton} from '../ui/skeleton';
import {Select,SelectTrigger,SelectValue,SelectContent,SelectItem} from '../ui/select';
import {ErrorBox} from '../Shared';
import {StatusChip,TextDialog,ConfirmDialog} from './AdminShared';
import {ReadyAction} from './ReadyAction';
import {toast} from 'sonner';

const SOURCE={book:'From a combined book',mock_book:'Mock book',import:'Paper / Excel upload',chapter_book:'Chapter book',pyq:'Verified PYQ',manual:'Manual editor'};
export const sourceLink=t=>t.book_import_id?`/super-admin/upload?book=${t.book_import_id}`:t.import_id?`/studio/imports/${t.import_id}`:t.chapter_book_id?`/studio/chapter-books/${t.chapter_book_id}`:t.source==='manual'?`/studio/${t.id}`:null;

function TestState({t,onDone}){
 if(t.state==='draft'&&t.chapter_book_id)return <ReadyAction item={{kind:'chapter_book',id:t.chapter_book_id,title:'this chapter book'}} label="Draft · publish" onDone={onDone} testId={'admin-test-ready-'+t.id}/>;
 return <StatusChip state={t.state} testId={'admin-test-state-'+t.id}/>;
}

function TestRow({t,i,total,busy,reorder,targets,selectable,checked,onCheck,onMove,onLive,onRename,onRelocate,onDone}){
 const link=sourceLink(t);
 return <li className="admin-test-row" data-testid={'admin-test-'+t.id}>
  {selectable&&<input type="checkbox" className="admin-row-check" checked={checked} onChange={e=>onCheck(t.id,e.target.checked)} aria-label={'Select '+t.title} data-testid={'admin-test-select-'+t.id}/>}
  <span className="admin-test-index" aria-hidden="true">{String(i+1).padStart(2,'0')}</span>
  <div className="admin-row-main"><strong data-testid={'admin-test-title-'+t.id}>{t.title}</strong><small>{[t.subject,`${t.count} questions`,t.minutes?`${t.minutes} min`:null,SOURCE[t.source]].filter(Boolean).join(' · ')}</small>{t.replace_pending&&<small className="admin-replacing" data-testid={'admin-test-replacing-'+t.id}>Being replaced by “{t.replace_pending}”. It moves to the Library when that is published.</small>}</div>
  <TestState t={t} onDone={onDone}/>
  <div className="admin-test-actions">
   {reorder&&<><Button size="icon" variant="ghost" aria-label={'Move '+t.title+' up'} disabled={busy||i===0} onClick={()=>onMove(i,-1)} data-testid={'admin-test-up-'+t.id}><ArrowUp size={16}/></Button><Button size="icon" variant="ghost" aria-label={'Move '+t.title+' down'} disabled={busy||i===total-1} onClick={()=>onMove(i,1)} data-testid={'admin-test-down-'+t.id}><ArrowDown size={16}/></Button></>}
   <label className="admin-switch"><Switch checked={t.state!=='unlive'} disabled={busy||t.state==='draft'} onCheckedChange={v=>onLive(t,v)} aria-label={'Live for students: '+t.title} data-testid={'admin-test-live-'+t.id}/><span>{t.state==='unlive'?'Unlive':'Live'}</span></label>
   <Button size="icon" variant="ghost" aria-label={'Rename '+t.title} disabled={busy} onClick={()=>onRename(t)} data-testid={'admin-test-rename-'+t.id}><Pencil size={16}/></Button>
   {targets.length>0&&<Select value="" onValueChange={sid=>onRelocate(t,sid)} disabled={busy}><SelectTrigger className="admin-move-select" aria-label={'Move '+t.title+' to another section'} data-testid={'admin-test-move-'+t.id}><SelectValue placeholder="Move to…"/></SelectTrigger><SelectContent>{targets.map(s=><SelectItem key={s.id} value={s.id} data-testid={`admin-test-move-${t.id}-${s.slug}`}>{s.name}</SelectItem>)}</SelectContent></Select>}
   {link&&<Button asChild size="icon" variant="ghost"><Link to={link} aria-label={'Open the upload for '+t.title} data-testid={'admin-test-open-'+t.id}><ExternalLink size={16}/></Link></Button>}
   {t.state!=='draft'&&<Button asChild size="icon" variant="ghost"><Link to={'/sets/'+t.id} aria-label={'See '+t.title+' as a student'} data-testid={'admin-test-student-'+t.id}><Eye size={16}/></Link></Button>}
  </div>
 </li>;
}

function SelectBar({items,picked,setPicked,onReplace,onArchive}){
 return <div className="admin-select-bar" data-testid="section-select-bar">
  <label className="admin-check"><input type="checkbox" className="admin-row-check" checked={picked.size>0&&picked.size===items.length} onChange={e=>setPicked(e.target.checked?new Set(items.map(t=>t.id)):new Set())} data-testid="section-select-all"/><span data-testid="section-selected-count">{picked.size?`${picked.size} selected`:'Select tests to replace or move to the Library'}</span></label>
  {picked.size>0&&<><Button variant="outline" size="sm" onClick={onReplace} data-testid="section-replace-selected"><RefreshCw size={15}/>Replace with a new upload</Button><Button variant="outline" size="sm" onClick={onArchive} data-testid="section-archive-selected"><Archive size={15}/>Move to Library</Button><Button variant="ghost" size="sm" onClick={()=>setPicked(new Set())} data-testid="section-clear-selection">Clear</Button></>}
 </div>;
}

export function SectionTests({section,exam,path,onChanged}){
 const nav=useNavigate();
 const [items,setItems]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[rename,setRename]=useState(null),[reload,setReload]=useState(0),[picked,setPicked]=useState(new Set()),[confirm,setConfirm]=useState(false);
 useEffect(()=>{setItems(null);setError('');setPicked(new Set());api(path).then(d=>setItems(d.items)).catch(e=>setError(e.message));},[path,reload]);
 async function run(fn,message){setBusy(true);try{const r=await fn();invalidateCatalog();if(message)toast.success(typeof message==='function'?message(r):message);if(r?.note)toast.message(r.note);setReload(n=>n+1);onChanged?.();}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 function move(i,d){const ids=items.map(t=>t.id);[ids[i],ids[i+d]]=[ids[i+d],ids[i]];run(()=>post(`/admin/catalog/sections/${section.id}/order`,{ids}),'Order saved. Students see the new order.');}
 function check(id,on){setPicked(p=>{const n=new Set(p);on?n.add(id):n.delete(id);return n;});}
 const targets=exam.sections.filter(s=>s.id!==section?.id&&s.kind!=='pyq');
 const selectable=!!section&&section.kind!=='pyq';
 if(error)return <ErrorBox error={error} retry={()=>setReload(n=>n+1)}/>;
 if(!items)return <div className="admin-list">{[1,2,3].map(n=><Skeleton key={n} className="h-16"/>)}</div>;
 if(!items.length)return <div className="admin-empty" data-testid="section-empty"><p>Nothing in this section yet.</p>{section&&section.kind!=='pyq'&&<Button asChild><Link to={`/super-admin/upload/new?exam=${exam.slug}&section=${section.id}`} data-testid="section-empty-add"><Plus size={16}/>Add content</Link></Button>}</div>;
 return <>
  {selectable&&<SelectBar items={items} picked={picked} setPicked={setPicked} onArchive={()=>setConfirm(true)} onReplace={()=>nav(`/super-admin/upload/new?exam=${exam.slug}&section=${section.id}&replace=${[...picked].join(',')}`)}/>}
  <ol className="admin-list admin-test-list" data-testid="section-test-list">{items.map((t,i)=><TestRow key={t.id} t={t} i={i} total={items.length} busy={busy} reorder={selectable} targets={targets} selectable={selectable} checked={picked.has(t.id)} onCheck={check}
   onMove={move} onDone={()=>setReload(n=>n+1)}
   onLive={(t,live)=>run(()=>patch('/admin/catalog/tests/'+t.id,{live}),live?`${t.title} is switched on for students.`:`${t.title} is Unlive. Existing attempts and scores are kept.`)}
   onRename={setRename}
   onRelocate={(t,sid)=>run(()=>patch('/admin/catalog/tests/'+t.id,{section_id:sid}),`${t.title} moved to ${targets.find(s=>s.id===sid)?.name}. Attempts and scores are kept.`)}/>)}</ol>
  {section?.kind==='pyq'&&<p className="admin-note" data-testid="pyq-order-note">PYQ papers are listed by exam date and shift for students. They are never replaced or moved to the Library.</p>}
  <TextDialog open={!!rename} onClose={()=>setRename(null)} title="Rename test" label="Name students see" value={rename?.title} testId="test-rename-dialog" onSave={title=>run(()=>patch('/admin/catalog/tests/'+rename.id,{title}),'Name saved.')}/>
  <ConfirmDialog open={confirm} onClose={()=>setConfirm(false)} busy={busy} testId="archive-selected-confirm" title={`Move ${picked.size} test${picked.size===1?'':'s'} to the Library?`} text="Students stop seeing them here and in the app. Everyone keeps their old scores. You can restore them from Library any time." button="Move to Library"
   onConfirm={()=>{setConfirm(false);run(()=>post('/admin/library/archive',{ids:[...picked]}),r=>r.message);}}/>
 </>;
}
