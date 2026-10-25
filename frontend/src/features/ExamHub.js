import React from 'react';
import {Link,useParams} from 'react-router-dom';
import {ClipboardList,Layers3,ChartNoAxesCombined} from 'lucide-react';
import {examBySlug} from '../lib/exams';
import {ExamBreadcrumbs,NavigationCard} from '../components/exams/ExamNavigation';
import {Empty} from '../components/Shared';
import {Button} from '../components/ui/button';
export default function ExamHub(){
 const {examSlug}=useParams();const exam=examBySlug(examSlug);
 if(!exam)return <div className="container page"><Empty title="Choose a supported exam." action={<Button asChild><Link to="/home" data-testid="unknown-exam-home">Back to Home</Link></Button>}>JEE Main, BITSAT and COMEDK are available from Home.</Empty></div>;
 const sections=[examSlug==='jee-main'?['pyq','PYQ Papers','Choose an exam date and shift. Start a full paper or revisit your results.',ClipboardList]:['mocks','Mock Tests','Live, full-length papers. Practice the complete test in one sitting.',ClipboardList],['chapters','Chapter-wise Tests','Choose a subject, pick a chapter and build understanding.',Layers3],['results','Results','Revisit previous attempts, your answers and available solutions.',ChartNoAxesCombined]];
 return <div className="container page exam-home" data-testid="exam-hub-page"><ExamBreadcrumbs exam={exam}/><header className="exam-simple-heading"><span className="eyebrow" data-testid="exam-hub-eyebrow">YOUR {exam.name.toUpperCase()} SPACE</span><h1 data-testid="exam-hub-title">What would you like to do?</h1><p data-testid="exam-hub-description">One clear path from practice to understanding.</p></header><div className="exam-choice-grid" data-testid="exam-hub-card-grid">{sections.map(([path,title,description,Icon],i)=><NavigationCard key={path} to={'/exams/'+examSlug+'/'+path} title={title} description={description} Icon={Icon} index={'0'+(i+1)} testId={'exam-hub-card-'+path}/>)}</div></div>;
}
