import React,{useEffect,useRef,useState} from 'react';
import {Link,useNavigate,useParams} from 'react-router-dom';
import {Plus,ClipboardPaste,Loader2,ArrowLeft,FileSpreadsheet,Download} from 'lucide-react';
import {api,post,downloadFile} from '../../../lib/api';
import {useAuth} from '../../../lib/auth';
import {Button} from '../../../components/ui/button';
import {Textarea} from '../../../components/ui/textarea';
import {Skeleton} from '../../../components/ui/skeleton';
import {Tabs,TabsList,TabsTrigger} from '../../../components/ui/tabs';
import {ErrorBox} from '../../../components/Shared';
import {AdminCrumbs,AdminHeading} from '../../../components/admin/AdminShared';
import {QuestionForm} from '../../../components/master/QuestionForm';
import {STATUS,plural} from '../../../components/master/MasterShared';
import {toast} from 'sonner';

function PasteBox({mock,onDone,disabled}){
 const [text,setText]=useState(''),[busy,setBusy]=useState(false);const file=useRef(null);
 async function excel(f){if(!f)return;setBusy(true);try{const form=new FormData();form.append('file',f);const r=await api(`/admin/master/written/${mock.id}/excel`,{method:'POST',body:form});toast.success(r.message);onDone();}catch(e){toast.error(e.message);}finally{setBusy(false);if(file.current)file.current.value='';}}
 async function send(){setBusy(true);try{const r=await post(`/admin/master/written/${mock.id}/paste`,{text});toast.success(r.message);setText('');onDone();}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 return <section className="admin-panel" data-testid="paste-panel">
  <h2>Paste the whole paper</h2>
  <p className="master-hint">Number each question (1. or Q1.), options as (A)–(D) or (1)–(4), and either “Answer: B” under a question or an “Answer Key” list at the end. A “Solutions” part is optional. Subject headings like Physics split the paper. Anything unclear is marked to fix.</p>
  <Textarea rows={14} value={text} onChange={e=>setText(e.target.value)} placeholder={'Physics\n1. A ball is thrown…\n(A) 2 m/s (B) 4 m/s (C) 6 m/s (D) 8 m/s\nAnswer: B\n\nAnswer Key\n1. B  2. 14'} data-testid="paste-text"/>
  <div className="button-row"><Button disabled={busy||disabled||text.trim().length<10} onClick={send} data-testid="paste-send">{busy?<Loader2 size={16} className="spin"/>:<ClipboardPaste size={16}/>}Split into questions</Button></div>
  {disabled&&<p className="admin-note">A Live mock changes one complete question at a time. Use One question.</p>}
  <p className="master-excel" data-testid="write-excel"><FileSpreadsheet size={15} aria-hidden="true"/>Questions already in Excel?<Button type="button" variant="link" size="sm" disabled={busy||disabled} onClick={()=>file.current?.click()} data-testid="write-excel-upload">Import from Excel</Button><Button type="button" variant="link" size="sm" onClick={()=>downloadFile('/studio/imports/template?variant=combined','jeelive-excel-template.xlsx').catch(e=>toast.error(e.message))} data-testid="write-excel-template"><Download size={13}/>Template</Button><input ref={file} type="file" hidden accept=".xlsx" onChange={e=>excel(e.target.files[0])} data-testid="write-excel-input"/></p>
 </section>;
}

export default function WriteEditor(){
 const {id}=useParams();const {user}=useAuth();const nav=useNavigate();const owner=user.role==='owner';
 const [data,setData]=useState(null),[error,setError]=useState(''),[reload,setReload]=useState(0),[pick,setPick]=useState(owner?'new':''),[tab,setTab]=useState('one');
 useEffect(()=>{api('/admin/master/written/'+id).then(d=>{setData(d);setError('');if(!owner)setPick(p=>d.questions.some(x=>x.id===p)?p:(d.questions.find(x=>x.flag)||{}).id||'');}).catch(e=>setError(e.message));},[id,reload,owner]);
 if(error)return <ErrorBox error={error} retry={()=>setReload(n=>n+1)}/>;
 if(!data)return <Skeleton className="h-96"/>;
 const exam=data.exam_info||{},sec=data.section||{},q=data.questions.find(x=>x.id===pick),live=data.status==='published';
 const back=user.role==='owner'&&sec.id?`/super-admin/exam/${exam.slug}/${sec.id}`:'/super-admin/fix';
 const [label]=STATUS[data.state==='unlive'||data.state==='paused'?'off':data.state]||['Draft'];
 async function remove(){try{await api(`/admin/master/written/${id}/questions/${q.id}`,{method:'DELETE'});toast.success('Question removed.');setPick('new');setReload(n=>n+1);}catch(e){toast.error(e.message);}}
 const flagged=data.questions.filter(x=>x.flag).length;
 return <div className="admin-page master-page" data-testid="write-editor">
  <AdminCrumbs items={[{label:'Master',to:'/super-admin'},...(exam.slug&&user.role==='owner'?[{label:exam.name,to:'/super-admin/exam/'+exam.slug},{label:sec.name,to:back}]:[]),{label:data.title}]}/>
  <AdminHeading testId="write-title" title={data.title} text={[label,plural(data.questions.length,'question'),`${data.rules.minutes} min · +${data.rules.correct} / ${data.rules.wrong}`,data.pyq_year?`Year ${data.pyq_year}`:null,data.series_date?`Series day ${data.series_date}`:null].filter(Boolean).join(' · ')}
   action={<Button asChild variant="outline"><Link to={back} data-testid="write-back"><ArrowLeft size={16}/>Back to the list</Link></Button>}/>
  {data.problems.length>0&&<p className="admin-note warn" data-testid="write-problems">{data.problems[0]} It stays a Draft until then.</p>}
  {live&&<p className="admin-note" data-testid="write-live-note">This mock is Live. Each saved change becomes a new version; students who already took it keep their old paper and score.</p>}
  {owner&&<Tabs value={tab} onValueChange={setTab}><TabsList className="admin-tabs"><TabsTrigger value="one" data-testid="write-tab-one">One question</TabsTrigger><TabsTrigger value="paste" data-testid="write-tab-paste">Paste whole paper</TabsTrigger></TabsList></Tabs>}
  {tab==='paste'?<PasteBox mock={data} disabled={live} onDone={()=>{setTab('one');setReload(n=>n+1);}}/>:<div className="master-write">
   <aside className="master-qlist" data-testid="question-list">
    {owner&&<Button variant={pick==='new'?'default':'outline'} size="sm" onClick={()=>setPick('new')} data-testid="question-new"><Plus size={15}/>New question</Button>}
    {flagged>0&&<small className="master-flag-count" data-testid="question-flag-count">{flagged} to fix</small>}
    <ol>{data.questions.filter(x=>owner||x.flag).map(x=><li key={x.id}><button type="button" className={(pick===x.id?'is-picked ':'')+(x.flag?'is-flagged':'')} onClick={()=>setPick(x.id)} data-testid={'question-pick-'+x.number}><span>Q{x.number}</span><small>{x.subject}</small></button></li>)}</ol>
   </aside>
   {(owner||q)&&<QuestionForm key={pick+':'+data.revision} mock={data} question={q} subjects={exam.subjects||[]} onDelete={owner?remove:null}
    onSaved={r=>{if(!owner&&r.flags===0){toast.success('All marked questions are fixed.');nav('/super-admin');return;}if(q){const i=data.questions.findIndex(x=>x.id===q.id);const next=data.questions.slice(i+1).find(x=>x.flag)||data.questions[i+1];setPick(next?next.id:owner?'new':'');}setReload(n=>n+1);}}/>}
  </div>}
 </div>;
}
