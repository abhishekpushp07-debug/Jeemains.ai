import React,{useEffect,useRef,useState} from 'react';
import {Link,useNavigate,useSearchParams} from 'react-router-dom';
import {ArrowLeft,ArrowRight,Plus,BookOpen,FileText,FileSpreadsheet,Layers3,Download,Loader2,CheckCircle2} from 'lucide-react';
import {api,downloadFile} from '../../lib/api';
import {Button} from '../../components/ui/button';
import {Skeleton} from '../../components/ui/skeleton';
import {ErrorBox} from '../../components/Shared';
import {AdminCrumbs,AdminHeading,StepBar,DestinationChip,StudentPath,StatusChip,ExamDialog,SectionDialog} from '../../components/admin/AdminShared';
import {BookUpload} from '../../components/books/BookUpload';
import {SourcePicker} from '../StudioImport';
import {toast} from 'sonner';

const TYPES={
 book:{Icon:BookOpen,title:'Combined book with many mocks',text:'One PDF up to 100 MB. No page or mock limit. Each printed mock becomes its own test.',layouts:['list']},
 paper:{Icon:FileText,title:'One paper: questions + solutions PDFs',text:'Two searchable PDFs, up to 50 MB each. Becomes one test.',layouts:['list']},
 chapter:{Icon:Layers3,title:'Chapter book',text:'One PDF up to 50 MB. Each chapter becomes its own 50-question test.',layouts:['chapters']},
 excel:{Icon:FileSpreadsheet,title:'Excel workbook',text:'Questions, options, keys and solutions as text. Up to 300 questions.',layouts:['list','chapters']},
};

function Rights({checked,onChange}){
 return <label className="book-check" data-testid="wizard-rights-label"><input type="checkbox" data-testid="wizard-rights" checked={checked} onChange={e=>onChange(e.target.checked)}/><span>I have permission to upload and share these questions, explanations and student reports.</span></label>;
}

function FileForm({type,section,replace,onDone}){
 const [questions,setQuestions]=useState(null),[solutions,setSolutions]=useState(null),[two,setTwo]=useState(false),[rights,setRights]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');const key=useRef(null);
 const pdf=type==='paper',needSecond=pdf||(type==='excel'&&two);
 function pick(setter){return f=>{setter(f);key.current=null;setError('');};}
 async function send(){setBusy(true);setError('');key.current ||= crypto.randomUUID();const form=new FormData();form.append('request_id',key.current);form.append('section_id',section.id);
  try{if(replace)form.append('replace',replace);
   if(type==='chapter'){form.append('file',questions);const r=await api('/studio/chapter-books',{method:'POST',body:form});onDone({id:r.id,link:'/studio/chapter-books/'+r.id,title:r.title});}
   else{form.append('format',pdf?'pdf':'xlsx');form.append('questions',questions);if(needSecond)form.append('solutions',solutions);const r=await api('/studio/imports',{method:'POST',body:form});onDone({id:r.id,link:'/studio/imports/'+r.id,title:r.title});}
  }catch(e){setError(e.message);}finally{setBusy(false);}}
 const template=variant=>downloadFile('/studio/imports/template?variant='+variant,`jeelive-ai-${variant}-template.xlsx`).catch(e=>toast.error(e.message));
 return <div className="admin-panel" data-testid={'wizard-form-'+type}>
  {type==='excel'&&<div className="admin-actions"><Button variant="outline" onClick={()=>template(two?'sheets':'combined')} data-testid="wizard-excel-template"><Download size={16}/>{two?'Two-file templates':'Combined template'}</Button><label className="book-check"><input type="checkbox" checked={two} onChange={e=>{setTwo(e.target.checked);setSolutions(null);}} data-testid="wizard-excel-two-files"/><span>Solutions are in a separate workbook</span></label></div>}
  <div className="import-dropzones">
   <SourcePicker role="questions" title={type==='chapter'?'Chapter book PDF':pdf?'Questions PDF':two?'Questions workbook':'Questions + solutions workbook'} format={type==='excel'?'xlsx':'pdf'} file={questions} onChange={pick(setQuestions)} disabled={busy}/>
   {needSecond&&<SourcePicker role="solutions" title={pdf?'Solutions PDF':'Solutions workbook'} format={pdf?'pdf':'xlsx'} file={solutions} onChange={pick(setSolutions)} disabled={busy}/>}
  </div>
  <p className="admin-note">The test name comes from the file name. You can rename it later in Exams & Content.</p>
  <Rights checked={rights} onChange={setRights}/>
  <ErrorBox error={error}/>
  <Button disabled={busy||!rights||!questions||(needSecond&&!solutions)} onClick={send} data-testid="wizard-upload-files">{busy?<><Loader2 size={16} className="spin"/>Uploading privately…</>:<>Upload<ArrowRight size={16}/></>}</Button>
 </div>;
}

function ExistingList({section}){
 const [items,setItems]=useState(null);
 useEffect(()=>{api(`/admin/catalog/sections/${section.id}/tests`).then(d=>setItems(d.items)).catch(()=>setItems([]));},[section.id]);
 if(!items)return <Skeleton className="h-24"/>;
 return <ol className="admin-list admin-preview-list" data-testid="wizard-existing-list">{items.map((t,i)=><li key={t.id} className="admin-row is-existing"><span className="admin-test-index">{String(i+1).padStart(2,'0')}</span><div className="admin-row-main"><strong>{t.title}</strong><small>Already in this section</small></div><StatusChip state={t.state}/></li>)}</ol>;
}

function Done({exam,section,done}){
 if(section.kind==='series')return <section className="admin-panel admin-preview" data-testid="wizard-done"><span className="eyebrow">ALL INDIA TEST SERIES</span><div className="admin-row is-new" data-testid="wizard-new-item"><CheckCircle2 size={18}/><div className="admin-row-main"><strong>{done.title}</strong><small>Being organised privately. When it is ready, give it a day in Schedule & Live. Students see it only on that day.</small></div><StatusChip state="queued"/></div><div className="admin-actions"><Button asChild><Link to="/super-admin/schedule" data-testid="wizard-open-schedule">Open Schedule & Live<ArrowRight size={16}/></Link></Button><Button asChild variant="outline"><Link to={done.link} data-testid="wizard-open-review">Review the upload</Link></Button></div></section>;
 return <section className="admin-panel admin-preview" data-testid="wizard-done">
  <span className="eyebrow">STUDENTS WILL SEE IT LIKE THIS</span>
  <StudentPath exam={exam.name} section={section.name}/>
  <ExistingList section={section}/>
  <div className="admin-row is-new" data-testid="wizard-new-item"><CheckCircle2 size={18}/><div className="admin-row-main"><strong>{done.title}</strong><small>Being organised privately. It joins this list after you review and schedule or publish it.</small></div><StatusChip state="queued"/></div>
  <div className="admin-actions"><Button asChild><Link to={done.link} data-testid="wizard-open-review">Open review & publishing<ArrowRight size={16}/></Link></Button><Button asChild variant="outline"><Link to="/super-admin/upload/new" data-testid="wizard-add-another">Add more content</Link></Button></div>
 </section>;
}

export const AITS={id:'jee-main:aits',slug:'aits',name:'All India Test Series',layout:'list',kind:'series',counts:{live:0,total:0}};

function ReplaceNote({replace,section}){
 const count=replace.split(',').length;
 const n=replace==='all'?'every test':`${count} test${count===1?'':'s'}`;
 return <p className="admin-note warn admin-replace-note" data-testid="wizard-replace-note">Replacing {n} in {section.name}. They stay live until this new upload is published, then move to your Library. Students keep their old scores.</p>;
}

export default function UploadWizard(){
 const [params,setParams]=useSearchParams();const nav=useNavigate();
 const [catalog,setCatalog]=useState(null),[error,setError]=useState(''),[reload,setReload]=useState(0),[dialog,setDialog]=useState(null),[done,setDone]=useState(null);
 useEffect(()=>{api('/admin/catalog').then(d=>{setCatalog(d);setError('');}).catch(e=>setError(e.message));},[reload]);
 const exam=catalog?.items.find(e=>e.slug===params.get('exam'));
 const sections=exam?(exam.slug==='jee-main'?[...exam.sections,AITS]:exam.sections):[];
 const section=sections.find(s=>s.id===params.get('section'));
 const replace=section&&section.kind!=='series'?params.get('replace')||'':'';
 const type=section&&TYPES[params.get('type')]?.layouts.includes(section.layout)?params.get('type'):'';
 const step=done?5:!section?1:!type?2:Number(params.get('step'))===3?3:2;
 function go(values){const next=new URLSearchParams(params);Object.entries(values).forEach(([k,v])=>v?next.set(k,v):next.delete(k));setParams(next);}
 const crumbs=[{label:'Super Admin',to:'/super-admin'},{label:'Upload',to:'/super-admin/upload'},{label:'Add content'}];
 return <div className="admin-page" data-testid="upload-wizard">
  <AdminCrumbs items={crumbs}/>
  <AdminHeading testId="upload-wizard-title" title={step===1?'Where does it go?':step===2?'What kind of file?':step===3?'Details':'Uploaded.'} text="Choose the place first, then the file. Nothing goes live on its own."/>
  <StepBar step={step}/>
  {section&&<DestinationChip large exam={exam.name} section={section.name} testId="wizard-destination"/>}
  {replace&&<ReplaceNote replace={replace} section={section}/>}
  <ErrorBox error={error} retry={()=>setReload(n=>n+1)}/>
  {!catalog&&!error&&<Skeleton className="h-64"/>}
  {catalog&&step===1&&<section className="admin-panel" data-testid="wizard-step-place">
   <h2>Exam</h2>
   <div className="admin-choice-row" role="radiogroup" aria-label="Exam">{catalog.items.map(e=><button type="button" role="radio" aria-checked={exam?.slug===e.slug} key={e.slug} className={'admin-pill'+(exam?.slug===e.slug?' is-picked':'')} onClick={()=>go({exam:e.slug,section:null,type:null,step:null,replace:null})} data-testid={'wizard-exam-'+e.slug}>{e.name}{!e.shown&&<small> · hidden</small>}</button>)}<button type="button" className="admin-pill is-add" onClick={()=>setDialog('exam')} data-testid="wizard-new-exam"><Plus size={15}/>New exam</button></div>
   {exam&&<><h2>Section in {exam.name}</h2><div className="admin-choice-grid" role="radiogroup" aria-label="Section">{sections.map(s=>{const locked=s.kind==='pyq';return <button type="button" role="radio" aria-checked={false} key={s.id} disabled={locked} className={'admin-choice'+(s.kind==='series'?' is-series':'')} onClick={()=>go({section:s.id,type:null,step:null,replace:null})} data-testid={'wizard-section-'+s.slug}><strong>{s.name}</strong><small>{locked?'Filled only by the verified PYQ import.':s.kind==='series'?'62 daily papers · a book of full mocks or one paper':`${s.layout==='chapters'?'Subject › chapter':'Simple list'} · ${s.counts.live} live`}</small></button>;})}<button type="button" className="admin-choice is-add" onClick={()=>setDialog('section')} data-testid="wizard-new-section"><Plus size={18}/><strong>New section</strong><small>For example Revision Tests or Crash Course.</small></button></div></>}
   {!exam&&<p className="admin-note" data-testid="wizard-pick-exam">Pick an exam to see its sections.</p>}
  </section>}
  {step===2&&<section className="admin-panel" data-testid="wizard-step-type">
   <div className="admin-choice-grid">{Object.entries(TYPES).filter(([,t])=>t.layouts.includes(section.layout)).map(([key,t])=><button type="button" key={key} className={'admin-choice'+(type===key?' is-picked':'')} onClick={()=>go({type:key,step:'3'})} data-testid={'wizard-type-'+key}><t.Icon size={22}/><strong>{t.title}</strong><small>{t.text}</small></button>)}</div>
   <Button variant="ghost" onClick={()=>go({section:null,type:null,step:null,replace:null})} data-testid="wizard-back-place"><ArrowLeft size={16}/>Change place</Button>
  </section>}
  {step===3&&<>{type==='book'?<BookUpload sectionId={section.id} replace={replace} onOpen={id=>nav('/super-admin/upload?book='+id)}/>:<FileForm type={type} section={section} replace={replace} onDone={setDone}/>}
   <Button variant="ghost" onClick={()=>go({type:null,step:null})} data-testid="wizard-back-type"><ArrowLeft size={16}/>Change file type</Button></>}
  {step===5&&<Done exam={exam} section={section} done={done}/>}
  <ExamDialog open={dialog==='exam'} onClose={()=>setDialog(null)} onCreated={e=>{go({exam:e.slug,section:null,type:null,step:null});setReload(n=>n+1);}}/>
  {exam&&<SectionDialog open={dialog==='section'} onClose={()=>setDialog(null)} exam={exam} onCreated={s=>{go({section:s.id,type:null,step:null});setReload(n=>n+1);}}/>}
 </div>;
}
