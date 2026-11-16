import React,{useEffect,useMemo,useState} from 'react';
import {Archive,Download,RotateCcw,Search,X,Trash2} from 'lucide-react';
import {api,post,downloadFile} from '../../lib/api';
import {invalidateCatalog} from '../../lib/catalog';
import {Button} from '../../components/ui/button';
import {Input} from '../../components/ui/input';
import {Skeleton} from '../../components/ui/skeleton';
import {ErrorBox} from '../../components/Shared';
import {AdminCrumbs,AdminHeading} from '../../components/admin/AdminShared';
import {LibraryGuide} from '../../components/library/LibraryGuide';
import {LibraryGroup,LibraryUploads} from '../../components/library/LibraryGroups';
import {RestoreDialog} from '../../components/library/RestoreDialog';
import {DeleteDialog} from '../../components/library/DeleteDialog';
import {toast} from 'sonner';

const KINDS={pyq:'PYQ Papers',mocks:'Mock Tests',chapters:'Chapter-wise',aits:'All India Test Series',custom:'Your own types',other:'Not in any mock type'};
const ORDER=Object.keys(KINDS);

function Segments({items,value,onChange,testId,label}){
 return <div className="library-segments" role="tablist" aria-label={label} data-testid={testId}>{items.map(([id,name,n])=><button key={id} type="button" role="tab" aria-selected={value===id} className={value===id?'is-active':''} onClick={()=>onChange(id)} data-testid={`${testId}-${id}`}>{name}<span className="library-count">{n}</span></button>)}</div>;
}

function groupsOf(items){
 const map=new Map();
 items.forEach(t=>{const key=t.section_id||'none:'+t.exam_name;if(!map.has(key))map.set(key,{sid:t.section_id,exam:t.exam_name||'Other',section:t.section_name,kind:t.section_kind,items:[]});map.get(key).items.push(t);});
 const out=[...map.values()];
 out.forEach(g=>g.items.sort((a,b)=>(a.subject||'').localeCompare(b.subject||'')||(a.chapter_number||0)-(b.chapter_number||0)||(a.catalog_order||0)-(b.catalog_order||0)));
 return out.sort((a,b)=>a.exam.localeCompare(b.exam)||ORDER.indexOf(a.kind)-ORDER.indexOf(b.kind));
}

function useLibrary(){
 const [data,setData]=useState(null),[error,setError]=useState(''),[reload,setReload]=useState(0);
 useEffect(()=>{api('/admin/library').then(d=>{setData(d);setError('');}).catch(e=>setError(e.message));},[reload]);
 return {data,error,refresh:()=>setReload(n=>n+1)};
}

export default function AdminLibrary(){
 const {data,error,refresh}=useLibrary();
 const [exam,setExam]=useState('all'),[kind,setKind]=useState('all'),[q,setQ]=useState(''),[picked,setPicked]=useState(new Set()),[asking,setAsking]=useState(null),[removing,setRemoving]=useState(null),[busy,setBusy]=useState(false),[zipping,setZipping]=useState(false);
 const items=useMemo(()=>data?.items||[],[data]),uploads=useMemo(()=>data?.uploads||[],[data]);
 const exams=useMemo(()=>{const n={};items.forEach(t=>{n[t.exam_slug||'other']=(n[t.exam_slug||'other']||0)+1;});return [['all','All exams',items.length],...(data?.exams||[]).filter(e=>n[e.slug]).map(e=>[e.slug,e.name,n[e.slug]]),...(n.other?[['other','Other',n.other]]:[]),...(uploads.length?[['uploads','Uploads never Live',uploads.length]]:[])];},[items,uploads,data]);
 const inExam=useMemo(()=>items.filter(t=>exam==='all'||(t.exam_slug||'other')===exam),[items,exam]);
 const kinds=useMemo(()=>{const n={};inExam.forEach(t=>{n[t.section_kind]=(n[t.section_kind]||0)+1;});return [['all','All types',inExam.length],...ORDER.filter(k=>n[k]).map(k=>[k,KINDS[k],n[k]])];},[inExam]);
 const shown=useMemo(()=>{const s=q.trim().toLowerCase();return inExam.filter(t=>(kind==='all'||t.section_kind===kind)&&(!s||`${t.title} ${t.subject||''} ${t.section_name}`.toLowerCase().includes(s)));},[inExam,kind,q]);
 const groups=useMemo(()=>groupsOf(shown),[shown]);
 useEffect(()=>{setKind('all');},[exam]);
 function check(ids,on){setPicked(p=>{const n=new Set(p);ids.forEach(id=>on?n.add(id):n.delete(id));return n;});}
 async function restore(ids,refs=[]){setBusy(true);try{const r=await post('/admin/library/restore',{ids,uploads:refs});invalidateCatalog();toast.success(r.message);setPicked(new Set());setAsking(null);refresh();}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 async function remove(){setBusy(true);try{const r=await post('/admin/library/delete',{ids:removing.tests.map(t=>t.id),uploads:removing.uploads.map(x=>({kind:x.kind,id:x.id})),confirm:'DELETE'});toast.success(r.message);setPicked(new Set());setRemoving(null);refresh();}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 async function zipAll(){setZipping(true);try{await downloadFile('/admin/library/export','jeelive-library.zip');}catch(e){toast.error(e.message);}finally{setZipping(false);}}
 const chosen=items.filter(t=>picked.has(t.id));
 return <div className="admin-page library-page" data-testid="admin-library-page">
  <AdminCrumbs items={[{label:'Master',to:'/super-admin'},{label:'Library'}]}/>
  <AdminHeading testId="admin-library-title" title="Library" text="Your recycle bin for tests. Students cannot see anything here, their old scores are kept, and one click puts a test back where it was, or deletes it for good." action={<Button variant="outline" onClick={zipAll} disabled={zipping||!items.length} data-testid="library-zip-all"><Download size={17}/>{zipping?'Preparing ZIP…':'Download all as ZIP'}</Button>}/>
  <ErrorBox error={error} retry={refresh}/>
  {!data&&!error&&<Skeleton className="h-64"/>}
  {data&&<>
   <div className="library-stats" data-testid="library-stats"><div><strong data-testid="library-stat-tests">{items.length}</strong><span>tests in the Library</span></div><div><strong data-testid="library-stat-attempts">{data.attempts_kept||0}</strong><span>student attempts kept</span></div><div><strong data-testid="library-stat-uploads">{uploads.length}</strong><span>uploads never Live</span></div></div>
   <LibraryGuide fresh={data.fresh_start}/>
   {!items.length&&!uploads.length?<div className="admin-empty" data-testid="library-empty"><Archive size={22}/><p>The Library is empty. Tests you move here from Master, or replace with a new PDF, appear here.</p></div>:<>
    <Segments items={exams} value={exam} onChange={setExam} testId="library-exam-tabs" label="Exam"/>
    {exam!=='uploads'&&<>
     {kinds.length>2&&<Segments items={kinds} value={kind} onChange={setKind} testId="library-type-filters" label="Mock type"/>}
     <div className="library-search"><Search size={16} aria-hidden="true"/><Input value={q} onChange={e=>setQ(e.target.value)} placeholder="Find a test, chapter or subject" aria-label="Find a test" data-testid="library-search"/>{q&&<Button size="icon" variant="ghost" onClick={()=>setQ('')} aria-label="Clear search" data-testid="library-search-clear"><X size={15}/></Button>}</div>
     {!groups.length?<p className="admin-empty" data-testid="library-no-match">Nothing matches. Try another word or choose All exams.</p>:
      groups.map(g=><LibraryGroup key={(g.sid||g.exam)+exam+kind} g={g} startOpen={groups.length<=2||!!q} picked={picked} onCheck={check} onRestore={setAsking} onDelete={setRemoving} busy={busy}/>)}
    </>}
    {(exam==='uploads'||(exam==='all'&&kind==='all'&&!q))&&uploads.length>0&&<LibraryUploads items={uploads} busy={busy} onRestore={restore} onDelete={setRemoving}/>}
   </>}
  </>}
  {picked.size>0&&<div className="library-sticky-bar" data-testid="library-sticky-batch-bar"><span data-testid="library-selected-count">{picked.size} selected</span><div className="button-row"><Button variant="ghost" onClick={()=>setPicked(new Set())} data-testid="library-clear-selection">Clear</Button><Button variant="outline" className="library-delete" onClick={()=>setRemoving({tests:chosen,uploads:[]})} disabled={busy} data-testid="library-delete-selected"><Trash2 size={16}/>Delete selected</Button><Button onClick={()=>setAsking(chosen)} disabled={busy} data-testid="library-restore-selected"><RotateCcw size={16}/>Restore selected</Button></div></div>}
  <RestoreDialog tests={asking} busy={busy} onClose={()=>setAsking(null)} onConfirm={()=>restore(asking.map(t=>t.id))}/>
  <DeleteDialog target={removing} busy={busy} onClose={()=>setRemoving(null)} onConfirm={remove}/>
 </div>;
}
