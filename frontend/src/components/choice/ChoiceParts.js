// The small parts of Student Choice's screens: the red top card, subject tabs, a tick, a listed question (never its
// options), the bar at the bottom and the paper's make-up subject by subject.
import React,{memo,useState} from 'react';
import {Check} from 'lucide-react';
import {MathText} from '../QuestionContent';
import {SHORT,SUBJECTS,minutesFor,splitMinutes,timeLabel,totalOf} from '../../lib/choice';

export const subjectKey=s=>s.toLowerCase();

export function ChoiceHero({testId,kicker,children}){
 return <header className="ch-hero" data-testid={testId}><span className="ch-kicker">{kicker}</span>{children}</header>;
}

export function SubjectTabs({prefix,value,onChange,items}){
 return <div className="ch-subjects" role="tablist" aria-label="Subject">{items.map(i=>
  <button type="button" role="tab" key={i.subject} aria-selected={value===i.subject} className={'ch-subject is-'+subjectKey(i.subject)+(value===i.subject?' is-on':'')}
   onClick={()=>onChange(i.subject)} data-testid={`${prefix}-${subjectKey(i.subject)}`}>{SHORT[i.subject]}<b data-testid={`${prefix}-${subjectKey(i.subject)}-count`}>{i.count}</b></button>)}</div>;
}

export const Tick=({on,subject})=><span className={'ch-tick'+(on?' is-on':'')+(on&&subject?' is-'+subjectKey(subject):'')} aria-hidden="true">{on&&<Check size={15} strokeWidth={3}/>}</span>;

function StemPicture({p,testId}){
 const [failed,setFailed]=useState(false);
 if(failed)return <span className="ch-muted" data-testid={testId+'-failed'}>Is sawaal ki picture load nahi hui.</span>;
 const style=p.w&&p.h?{width:'100%',maxWidth:Math.round(p.w*1.25),aspectRatio:`${p.w} / ${p.h}`}:undefined;
 return <img src={p.url} alt="" loading="lazy" decoding="async" style={style} className="ch-stem-img" onError={()=>setFailed(true)} data-testid={testId}/>;
}

export const QuestionCard=memo(function QuestionCard({q,on,onToggle}){
 const id='choice-q-'+q.id;
 return <button type="button" role="checkbox" aria-checked={on} className={'ch-q'+(on?' is-on':'')} onClick={()=>onToggle(q)} data-testid={id}
  aria-label={`Sawaal ${q.number}${q.type==='integer'?', numerical':''}${on?', chuna hua':''}`}>
  <span className="ch-q-head"><Tick on={on}/><b data-testid={id+'-number'}>Q {q.number}</b><span className="ch-kind">{q.type==='integer'?'NUMERICAL':'MCQ'}</span></span>
  <span className="ch-q-stem">{q.text?<span className="ch-q-text" data-testid={id+'-text'}><MathText text={q.text}/></span>:null}
   {q.stem.map((p,i)=><StemPicture key={p.url} p={p} testId={`${id}-picture-${i}`}/>)}</span>
 </button>;
});

export function Makeup({counts,bank,testId}){
 const share=splitMinutes(counts,bank.minutes_per_question);
 return <div className="ch-makeup" data-testid={testId}>
  {SUBJECTS.filter(s=>counts[s]).map(s=><div key={s} className="ch-makeup-row" data-testid={`${testId}-${subjectKey(s)}`}>
   <i className={'ch-dot is-'+subjectKey(s)}/><span>{SHORT[s]}</span><b>{counts[s]} <small>sawaal</small></b><em data-testid={`${testId}-${subjectKey(s)}-time`}>{timeLabel(share[s])}</em></div>)}
  <div className="ch-makeup-row is-total"><span>Poora paper</span><b data-testid={testId+'-total'}>{totalOf(counts)} <small>sawaal</small></b><em data-testid={testId+'-time'}>{timeLabel(minutesFor(counts,bank.minutes_per_question))}</em></div>
 </div>;
}

export function StepBar({big,small,label,onGo,disabled,testId}){
 return <div className="ch-bar" data-testid={testId}><div><strong data-testid={testId+'-count'}>{big}</strong><small data-testid={testId+'-note'}>{small}</small></div>
  <button type="button" className="ch-btn" disabled={disabled} onClick={onGo} data-testid={testId+'-go'}>{label}</button></div>;
}
