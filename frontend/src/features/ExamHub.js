import React from 'react';
import {Link,useParams} from 'react-router-dom';
import {ClipboardList,Layers3,ChartNoAxesCombined,ListChecks} from 'lucide-react';
import {examBySlug} from '../lib/exams';
import {useExamStructure} from '../lib/catalog';
import {ExamBreadcrumbs,NavigationCard,OwnerHiddenNote} from '../components/exams/ExamNavigation';
import {Empty} from '../components/Shared';
import {Button} from '../components/ui/button';
import {Skeleton} from '../components/ui/skeleton';

const ICONS={pyq:ClipboardList,mocks:ClipboardList,chapters:Layers3};
const index=n=>String(n).padStart(2,'0');

export default function ExamHub(){
 const {examSlug}=useParams();const {data,error}=useExamStructure(examSlug);const exam=data||examBySlug(examSlug);
 if(error)return <div className="container page"><Empty title="Choose an available exam." action={<Button asChild><Link to="/home" data-testid="unknown-exam-home">Back to Home</Link></Button>}>This exam is not open yet. Pick another exam from Home.</Empty></div>;
 if(!exam)return <div className="container page exam-home" data-testid="exam-hub-loading"><Skeleton className="h-64"/></div>;
 const sections=data?.sections;
 return <div className="container page exam-home" data-testid="exam-hub-page"><ExamBreadcrumbs exam={exam}/>{data&&!data.shown&&<OwnerHiddenNote exam={data}/>}
  <header className="exam-simple-heading"><span className="eyebrow" data-testid="exam-hub-eyebrow">YOUR {exam.name.toUpperCase()} SPACE</span><h1 data-testid="exam-hub-title">What would you like to do?</h1><p data-testid="exam-hub-description">One clear path from practice to understanding.</p></header>
  {!sections?<div className="exam-choice-grid" data-testid="exam-hub-sections-loading">{[1,2,3].map(n=><Skeleton key={n} className="h-56"/>)}</div>:<div className="exam-choice-grid" data-testid="exam-hub-card-grid">
   {sections.map((s,i)=><NavigationCard key={s.id} to={`/exams/${examSlug}/${s.slug}`} title={s.name} description={s.description||`${s.live_count} live test${s.live_count===1?'':'s'}`} Icon={ICONS[s.kind]||ListChecks} index={index(i+1)} testId={'exam-hub-card-'+s.slug}/>)}
   <NavigationCard to={`/exams/${examSlug}/results`} title="Results" description="Revisit previous attempts, your answers and available solutions." Icon={ChartNoAxesCombined} index={index(sections.length+1)} testId="exam-hub-card-results"/>
  </div>}
  {sections&&!sections.length&&<p className="exam-hub-empty" data-testid="exam-hub-no-sections">Tests for {exam.name} will appear here as soon as they go live.</p>}
 </div>;
}
