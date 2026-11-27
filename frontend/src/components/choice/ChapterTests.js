// Student Choice, step 2 while choosing questions is closed: the ticked chapters' whole tests, one after another.
import React from 'react';
import {Link} from 'react-router-dom';
import {SHORT,chosenChapters} from '../../lib/choice';
import {ChoiceHero,subjectKey} from './ChoiceParts';

const action=c=>c.attempt?.resumable?{label:'Resume',to:'/attempts/'+c.attempt.id}:c.attempt?.result_available?{label:'Result',to:'/results/'+c.attempt.id}:{label:'Start',to:'/sets/'+c.id};

export function ChapterTests({bank,go}){
 const ticked=new Set(chosenChapters());
 const mine=bank.subjects.flatMap(s=>s.chapters.filter(c=>ticked.has(c.id)).map(c=>({...c,subject:s.name})));
 const labels=mine.map(c=>action(c).label),done=labels.filter(l=>l==='Result').length,running=labels.filter(l=>l==='Resume').length;
 if(!mine.length)return <div className="ch-card ch-empty" data-testid="choice-tests-none"><p>Pehle chapters tick karo.</p><button type="button" className="ch-btn" onClick={()=>go('chapters')} data-testid="choice-tests-pick">Chapters chuno</button></div>;
 return <div className="ch-step" data-testid="choice-tests-screen">
  <ChoiceHero testId="choice-tests-hero" kicker="STUDENT CHOICE · AAPKE CHAPTER TESTS">
   <h1 data-testid="choice-tests-count">{mine.length} chapter test{mine.length===1?'':'s'} · {done} ho gaye</h1>
   <div className="ch-counts">{[['done','Ho gaye',done],['running','Chal rahe',running],['left','Baaki',mine.length-done-running]].map(([k,l,v])=><span key={k}><b data-testid={'choice-tests-'+k}>{v}</b>{l}</span>)}</div>
  </ChoiceHero>
  <p className="ch-muted" data-testid="choice-tests-hint">Har chapter ka poora test hai: jo chaho pehle do, ek-ek karke. Result, analysis aur solutions har paper ki tarah milte hain.</p>
  <div className="ch-list">{mine.map((c,i)=>{const a=action(c),id='choice-test-'+c.id;return <React.Fragment key={c.id}>
   {(i===0||mine[i-1].subject!==c.subject)&&<span className={'ch-subject-label is-'+subjectKey(c.subject)} data-testid={'choice-tests-subject-'+subjectKey(c.subject)}>{SHORT[c.subject].toUpperCase()}</span>}
   <Link to={a.to} state={{returnTo:'/choice?step=tests'}} className="ch-row" data-testid={id}><span className={'ch-num is-'+subjectKey(c.subject)}>{c.number??'•'}</span>
    <span className="ch-row-body"><strong data-testid={id+'-title'}>{c.title}</strong><small data-testid={id+'-facts'}>{c.count} Q · {c.test?.minutes?`${c.test.minutes} min`:'Untimed'} · +{c.test?.correct}/{c.test?.wrong}</small></span>
    <span className={'ch-action is-'+a.label.toLowerCase()} data-testid={id+'-action'}>{a.label}</span></Link></React.Fragment>;})}</div>
  <button type="button" className="ch-btn ghost" onClick={()=>go('chapters')} data-testid="choice-tests-change">Chapters badlo</button>
 </div>;
}
