import React,{useEffect,useState} from 'react';
import {Link,useParams,useSearchParams} from 'react-router-dom';
import {ArrowLeft,ArrowRight,Atom,FlaskConical,Calculator,BookOpen,Search} from 'lucide-react';
import {api} from '../lib/api';
import {examBySlug} from '../lib/exams';
import {ExamBreadcrumbs,NavigationCard} from '../components/exams/ExamNavigation';
import {SetCard,SetRow} from './Exams';
import {Empty,ErrorBox} from '../components/Shared';
import {Button} from '../components/ui/button';
import {Input} from '../components/ui/input';
import {Skeleton} from '../components/ui/skeleton';

export default function ExamSection({kind='chapters'}){
 const {examSlug}=useParams(),exam=examBySlug(examSlug);const [params,setParams]=useSearchParams();
 const subject=params.get('subject')||'',q=params.get('q')||'',page=Math.max(1,Math.min(10000,Number(params.get('page'))||1));
 const [data,setData]=useState(null),[error,setError]=useState(''),[reload,setReload]=useState(0);
 const [search,setSearch]=useState(q);
 useEffect(()=>setSearch(q),[q]);
 useEffect(()=>{
  if(!exam)return;const controller=new AbortController();setData(null);setError('');
  const query=new URLSearchParams({kind,subject,q,page});
  api(`/exam-navigation/${exam.slug}/catalogue?${query}`,{signal:controller.signal}).then(d=>{if(!controller.signal.aborted)setData(d)}).catch(e=>{if(!controller.signal.aborted)setError(e.message)});
  return()=>controller.abort();
 },[exam,kind,subject,q,page,reload]);
 if(!exam)return <div className="container page"><Empty title="Exam not found." action={<Button asChild><Link to="/home" data-testid="catalogue-invalid-exam-home">Choose your exam</Link></Button>}/></div>;
 const chapters=kind==='chapters',base=`/exams/${examSlug}/${kind}`,label=chapters?'Chapter-wise Tests':'Mock Tests';
 const subjects=Object.entries(data?.subject_counts||{}).sort((a,b)=>{const order=['Physics','Chemistry','Mathematics'];const ai=order.indexOf(a[0]),bi=order.indexOf(b[0]);return(ai<0?99:ai)-(bi<0?99:bi)||a[0].localeCompare(b[0])});
 const pickingSubject=chapters&&!subject;
 function update(values){const next=new URLSearchParams(params);Object.entries(values).forEach(([k,v])=>v?next.set(k,String(v)):next.delete(k));setParams(next)}
 return <div className="container page exam-section" data-testid={'exam-section-'+kind}>
  <ExamBreadcrumbs exam={exam} section={{label,to:base}} subject={subject}/>
  <header className="exam-simple-heading"><span className="eyebrow" data-testid="exam-section-exam">{exam.name}</span><h1 data-testid="exam-section-title">{pickingSubject?'Choose a subject.':subject?subject:label}</h1><p data-testid="exam-section-description">{pickingSubject?'Start with one subject. Find your next chapter.':chapters?'Pick a chapter. Check its rules, then begin.':'Only live full-length mock tests for this exam appear here.'}</p></header>
  <ErrorBox error={error} retry={()=>setReload(n=>n+1)}/>
  {pickingSubject?<>
   {!data&&!error&&<div className="exam-choice-grid" data-testid="subjects-loading">{[1,2,3].map(n=><Skeleton key={n} className="h-56"/>)}</div>}
   {data&&subjects.length>0&&<div className="exam-choice-grid subject-choice-grid" data-testid="chapters-subject-grid">{subjects.map(([name,count],i)=><NavigationCard key={name} to={base+'?subject='+encodeURIComponent(name)} title={name} description={`${count} live chapter test${count===1?'':'s'}`} Icon={{Physics:Atom,Chemistry:FlaskConical,Mathematics:Calculator}[name]||BookOpen} testId={'chapters-subject-'+name.toLowerCase().replace(/\s+/g,'-')} index={'0'+(i+1)}/>)}</div>}
   {data&&!subjects.length&&<Empty title="Chapter tests are not live yet." action={<Button asChild variant="outline"><Link to={'/exams/'+examSlug} data-testid="chapters-empty-back">Back to {exam.name}</Link></Button>}>Reviewed {exam.name} chapters will appear here when published. Tests from other exams are kept separate.</Empty>}
  </>:<>
   <form className="exam-section-search" onSubmit={e=>{e.preventDefault();update({q:search.trim(),page:null})}} data-testid="exam-section-search-form"><Search size={18}/><Input value={search} onChange={e=>setSearch(e.target.value)} maxLength={100} placeholder={chapters?'Find a chapter…':'Find a mock test…'} aria-label="Search available tests" data-testid="exams-search-input"/><Button type="submit" variant="outline" data-testid="exam-section-search-submit">Search</Button>{q&&<Button type="button" variant="ghost" onClick={()=>update({q:null,page:null})} data-testid="exam-section-clear-search">Clear</Button>}</form>
   {!data&&!error&&<div className="exam-library-list" data-testid="exam-section-loading">{[1,2,3].map(n=><Skeleton key={n} className="h-28"/>)}</div>}
   {data?.items.length>0&&<><div className="exam-library-count"><p aria-live="polite" data-testid="exam-result-count">{data.total} live {chapters?'chapter tests':'mock tests'}</p>{chapters&&<Button asChild variant="ghost"><Link to={base} data-testid="chapters-change-subject"><ArrowLeft size={16}/>Subjects</Link></Button>}</div><div className={chapters?'exam-library-list':'set-grid'} data-testid={chapters?'chapters-chapter-list':'mocks-list'}>{data.items.map(s=>chapters?<SetRow key={s.id} s={s}/>:<SetCard key={s.id} s={s}/>)}</div></>}
   {data&&!data.items.length&&<Empty title={q?'No matching tests.':chapters?'No live tests for this subject.':'Full-length mocks are not live yet.'} action={<Button asChild variant="outline"><Link to={chapters?base:'/exams/'+examSlug} data-testid="exam-section-empty-back">{chapters?'Choose a subject':'Back to '+exam.name}</Link></Button>}>{q?'Try another search.':`Reviewed ${exam.name} papers will appear here when published. No sample or chapter tests are shown as full mocks.`}</Empty>}
   {data&&data.pages>1&&<nav className="chapter-pagination" aria-label="Test pages"><Button variant="outline" data-testid="catalog-prev" disabled={page<=1} onClick={()=>update({page:page-1})}>Previous</Button><span data-testid="catalog-page">Page {page} of {data.pages}</span><Button variant="outline" data-testid="catalog-next" disabled={page>=data.pages} onClick={()=>update({page:page+1})}>Next<ArrowRight size={16}/></Button></nav>}
  </>}
 </div>;
}
