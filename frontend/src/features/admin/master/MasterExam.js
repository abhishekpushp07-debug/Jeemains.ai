import React,{useEffect,useState} from 'react';
import {Link,useParams} from 'react-router-dom';
import {Plus,ArrowUp,ArrowDown,Settings2,Eye,EyeOff,Home,Pencil,ChevronRight,FolderOpen} from 'lucide-react';
import {api,post,patch} from '../../../lib/api';
import {invalidateCatalog} from '../../../lib/catalog';
import {Button} from '../../../components/ui/button';
import {Skeleton} from '../../../components/ui/skeleton';
import {ErrorBox} from '../../../components/Shared';
import {AdminHeading,StatusChip,TextDialog} from '../../../components/admin/AdminShared';
import {MasterCrumbs,KIND_LABEL,marks} from '../../../components/master/MasterShared';
import {TypeDialog,TypeSettings} from '../../../components/master/TypeDialog';
import {toast} from 'sonner';

function TypeRow({s,i,total,waiting,busy,exam,onMove,onHide,onSettings}){
 const drafts=s.counts.draft+(waiting?.ready||0)+(waiting?.held||0);
 const facts=[KIND_LABEL[s.kind]||'Apna type',s.kind==='aits'?'Roz ek paper':`${s.counts.total+(waiting?.ready||0)+(waiting?.held||0)} mock · ${s.counts.live} live${drafts?` · ${drafts} draft`:''}`,marks(s.defaults)].filter(Boolean).join(' · ');
 return <li className="admin-row master-type-row" data-testid={'master-type-'+s.slug}>
  <Link to={`/super-admin/exam/${exam.slug}/${s.id}`} className="admin-row-main master-type-open" data-testid={'master-type-open-'+s.slug}><strong>{s.name}</strong><small>{facts}</small></Link>
  {s.hidden?<StatusChip state="hidden" label="Chhupa hai" testId={'master-type-state-'+s.slug}/>:(waiting?.held>0?<StatusChip state="attention_needed" label={waiting.held+' fix karne hain'} testId={'master-type-state-'+s.slug}/>:null)}
  <div className="admin-test-actions">
   <Button size="icon" variant="ghost" aria-label={s.name+' ko upar karo'} disabled={busy||i===0} onClick={()=>onMove(i,-1)} data-testid={'master-type-up-'+s.slug}><ArrowUp size={16}/></Button>
   <Button size="icon" variant="ghost" aria-label={s.name+' ko neeche karo'} disabled={busy||i===total-1} onClick={()=>onMove(i,1)} data-testid={'master-type-down-'+s.slug}><ArrowDown size={16}/></Button>
   <Button size="icon" variant="ghost" aria-label={s.name+' ki settings'} onClick={onSettings} data-testid={'master-type-settings-'+s.slug}><Settings2 size={16}/></Button>
   <Button size="icon" variant="ghost" aria-label={s.name+(s.hidden?' dikhao':' chhupao')} disabled={busy} onClick={onHide} data-testid={'master-type-hide-'+s.slug}>{s.hidden?<Eye size={16}/>:<EyeOff size={16}/>}</Button>
   <Button asChild variant="outline" size="sm"><Link to={`/super-admin/exam/${exam.slug}/${s.id}`} data-testid={'master-type-go-'+s.slug}>Kholo<ChevronRight size={15}/></Link></Button>
  </div>
 </li>;
}

export default function MasterExam(){
 const {slug}=useParams();
 const [data,setData]=useState(null),[waiting,setWaiting]=useState({}),[error,setError]=useState(''),[reload,setReload]=useState(0),[busy,setBusy]=useState(false),[dialog,setDialog]=useState(null);
 useEffect(()=>{api('/admin/catalog').then(d=>{setData(d);setError('');}).catch(e=>setError(e.message));api('/admin/master/summary').then(s=>setWaiting(s.waiting)).catch(()=>{});},[reload]);
 const exam=data?.items.find(e=>e.slug===slug);
 async function run(fn,message){setBusy(true);try{await fn();invalidateCatalog();toast.success(message);setReload(n=>n+1);}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 function move(i,d){const ids=exam.sections.map(s=>s.id);[ids[i],ids[i+d]]=[ids[i+d],ids[i]];run(()=>post(`/admin/catalog/exams/${slug}/sections/order`,{ids}),'Order save ho gaya. Students ko naya order dikhega.');}
 if(error)return <ErrorBox error={error} retry={()=>setReload(n=>n+1)}/>;
 if(!data)return <Skeleton className="h-64"/>;
 if(!exam)return <div className="admin-empty" data-testid="master-exam-missing"><p>Yeh exam nahi mila.</p><Button asChild><Link to="/super-admin">Master par wapas</Link></Button></div>;
 return <div className="admin-page master-page" data-testid={'master-exam-page-'+slug}>
  <MasterCrumbs exam={exam}/>
  <AdminHeading testId="master-exam-title" title={exam.name} text={exam.subjects.join(' · ')} action={<div className="admin-actions">
   {!exam.builtin&&<Button variant={exam.shown?'outline':'default'} disabled={busy} onClick={()=>run(()=>patch('/admin/catalog/exams/'+slug,{shown:!exam.shown}),exam.shown?`${exam.name} phir se students se chhup gaya.`:`${exam.name} ab Home par dikh raha hai.`)} data-testid="master-exam-visibility">{exam.shown?<><EyeOff size={16}/>Home se chhupao</>:<><Home size={16}/>Home par dikhao</>}</Button>}
   {!exam.builtin&&<Button variant="ghost" onClick={()=>setDialog('rename')} data-testid="master-exam-rename"><Pencil size={16}/>Naam badlo</Button>}
   <Button asChild variant="outline"><Link to={'/exams/'+slug} data-testid="master-exam-student-view"><Eye size={16}/>Student ki tarah dekho</Link></Button>
  </div>}/>
  {!exam.builtin&&!exam.shown&&<p className="admin-note warn" data-testid="master-exam-hidden-note">Jab tak aap Home par dikhao nahi dabate, yeh students se chhupa rahega, link se bhi.</p>}
  <section className="admin-panel">
   <div className="admin-panel-head"><div><h2>Mock types, students wale order mein</h2><p>Students ko type tabhi dikhta hai jab usme kam se kam ek Live mock ho.</p></div><Button onClick={()=>setDialog('type')} data-testid="master-add-type"><Plus size={16}/>Mock type jodo</Button></div>
   {exam.sections.length?<ol className="admin-list" data-testid="master-type-list">{exam.sections.map((s,i)=><TypeRow key={s.id} s={s} i={i} total={exam.sections.length} exam={exam} busy={busy} waiting={waiting[s.id]} onMove={move} onSettings={()=>setDialog({settings:s})}
    onHide={()=>run(()=>patch('/admin/catalog/sections/'+s.id,{hidden:!s.hidden}),s.hidden?`${s.name} Live mock aate hi phir dikhega.`:`${s.name} students se chhup gaya.`)}/>)}</ol>
    :<div className="admin-empty" data-testid="master-no-types"><p>Abhi koi mock type nahi. PYQ, Mock, Chapter-wise, All India Test Series ya apna type jodiye.</p></div>}
   <ul className="admin-list admin-extra-rows">
    <li className="admin-row"><div className="admin-row-main"><strong>Results</strong><small>Har exam mein students ko hamesha dikhta hai.</small></div></li>
    {exam.unplaced>0&&<li className="admin-row" data-testid="master-unplaced-row"><div className="admin-row-main"><strong>Kisi type mein nahi ({exam.unplaced})</strong><small>Purane tests jo kisi type ki list mein nahi. Har ek ko sahi jagah rakhiye.</small></div><Button asChild variant="outline"><Link to={`/super-admin/exam/${slug}/unplaced`} data-testid="master-unplaced-open"><FolderOpen size={16}/>Kholo</Link></Button></li>}
   </ul>
  </section>
  <TypeDialog open={dialog==='type'} onClose={()=>setDialog(null)} exam={exam} onCreated={()=>setReload(n=>n+1)}/>
  <TypeSettings open={!!dialog?.settings} onClose={()=>setDialog(null)} type={dialog?.settings} onSaved={()=>setReload(n=>n+1)}/>
  <TextDialog open={dialog==='rename'} onClose={()=>setDialog(null)} title="Exam ka naam badlo" label="Exam ka naam" value={exam.name} maxLength={60} testId="exam-rename-dialog" onSave={name=>run(()=>patch('/admin/catalog/exams/'+slug,{name}),'Exam ka naam save ho gaya.')}/>
 </div>;
}
