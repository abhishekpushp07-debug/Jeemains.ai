// Student Choice (JEE Main): make your own paper from the live chapter-wise questions. ?step= chapters | questions | tests.
import React,{useCallback,useEffect,useState} from 'react';
import {Link,useNavigate,useSearchParams} from 'react-router-dom';
import {ArrowLeft,Loader2} from 'lucide-react';
import {useAuth} from '../lib/auth';
import {usePageTitle} from '../lib/pageMeta';
import {chosenChapters,dropGone,pickedCount,useChoiceHome,useChoiceStore} from '../lib/choice';
import {ChoiceStart} from '../components/choice/ChoiceStart';
import {ChooseChapters} from '../components/choice/ChooseChapters';
import {ChooseQuestions} from '../components/choice/ChooseQuestions';
import {ChapterTests} from '../components/choice/ChapterTests';
import {RandomDialog} from '../components/choice/RandomDialog';
import {ErrorBox} from '../components/Shared';
import '../choice.css';

const STEPS=['chapters','questions','tests'];

export default function StudentChoice(){
 const {user}=useAuth();const nav=useNavigate();const [params,setParams]=useSearchParams();
 usePageTitle('Student Choice');
 useChoiceStore(user?.id);
 const home=useChoiceHome(!!user);const bank=home.data;
 const [random,setRandom]=useState(false);
 const step=STEPS.includes(params.get('step'))?params.get('step'):'';
 const go=useCallback(s=>setParams(s?{step:s}:{}),[setParams]);
 useEffect(()=>{if(bank)dropGone(bank);},[bank]);
 useEffect(()=>{window.scrollTo({top:0});},[step]);
 const open=bank&&(bank.pick||bank.random);
 const safeStep=!open?'':step==='questions'&&!bank.pick?'tests':step==='tests'&&bank.pick?'questions':step;
 const live=new Set((bank?.subjects||[]).flatMap(s=>s.chapters.map(c=>c.id)));
 const ticked=chosenChapters().filter(id=>live.has(id)).length;
 return <div className="container page ch-page" data-testid="choice-page">
  <Link className="breadcrumb" to={safeStep?(safeStep==='chapters'?'/choice':'/choice?step=chapters'):'/home'} data-testid="choice-back"><ArrowLeft size={15}/>{safeStep?'Peeche':'Home'}</Link>
  <ErrorBox error={home.error} retry={home.reload}/>
  {!bank&&!home.error&&<p className="ch-muted" data-testid="choice-loading"><Loader2 size={15} className="spin"/>Load ho raha hai…</p>}
  {bank&&!open&&<section className="ch-card ch-empty" data-testid="choice-closed"><h1>Student Choice abhi band hai</h1><p>Tab tak JEE Main ke chapter-wise tests do: har chapter ka poora test.</p>
   <Link className="ch-btn" to="/exams/jee-main/chapters" data-testid="choice-closed-chapters">Chapter-wise tests</Link></section>}
  {open&&!safeStep&&<ChoiceStart bank={bank} ticked={ticked} picked={pickedCount()} onRandom={()=>setRandom(true)}/>}
  {open&&safeStep==='chapters'&&<ChooseChapters bank={bank} go={go}/>}
  {open&&safeStep==='questions'&&<ChooseQuestions bank={bank} go={go}/>}
  {open&&safeStep==='tests'&&<ChapterTests bank={bank} go={go}/>}
  {open&&bank.random&&random&&<RandomDialog open={random} onOpenChange={setRandom} bank={bank} onMade={id=>{setRandom(false);nav('/sets/'+id,{state:{returnTo:'/choice'}});}}/>}
 </div>;
}
