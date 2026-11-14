import React,{useEffect,useState} from 'react';
import {Link,useSearchParams} from 'react-router-dom';
import {Plus,ArrowUp,ArrowDown,Pencil,Eye,EyeOff,Home,ChevronRight,CalendarClock,FolderOpen,RefreshCw,Archive,UploadCloud} from 'lucide-react';
import {api,post,patch} from '../../lib/api';
import {invalidateCatalog} from '../../lib/catalog';
import {Button} from '../../components/ui/button';
import {Skeleton} from '../../components/ui/skeleton';
import {ErrorBox} from '../../components/Shared';
import {AdminCrumbs,AdminHeading,StatusChip,StudentPath,ExamDialog,SectionDialog,TextDialog,ConfirmDialog} from '../../components/admin/AdminShared';
import {SectionTests} from '../../components/admin/SectionTests';
import {WaitingList} from '../../components/admin/WaitingList';
import {ContentTools} from './ContentTools';
import {PreviewLink} from '../../components/admin/PreviewLink';
import {toast} from 'sonner';

function SectionRow({s,i,total,busy,onOpen,onMove,onRename,onHide}){
 return <li className="admin-row admin-section-row" data-testid={'admin-section-'+s.slug}>
  <button type="button" className="admin-row-main admin-row-button" onClick={onOpen} data-testid={'admin-section-open-'+s.slug}><strong>{s.name}</strong><small>{s.layout==='chapters'?'Subject › chapter':'Simple list'} · {s.counts.total} test{s.counts.total===1?'':'s'} · {s.counts.live} live{s.counts.draft?` · ${s.counts.draft} draft`:''}</small></button>
  {s.hidden?<StatusChip state="hidden" testId={'admin-section-state-'+s.slug}/>:s.counts.live?<StatusChip state="live" label="Students see it" testId={'admin-section-state-'+s.slug}/>:<StatusChip state="paused" label="Not shown: no live test" testId={'admin-section-state-'+s.slug}/>}
  <div className="admin-test-actions">
   <Button size="icon" variant="ghost" aria-label={'Move '+s.name+' up'} disabled={busy||i===0} onClick={()=>onMove(i,-1)} data-testid={'admin-section-up-'+s.slug}><ArrowUp size={16}/></Button>
   <Button size="icon" variant="ghost" aria-label={'Move '+s.name+' down'} disabled={busy||i===total-1} onClick={()=>onMove(i,1)} data-testid={'admin-section-down-'+s.slug}><ArrowDown size={16}/></Button>
   <Button size="icon" variant="ghost" aria-label={'Rename '+s.name} disabled={busy} onClick={onRename} data-testid={'admin-section-rename-'+s.slug}><Pencil size={16}/></Button>
   <Button variant="ghost" disabled={busy} onClick={onHide} data-testid={'admin-section-hide-'+s.slug}>{s.hidden?<><Eye size={16}/>Show</>:<><EyeOff size={16}/>Hide</>}</Button>
   <Button variant="outline" onClick={onOpen} data-testid={'admin-section-tests-'+s.slug}>Tests<ChevronRight size={16}/></Button>
  </div>
 </li>;
}

function ExamPanel({exam,busy,run,open}){
 const [dialog,setDialog]=useState(null);
 function move(i,d){const ids=exam.sections.map(s=>s.id);[ids[i],ids[i+d]]=[ids[i+d],ids[i]];run(()=>post(`/admin/catalog/exams/${exam.slug}/sections/order`,{ids}),'Section order saved.');}
 return <section className="admin-panel" data-testid={'admin-exam-panel-'+exam.slug}>
  <div className="admin-panel-head"><div><h2 data-testid="admin-exam-name">{exam.name}</h2><p>{exam.subjects.join(' · ')}</p></div>
   <div className="admin-actions">
    {!exam.builtin&&<Button variant={exam.shown?'outline':'default'} disabled={busy} onClick={()=>run(()=>patch('/admin/catalog/exams/'+exam.slug,{shown:!exam.shown}),exam.shown?`${exam.name} is hidden from students again.`:`${exam.name} now shows on Home.`)} data-testid="admin-exam-visibility">{exam.shown?<><EyeOff size={16}/>Hide from Home</>:<><Home size={16}/>Show on Home</>}</Button>}
    {!exam.builtin&&<Button variant="ghost" disabled={busy} onClick={()=>setDialog('rename')} data-testid="admin-exam-rename"><Pencil size={16}/>Rename</Button>}
    <Button asChild variant="outline"><Link to={'/exams/'+exam.slug} data-testid="admin-exam-student-view"><Eye size={16}/>View as student</Link></Button>
   </div></div>
  {!exam.builtin&&<p className="admin-note" data-testid="admin-exam-visibility-note">{exam.shown?'Students can see this exam on Home.':'Hidden from students, even through links. Live tests stay private until you choose Show on Home.'}</p>}
  <div className="admin-panel-head"><h3>Sections, in student order</h3><Button variant="outline" onClick={()=>setDialog('section')} data-testid="admin-new-section"><Plus size={16}/>New section</Button></div>
  {exam.sections.length?<ol className="admin-list" data-testid="admin-section-list">{exam.sections.map((s,i)=><SectionRow key={s.id} s={s} i={i} total={exam.sections.length} busy={busy} onOpen={()=>open(s.id)} onMove={move} onRename={()=>setDialog({rename:s})} onHide={()=>run(()=>patch('/admin/catalog/sections/'+s.id,{hidden:!s.hidden}),s.hidden?`${s.name} will show when it has a live test.`:`${s.name} is hidden from students.`)}/>)}</ol>:<div className="admin-empty" data-testid="admin-no-sections"><p>No sections yet. Create one, then add content to it.</p></div>}
  <ul className="admin-list admin-extra-rows">
   <li className="admin-row"><div className="admin-row-main"><strong>Results</strong><small>Always shown to students in every exam.</small></div></li>
   {exam.slug==='jee-main'&&<li className="admin-row" data-testid="admin-series-row"><div className="admin-row-main"><strong>All India Test Series</strong><small>62 daily papers, 1 Dec – 31 Jan. Upload a book of full mocks or one paper, then give each a day.</small></div><div className="admin-test-actions"><Button asChild><Link to="/super-admin/upload/new?exam=jee-main&section=jee-main:aits" data-testid="admin-series-add"><UploadCloud size={16}/>Upload book or paper</Link></Button><Button asChild variant="outline"><Link to="/super-admin/schedule" data-testid="admin-series-open"><CalendarClock size={16}/>Days</Link></Button></div></li>}
   {exam.unplaced>0&&<li className="admin-row" data-testid="admin-unplaced-row"><div className="admin-row-main"><strong>Not in any section ({exam.unplaced})</strong><small>Practice or competition tests that no section lists. Move them where they belong.</small></div><Button variant="outline" onClick={()=>open('unplaced')} data-testid="admin-unplaced-open"><FolderOpen size={16}/>Review</Button></li>}
  </ul>
  <SectionDialog open={dialog==='section'} onClose={()=>setDialog(null)} exam={exam} onCreated={()=>run(async()=>{})}/>
  <TextDialog open={dialog==='rename'} onClose={()=>setDialog(null)} title="Rename exam" label="Exam name" value={exam.name} maxLength={60} testId="exam-rename-dialog" onSave={name=>run(()=>patch('/admin/catalog/exams/'+exam.slug,{name}),'Exam name saved.')}/>
  <TextDialog open={!!dialog?.rename} onClose={()=>setDialog(null)} title="Rename section" label="Section name" value={dialog?.rename?.name} maxLength={60} testId="section-rename-dialog" onSave={name=>run(()=>patch('/admin/catalog/sections/'+dialog.rename.id,{name}),'Section name saved.')}/>
 </section>;
}

function SectionPanel({exam,section,onChanged}){
 const [version,setVersion]=useState(0),[confirm,setConfirm]=useState(false),[busy,setBusy]=useState(false);
 if(section==='unplaced')return <section className="admin-panel" data-testid="admin-unplaced-panel"><div className="admin-panel-head"><div><h2>Not in any section</h2><p>Students reach these only through competitions or saved links. Use Move to place them.</p></div></div><SectionTests exam={exam} path={`/admin/catalog/exams/${exam.slug}/unplaced`} onChanged={onChanged}/></section>;
 const changed=()=>{setVersion(n=>n+1);onChanged();};
 const open=section.kind!=='pyq';
 async function archiveAll(){setBusy(true);try{const r=await post('/admin/library/archive',{section_id:section.id});invalidateCatalog();toast.success(r.message);setConfirm(false);changed();}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 return <section className="admin-panel" data-testid={'admin-section-panel-'+section.slug}>
  <div className="admin-panel-head"><div><h2 data-testid="admin-section-name">{section.name}</h2><StudentPath exam={exam.name} section={section.name}/>{section.description&&<p>{section.description}</p>}</div>
   <div className="admin-actions"><PreviewLink section={section} exam={exam}/>{open&&<Button asChild><Link to={`/super-admin/upload/new?exam=${exam.slug}&section=${section.id}`} data-testid="admin-section-add-content"><Plus size={16}/>Add content here</Link></Button>}</div></div>
  {open&&section.counts?.total>0&&<div className="admin-actions" data-testid="admin-section-replace-actions"><Button asChild variant="outline"><Link to={`/super-admin/upload/new?exam=${exam.slug}&section=${section.id}&replace=all`} data-testid="admin-section-replace-all"><RefreshCw size={16}/>Replace all with a new upload</Link></Button><Button variant="outline" onClick={()=>setConfirm(true)} data-testid="admin-section-archive-all"><Archive size={16}/>Move all to Library</Button></div>}
  {section.hidden&&<p className="admin-note warn" data-testid="admin-section-hidden-note">This section is hidden from students.</p>}
  {open&&<WaitingList key={'w'+version} sectionId={section.id} onChanged={changed}/>}
  <SectionTests key={version} section={section} exam={exam} path={`/admin/catalog/sections/${section.id}/tests`} onChanged={onChanged}/>
  <ConfirmDialog open={confirm} onClose={()=>setConfirm(false)} busy={busy} onConfirm={archiveAll} testId="archive-all-confirm" title={`Move everything in ${section.name} to the Library?`} text="Students stop seeing these tests on the website and the app. Everyone keeps their old scores. Uploads waiting for this section go to the Library too. You can restore any test later." button="Move all to Library"/>
 </section>;
}

export default function AdminContent(){
 const [params,setParams]=useSearchParams();
 const [data,setData]=useState(null),[error,setError]=useState(''),[reload,setReload]=useState(0),[busy,setBusy]=useState(false),[examDialog,setExamDialog]=useState(false);
 useEffect(()=>{api('/admin/catalog').then(d=>{setData(d);setError('');}).catch(e=>setError(e.message));},[reload]);
 async function run(fn,message){setBusy(true);try{await fn();invalidateCatalog();if(message)toast.success(message);setReload(n=>n+1);}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 const exam=data?.items.find(e=>e.slug===params.get('exam'))||data?.items[0];
 const sid=params.get('section');const section=sid==='unplaced'?'unplaced':exam?.sections.find(s=>s.id===sid);
 const crumbs=[{label:'Super Admin',to:'/super-admin'},{label:'Exams & Content',to:'/super-admin/content'},...(exam?[{label:exam.name,to:'/super-admin/content?exam='+exam.slug}]:[]),...(section?[{label:section==='unplaced'?'Not in any section':section.name}]:[])];
 return <div className="admin-page" data-testid="admin-content-page">
  <AdminCrumbs items={crumbs}/>
  <AdminHeading testId="admin-content-title" title="Exams & Content" text="Exam › section › tests, in the same order students see on the website and the app." action={<Button onClick={()=>setExamDialog(true)} data-testid="admin-new-exam"><Plus size={16}/>New exam</Button>}/>
  <ErrorBox error={error} retry={()=>setReload(n=>n+1)}/>
  {!data&&!error?<Skeleton className="h-64"/>:data&&<>
   <div className="admin-exam-tabs" role="tablist" data-testid="admin-exam-tabs">{data.items.map(e=><button type="button" role="tab" key={e.slug} aria-selected={e.slug===exam?.slug} className={e.slug===exam?.slug?'is-active':''} onClick={()=>setParams({exam:e.slug})} data-testid={'admin-exam-tab-'+e.slug}>{e.name}{!e.shown&&<StatusChip state="hidden" testId={'admin-exam-hidden-'+e.slug}/>}</button>)}</div>
   {exam&&(section?<SectionPanel exam={exam} section={section} onChanged={()=>setReload(n=>n+1)}/>:<ExamPanel exam={exam} busy={busy} run={run} open={id=>setParams({exam:exam.slug,section:id})}/>)}
   {!section&&<ContentTools/>}
  </>}
  <ExamDialog open={examDialog} onClose={()=>setExamDialog(false)} onCreated={e=>{setParams({exam:e.slug});setReload(n=>n+1);}}/>
 </div>;
}
