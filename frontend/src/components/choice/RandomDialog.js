// The random mock: only the number of questions is asked. jeelive.ai draws them, equal over the subjects.
import React,{useRef,useState} from 'react';
import {Loader2,Sparkles} from 'lucide-react';
import {Dialog,DialogContent,DialogDescription,DialogHeader,DialogTitle} from '../ui/dialog';
import {MARKS,SHORT,makePaper,minutesFor,splitOf,timeLabel,uuid} from '../../lib/choice';
import {Makeup} from './ChoiceParts';

const QUICK=[15,30,45,60,75];

export function RandomDialog({open,onOpenChange,bank,onMade}){
 const subjects=bank.subjects.filter(s=>s.chapters.length).map(s=>s.name);
 const room=bank.subjects.filter(s=>s.chapters.length).map(s=>Math.min(s.chapters.reduce((n,c)=>n+c.count,0),bank.max_per_subject??Infinity));
 const most=subjects.length?Math.min(bank.max_questions,Math.min(...room)*subjects.length):0,least=Math.max(3,subjects.length);
 const [text,setText]=useState(String(Math.min(30,most))),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const asked=useRef({n:0,key:''});
 const n=/^\d{1,3}$/.test(text)?Number(text):0,good=n>=least&&n<=most,split=splitOf(good?n:0,subjects);
 async function make(e){
  e?.preventDefault();if(!good||busy)return;
  if(asked.current.n!==n)asked.current={n,key:uuid()};
  setBusy(true);setError('');
  try{onMade(await makePaper({mode:'random',count:n},asked.current.key));}catch(err){setError(err.message||'Mock ban nahi paaya. Dobara try karo.');setBusy(false);}
 }
 return <Dialog open={open} onOpenChange={v=>{if(!busy)onOpenChange(v);}}>
  <DialogContent className="ch-dialog" data-testid="choice-random-sheet">
   <DialogHeader><DialogTitle>Random mock</DialogTitle><DialogDescription>Bas ginti batao. Sawaal {subjects.map(s=>SHORT[s]).join(', ')} se barabar aur mile-jule aayenge, JEE Main ke paper ki tarah.</DialogDescription></DialogHeader>
   <form onSubmit={make} className="ch-form">
    <label htmlFor="choice-random-input" className="ch-label">Kitne sawaal? ({least} se {most})</label>
    <input id="choice-random-input" className="ch-count-input" inputMode="numeric" maxLength={3} value={text} disabled={busy} placeholder="30"
     onChange={e=>{setText(e.target.value.replace(/[^0-9]/g,'').slice(0,3));setError('');}} data-testid="choice-random-input"/>
    <div className="ch-quick">{QUICK.filter(q=>q<=most).map(q=><button type="button" key={q} className={'ch-chip'+(n===q?' is-on':'')} aria-pressed={n===q}
     onClick={()=>{setText(String(q));setError('');}} data-testid={'choice-random-quick-'+q}>{q}</button>)}</div>
    {good?<Makeup testId="choice-random-makeup" counts={split} bank={bank}/>:<p className="ch-bad" data-testid="choice-random-range">{least} se {most} ke beech ginti likho.</p>}
    {good&&<p className="ch-muted" data-testid="choice-random-rule">Poore {n*MARKS.correct} marks · sahi +{MARKS.correct}, galat {MARKS.wrong}, chhoda 0 · time {timeLabel(minutesFor(split,bank.minutes_per_question))}</p>}
    {error&&<p className="ch-error" role="alert" data-testid="choice-random-error">{error}</p>}
    <button type="submit" className="ch-btn ch-btn-lg" disabled={!good||busy} data-testid="choice-random-make">{busy?<Loader2 size={18} className="spin"/>:<Sparkles size={18}/>}Random mock banao</button>
   </form>
  </DialogContent>
 </Dialog>;
}
