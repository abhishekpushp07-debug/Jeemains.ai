import React,{useEffect,useState} from 'react';
import {Link,Navigate,useParams,useSearchParams} from 'react-router-dom';
import {ArrowLeft,ArrowRight,Atom,FlaskConical,Calculator,BookOpen,Search} from 'lucide-react';
import {api} from '../lib/api';
import {examBySlug} from '../lib/exams';
import {ExamBreadcrumbs,ExamDestinations,NavigationCard} from '../components/exams/ExamNavigation';
import {SetCard,SetRow} from './Exams';
import {Empty,ErrorBox} from '../components/Shared';
import {Button} from '../components/ui/button';
import {Input} from '../components/ui/input';
import {Skeleton} from '../components/ui/skeleton';

export default function ExamSection({kind='chapters'}){
 const {examSlug,sectionSlug}=useParams();const slug=sectionSlug||kind;const [params,setParams]=useSearchParams();
 const subject=params.get('subject')||'',q=params.get('q')||'',page=Math.max(1,Math.min(10000,Number(params.get('page'))||1));
 const [data,setData]=useState(null),[error,setError]=useState(''),[reload,setReload]=useState(0);
 const [search,setSearch]=useState(q);
 useEffect(()=>setSearch(q),[q]);
 useEffect(()=>{
  const controller=new AbortController();setData(null);setError('');
  const query=new URLSearchParams({section:slug,subject,q,page});
  api(`/exam-navigation/${examSlug}/catalogue?${query}`,{signal:controller.signal}).then(d=>{if(!controller.signal.aborted)setData(d)}).catch(e=>{if(!controller.signal.aborted)setError(e.message)});
  return()=>controller.abort();
 },[examSlug,slug,subject,q,page,reload]);
 const exam=examBySlug(examSlug)||(data&&{slug:examSlug,name:data.exam,custom:true});
 if(error&&!data&&/not available/i.test(error))return <div className="container page"><Empty title="This section is not available." action={<Button asChild><Link to={'/exams/'+examSlug} data-testid="catalogue-invalid-exam-home">Back to the exam</Link></Button>}>Choose another section from the exam page.</Empty></div>;
 if(examSlug==='jee-main'&&slug==='mocks'&&data&&!data.total&&!q)return <Navigate to="/exams/jee-main/pyq" replace/>;
 const chapters=data?data.section?.layout==='chapters':slug==='chapters',base=`/exams/${examSlug}/${slug}`,label=data?.section?.name||(chapters?'Chapter-wise Tests':'Mock Tests');
 const subjects=Object.entries(data?.subject_counts||{}).sort((a,b)=>{const order=['Physics','Chemistry','Mathematics'];const ai=order.indexOf(a[0]),bi=order.indexOf(b[0]);return(ai<0?99:ai)-(bi<0?99:bi)||a[0].localeCompare(b[0])});
 const pickingSubject=chapters&&!subject;
 const examName=exam?.name||'';
 function update(values){const next=new URLSearchParams(params);Object.entries(values).forEach(([k,v])=>v?next.set(k,String(v)):next.delete(k));setParams(next)}
 return <div className="container page exam-section" data-testid={'exam-section-'+(chapters?'chapters':'mocks')}>
  {exam&&<ExamBreadcrumbs exam={exam} section={{label,to:base}} subject={subject}/>}
  <header className="exam-simple-heading"><span className="eyebrow" data-testid="exam-section-exam">{examName}</span><h1 data-testid="exam-section-title">{pickingSubject?'Choose a subject.':subject?subject:label}</h1><p data-testid="exam-section-description">{pickingSubject?'Start with one subject. Find your next chapter.':data?.section?.description||(chapters?'Pick a chapter. Check its rules, then begin.':'Only live tests in this section appear here.')}</p></header>
  {exam&&<ExamDestinations exam={exam}/>}
  <ErrorBox error={error} retry={()=>setReload(n=>n+1)}/>
  {pickingSubject?<>
   {!data&&!error&&<div className="exam-choice-grid" data-testid="subjects-loading">{[1,2,3].map(n=><Skeleton key={n} className="h-56"/>)}</div>}
   {data&&subjects.length>0&&<div className="exam-choice-grid subject-choice-grid" data-testid="chapters-subject-grid">{subjects.map(([name,count],i)=><NavigationCard key={name} to={base+'?subject='+encodeURIComponent(name)} title={name} description={`${count} live chapter test${count===1?'':'s'}`} Icon={{Physics:Atom,Chemistry:FlaskConical,Mathematics:Calculator}[name]||BookOpen} testId={'chapters-subject-'+name.toLowerCase().replace(/\s+/g,'-')} index={'0'+(i+1)}/>)}</div>}
   {data&&!subjects.length&&<Empty title="Tests here are not live yet." action={<Button asChild variant="outline"><Link to={'/exams/'+examSlug} data-testid="chapters-empty-back">Back to {examName}</Link></Button>}>Reviewed {examName} tests will appear here when published. Tests from other exams are kept separate.</Empty>}
  </>:<>
   <form className="exam-section-search" onSubmit={e=>{e.preventDefault();update({q:search.trim(),page:null})}} data-testid="exam-section-search-form"><Search size={18}/><Input value={search} onChange={e=>setSearch(e.target.value)} maxLength={100} placeholder={chapters?'Find a chapter…':'Find a test…'} aria-label="Search available tests" data-testid="exams-search-input"/><Button type="submit" variant="outline" data-testid="exam-section-search-submit">Search</Button>{q&&<Button type="button" variant="ghost" onClick={()=>update({q:null,page:null})} data-testid="exam-section-clear-search">Clear</Button>}</form>
   {!data&&!error&&<div className="exam-library-list" data-testid="exam-section-loading">{[1,2,3].map(n=><Skeleton key={n} className="h-28"/>)}</div>}
   {data?.items.length>0&&<><div className="exam-library-count"><p aria-live="polite" data-testid="exam-result-count">{data.total} live {chapters?'chapter tests':'tests'}</p>{chapters&&<Button asChild variant="ghost"><Link to={base} data-testid="chapters-change-subject"><ArrowLeft size={16}/>Subjects</Link></Button>}</div><div className={chapters?'exam-library-list':'set-grid'} data-testid={chapters?'chapters-chapter-list':'mocks-list'}>{data.items.map(s=>chapters?<SetRow key={s.id} s={s}/>:<SetCard key={s.id} s={s}/>)}</div></>}
   {data&&!data.items.length&&<Empty title={q?'No matching tests.':chapters?'No live tests for this subject.':'Tests here are not live yet.'} action={<Button asChild variant="outline"><Link to={chapters?base:'/exams/'+examSlug} data-testid="exam-section-empty-back">{chapters?'Choose a subject':'Back to '+examName}</Link></Button>}>{q?'Try another search.':`Reviewed ${examName} tests will appear here when published.`}</Empty>}
   {data&&data.pages>1&&<nav className="chapter-pagination" aria-label="Test pages"><Button variant="outline" data-testid="catalog-prev" disabled={page<=1} onClick={()=>update({page:page-1})}>Previous</Button><span data-testid="catalog-page">Page {page} of {data.pages}</span><Button variant="outline" data-testid="catalog-next" disabled={page>=data.pages} onClick={()=>update({page:page+1})}>Next<ArrowRight size={16}/></Button></nav>}
  </>}
 </div>;
}
