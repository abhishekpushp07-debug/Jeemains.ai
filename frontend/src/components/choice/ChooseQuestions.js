// Student Choice, step 2 of 2: the questions of the ticked chapters, listed WITHOUT options (they come in the paper).
// A tap ticks one; "Paper banao" asks jeelive.ai to make the paper, and its page opens.
import React,{useCallback,useEffect,useRef,useState} from 'react';
import {useNavigate} from 'react-router-dom';
import {Loader2,Check} from 'lucide-react';
import {api} from '../../lib/api';
import {Dialog,DialogContent,DialogDescription,DialogHeader,DialogTitle} from '../ui/dialog';
import {MARKS,SHORT,chosenChapters,clearChoice,counts,hasQuestion,makePaper,minutesFor,orderedIds,pickedCount,pickedIn,timeLabel,toggleQuestion,totalOf,uuid} from '../../lib/choice';
import {Makeup,QuestionCard,StepBar,SubjectTabs} from './ChoiceParts';

const pages=new Map(); // a chapter's questions while this tab is open (their picture links live a day or more)

async function chapterQuestions(id){
 if(pages.has(id))return pages.get(id);
 const first=await api(`/choice/chapters/${id}/questions?page=1`);let items=first.items;
 for(let p=2;p<=first.pages;p++)items=items.concat((await api(`/choice/chapters/${id}/questions?page=${p}`)).items);
 const d={id,items};pages.set(id,d);return d;
}

function useChapter(id){
 const [d,setD]=useState(null),[error,setError]=useState(''),[tick,setTick]=useState(0);
 useEffect(()=>{if(!id)return undefined;let live=true;setD(pages.get(id)||null);setError('');
  chapterQuestions(id).then(x=>{if(live)setD(x);}).catch(e=>{if(live)setError(e.message);});return()=>{live=false;};},[id,tick]);
 return {d:d?.id===id?d:null,error,reload:()=>{pages.delete(id);setTick(v=>v+1);}};
}

function Review({open,setOpen,bank,onMade}){
 const [busy,setBusy]=useState(false),[error,setError]=useState('');const asked=useRef({ids:'',key:''});
 const made=counts();
 async function make(){
  const ids=orderedIds(bank),joined=ids.join(',');if(!ids.length||busy)return;
  if(asked.current.ids!==joined)asked.current={ids:joined,key:uuid()};
  setBusy(true);setError('');
  try{onMade(await makePaper({mode:'pick',question_ids:ids},asked.current.key));}
  catch(e){setError(e.message||'Paper ban nahi paaya. Dobara try karo.');setBusy(false);}
 }
 return <Dialog open={open} onOpenChange={v=>{if(!busy)setOpen(v);}}><DialogContent className="ch-dialog" data-testid="choice-review-sheet">
  <DialogHeader><DialogTitle>Aapka paper</DialogTitle><DialogDescription>Paper Physics, Chemistry, Maths ke order mein banega.</DialogDescription></DialogHeader>
  <Makeup testId="choice-review-makeup" counts={made} bank={bank}/>
  <p className="ch-muted" data-testid="choice-review-rule">Poore {totalOf(made)*MARKS.correct} marks. Sahi jawab +{MARKS.correct}, galat {MARKS.wrong}, chhoda hua 0. Result, analysis aur solutions har paper ki tarah milenge.</p>
  {error&&<p className="ch-error" role="alert" data-testid="choice-review-error">{error}</p>}
  <button type="button" className="ch-btn ch-btn-lg" disabled={busy} onClick={make} data-testid="choice-make">{busy?<Loader2 size={18} className="spin"/>:<Check size={18}/>}Haan, paper banao</button>
  <button type="button" className="ch-btn ghost" disabled={busy} onClick={()=>setOpen(false)} data-testid="choice-review-back">Aur sawaal chuno</button>
 </DialogContent></Dialog>;
}

export function ChooseQuestions({bank,go}){
 const nav=useNavigate();const leaving=useRef(false);
 const ticked=new Set(chosenChapters());
 const mine=bank.subjects.flatMap(s=>s.chapters.filter(c=>ticked.has(c.id)).map(c=>({...c,subject:s.name})));
 const subjects=[...new Set(mine.map(c=>c.subject))];
 const [subject,setSubject]=useState(''),[chapterId,setChapterId]=useState(''),[full,setFull]=useState(''),[review,setReview]=useState(false);
 const inSubject=mine.filter(c=>c.subject===(subjects.includes(subject)?subject:subjects[0]));
 const chapter=inSubject.find(c=>c.id===chapterId)||inSubject[0];
 const list=useChapter(chapter?.id);
 useEffect(()=>{if(!full)return undefined;const t=setTimeout(()=>setFull(''),3200);return()=>clearTimeout(t);},[full]);
 useEffect(()=>{window.scrollTo({top:0});},[chapter?.id]);
 const toggle=useCallback(q=>{
  const said=toggleQuestion(q.id,{chapter:chapter.id,subject:chapter.subject,n:q.number},bank);
  setFull(said==='full'?`${bank.max_questions} sawaal ho gaye: ek paper mein isse zyada nahi. Koi hatao, tab naya chuno.`:said==='subject'?`${SHORT[chapter.subject]} ke ${bank.max_per_subject} sawaal ho gaye. Koi hatao, tab naya chuno.`:'');
 },[bank,chapter]);
 useEffect(()=>{if(!mine.length&&!leaving.current)go('chapters');},[mine.length,go]);
 if(!chapter)return null;
 const n=pickedCount(),made=counts(),next=mine[mine.findIndex(c=>c.id===chapter.id)+1];
 return <div className="ch-step" data-testid="choice-questions-screen">
  <div className="ch-step-head"><span className="ch-kicker dark">Student Choice · Step 2 of 2</span><h1>Sawaal chuno</h1></div>
  {subjects.length>1&&<SubjectTabs prefix="choice-q-subject" value={chapter.subject} onChange={s=>{setSubject(s);setChapterId('');}} items={subjects.map(s=>({subject:s,count:made[s]}))}/>}
  {inSubject.length>1&&<div className="ch-pills" data-testid="choice-q-chapters">{inSubject.map(c=><button type="button" key={c.id} className={'ch-chip'+(c.id===chapter.id?' is-on':'')} onClick={()=>setChapterId(c.id)} data-testid={'choice-q-chapter-'+c.id}>{c.title}{pickedIn(c.id)>0&&<b>{pickedIn(c.id)}</b>}</button>)}</div>}
  <div><h2 className="ch-chapter" data-testid="choice-questions-chapter">{chapter.title}</h2>
   <p className="ch-muted" data-testid="choice-questions-hint">{SHORT[chapter.subject]} · {list.d?list.d.items.length:chapter.count} sawaal · yahan sirf sawaal hain, options paper mein milenge</p></div>
  {list.error&&<div className="ch-error-box" role="alert" data-testid="choice-questions-error">{list.error}<button type="button" className="ch-btn ghost" onClick={list.reload} data-testid="choice-questions-retry">Dobara try karo</button></div>}
  {!list.d&&!list.error&&<p className="ch-muted" data-testid="choice-questions-loading"><Loader2 size={15} className="spin"/>Sawaal load ho rahe hain…</p>}
  {list.d&&!list.d.items.length&&<p className="ch-card ch-empty" data-testid="choice-questions-empty">Is chapter mein sawaal nahi mile. Doosra chapter chuno.</p>}
  <div className="ch-list" data-testid="choice-question-list">{list.d?.items.map(q=><QuestionCard key={q.id} q={q} on={hasQuestion(q.id)} onToggle={toggle}/>)}</div>
  {list.d?.items.length>0&&next&&<button type="button" className="ch-btn ghost ch-next" onClick={()=>{setSubject(next.subject);setChapterId(next.id);}} data-testid="choice-next-chapter">Agla chapter: {next.title}</button>}
  {full&&<p className="ch-full" role="status" data-testid="choice-full">{full}</p>}
  <StepBar testId="choice-questions-bar" big={`${n} / ${bank.max_questions} sawaal`} small={n?`${timeLabel(minutesFor(made,bank.minutes_per_question))} · ${n*MARKS.correct} marks`:'Sawaal par tap karke chuno'} label="Paper banao" disabled={!n} onGo={()=>setReview(true)}/>
  <Review open={review} setOpen={setReview} bank={bank} onMade={id=>{leaving.current=true;nav('/sets/'+id,{state:{returnTo:'/choice'}});clearChoice();}}/>
 </div>;
}
