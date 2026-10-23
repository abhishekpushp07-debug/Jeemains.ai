import React,{useEffect,useState} from 'react';
import {Link,useParams,useSearchParams,useLocation} from 'react-router-dom';
import {ArrowUpRight,Clock3} from 'lucide-react';
import {api} from '../lib/api';
import {examBySlug} from '../lib/exams';
import {ExamBreadcrumbs,ExamDestinations} from '../components/exams/ExamNavigation';
import {Empty,ErrorBox,Badge} from '../components/Shared';
import {Button} from '../components/ui/button';
import {Tabs,TabsList,TabsTrigger} from '../components/ui/tabs';
import {Select,SelectContent,SelectItem,SelectTrigger,SelectValue} from '../components/ui/select';
import {Skeleton} from '../components/ui/skeleton';
import {Card} from '../components/ui/card';

export default function ExamHistory(){
 const location=useLocation();
 const {examSlug}=useParams(),exam=examBySlug(examSlug);const [params,setParams]=useSearchParams();
 const kind=['mock','chapter','practice'].includes(params.get('kind'))?params.get('kind'):'all',days=['7','30','90'].includes(params.get('days'))?params.get('days'):'all',page=Math.max(1,Math.min(10000,Number(params.get('page'))||1));
 const [data,setData]=useState(null),[error,setError]=useState(''),[reload,setReload]=useState(0);
 useEffect(()=>{
  if(!exam)return;const controller=new AbortController();setData(null);setError('');
  api(`/exam-navigation/${examSlug}/history?${new URLSearchParams({kind,days,page})}`,{signal:controller.signal}).then(d=>{if(!controller.signal.aborted)setData(d)}).catch(e=>{if(!controller.signal.aborted)setError(e.message)});
  return()=>controller.abort();
 },[exam,examSlug,kind,days,page,reload]);
 function update(values){const next=new URLSearchParams(params);Object.entries(values).forEach(([k,v])=>v?next.set(k,String(v)):next.delete(k));setParams(next)}
 if(!exam)return <div className="container page"><Empty title="Exam not found." action={<Button asChild><Link to="/home" data-testid="history-invalid-home">Back to Home</Link></Button>}/></div>;
 return <div className="container page exam-history" data-testid="exam-results-page"><ExamBreadcrumbs exam={exam} section={{label:'Results'}}/><header className="exam-simple-heading"><span className="eyebrow" data-testid="exam-results-exam">{exam.name}</span><h1 data-testid="exam-results-title">Your attempts. Your progress.</h1><p data-testid="exam-results-description">Resume a test or revisit your score, question-by-question review and available solutions.</p></header>
  <ExamDestinations exam={exam}/>
  <div className="history-filterbar"><Tabs value={kind} onValueChange={v=>update({kind:v==='all'?null:v,page:null})} data-testid="results-attempt-type-tabs"><TabsList>{[['all','All attempts'],['mock','Mock tests'],['chapter','Chapter-wise']].map(([v,label])=><TabsTrigger value={v} key={v} data-testid={'results-history-filter-'+v}>{label}</TabsTrigger>)}</TabsList></Tabs><Select value={days} onValueChange={v=>update({days:v==='all'?null:v,page:null})}><SelectTrigger className="history-date-filter" aria-label="Attempt date range" data-testid="results-history-date-filter"><SelectValue/></SelectTrigger><SelectContent>{[['all','All time'],['7','Last 7 days'],['30','Last 30 days'],['90','Last 90 days']].map(([v,label])=><SelectItem key={v} value={v} data-testid={'results-history-days-'+v}>{label}</SelectItem>)}</SelectContent></Select></div>
  <ErrorBox error={error} retry={()=>setReload(v=>v+1)}/>
  {!data&&!error&&<div className="exam-library-list" data-testid="results-history-loading">{[1,2,3].map(n=><Skeleton className="h-28" key={n}/>)}</div>}
  {data?.items.length>0&&<><p className="history-count" aria-live="polite" data-testid="results-history-count">{data.total} attempt{data.total===1?'':'s'}</p><div className="exam-library-list" data-testid="results-attempt-list">{data.items.map(a=>{const active=a.status==='active',embargo=a.competition_end>a.server_now;return <Card className="exam-history-row" key={a.id} data-testid={'results-attempt-row-'+a.id}><div className="exam-history-main"><div className="exam-history-meta" data-testid={'history-meta-'+a.id}><Badge>{a.test_kind==='chapter'?'Chapter-wise':a.test_kind==='mock'?'Mock test':'Other practice'}</Badge><span>{active?'In progress':a.mode==='retry'?'Revision attempt':'Completed'}</span></div><h2 data-testid={'history-title-'+a.id}>{a.title}</h2><p data-testid={'history-facts-'+a.id}>{new Date(a.started_at*1000).toLocaleString('en-IN',{day:'numeric',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'})} · {a.count} questions</p></div><div className="exam-history-score" data-testid={'history-score-'+a.id}>{active?<span><Clock3 size={16}/>In progress</span>:embargo?<span>Awaiting release</span>:a.summary?<><strong>{a.summary.score}<small> / {a.summary.maximum}</small></strong><span>Marks</span></>:<span>Open to prepare results</span>}</div><Button asChild variant={active?'default':'outline'}><Link state={{returnTo:location.pathname+location.search}} to={(active?'/attempts/':'/results/')+a.id} data-testid={(active?'history-resume-':'history-result-')+a.id}>{active?'Resume test':'View analysis'}<ArrowUpRight size={17}/></Link></Button></Card>})}</div></>}
  {data&&!data.items.length&&<Empty title="No attempts here yet." action={<Button asChild><Link to={'/exams/'+examSlug} data-testid="results-history-start">Explore {exam.name}<ArrowUpRight size={17}/></Link></Button>}>Your {kind==='mock'?'mock':kind==='chapter'?'chapter-wise':exam.name} attempts will appear here. Your other exam histories stay in their own Results section.</Empty>}
  {data&&data.pages>1&&<nav className="chapter-pagination" aria-label="Attempt pages"><Button variant="outline" disabled={page<=1} onClick={()=>update({page:page-1})} data-testid="history-prev">Previous</Button><span data-testid="history-page">Page {page} of {data.pages}</span><Button variant="outline" disabled={page>=data.pages} onClick={()=>update({page:page+1})} data-testid="history-next">Next</Button></nav>}
 </div>;
}
