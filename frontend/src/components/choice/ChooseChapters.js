// Student Choice, step 1 of 2: the chapters. A subject at a time, or by name in all three subjects at once.
import React,{useMemo,useState} from 'react';
import {Search,X} from 'lucide-react';
import {SHORT,chosenChapters,hasChapter,pickedCount,pickedIn,toggleChapter} from '../../lib/choice';
import {findChapters,searchIndex} from '../../lib/choiceSearch';
import {StepBar,SubjectTabs,Tick,subjectKey} from './ChoiceParts';

function ChapterRow({c,subject,showSubject}){
 const on=hasChapter(c.id),picked=pickedIn(c.id);
 return <button type="button" role="checkbox" aria-checked={on} className={'ch-row'+(on?' is-on is-'+subjectKey(subject):'')} onClick={()=>toggleChapter(c.id)} data-testid={'choice-chapter-'+c.id}>
  <Tick on={on} subject={subject}/>
  <span className="ch-row-body"><strong data-testid={`choice-chapter-${c.id}-title`}>{c.number?`${c.number}. `:''}{c.title}</strong>
   <small>{showSubject&&<b className={'is-'+subjectKey(subject)} data-testid={`choice-chapter-${c.id}-subject`}>{SHORT[subject]} · </b>}{c.count} sawaal · {c.mcq} MCQ · {c.integer} numerical</small></span>
  {picked>0&&<span className="ch-picked" data-testid={`choice-chapter-${c.id}-picked`}>{picked} chune</span>}
 </button>;
}

export function ChooseChapters({bank,go}){
 const [subject,setSubject]=useState(''),[q,setQ]=useState('');
 const subjects=bank.subjects.filter(s=>s.chapters.length);
 const current=subjects.find(s=>s.name===subject)||subjects[0];
 const index=useMemo(()=>searchIndex(subjects),[subjects]);
 const found=q.trim()?findChapters(index,q):null;
 const rows=found?found.items:(current?current.chapters.map(c=>({c,subject:current.name})):[]);
 const live=new Set(subjects.flatMap(s=>s.chapters.map(c=>c.id)));
 const ticked=chosenChapters().filter(id=>live.has(id)).length,questions=pickedCount();
 const sum=subjects.flatMap(s=>s.chapters).filter(c=>hasChapter(c.id)).reduce((n,c)=>n+c.count,0);
 return <div className="ch-step" data-testid="choice-pick-screen">
  <div className="ch-step-head"><span className="ch-kicker dark">Student Choice · Step 1 of 2</span><h1 data-testid="choice-pick-title">Chapters chuno</h1></div>
  <label className="ch-search" data-testid="choice-search"><Search size={18} aria-hidden="true"/><input value={q} onChange={e=>setQ(e.target.value.slice(0,60))} placeholder="Chapter ka naam likho…" aria-label="Chapter ka naam likh kar dhoondo" data-testid="choice-search-input"/>
   {q&&<button type="button" onClick={()=>setQ('')} aria-label="Search hatao" data-testid="choice-search-clear"><X size={16}/></button>}</label>
  {found?(found.items.length?<p className="ch-muted" data-testid="choice-search-count">{found.close?'Is naam ka chapter nahi mila. Milte-julte naam:':`${found.items.length} chapter${found.items.length===1?'':'s'} mile · teeno subjects mein dhoonda`}</p>
   :<div className="ch-card ch-empty" data-testid="choice-search-none"><h2>Is naam ka chapter nahi mila</h2><p>Spelling dekh lo, ya subject se chapter chuno.</p><button type="button" className="ch-btn ghost" onClick={()=>setQ('')} data-testid="choice-search-reset">Search hatao</button></div>)
   :current&&<><SubjectTabs prefix="choice-subject" value={current.name} onChange={setSubject} items={subjects.map(s=>({subject:s.name,count:s.chapters.filter(c=>hasChapter(c.id)).length}))}/>
    <p className="ch-muted" data-testid="choice-pick-hint">Jitne chahiye utne chapter tick karo, kisi bhi subject se. {bank.pick?'Sawaal agle step mein chunoge.':'Agle step mein har chune chapter ka poora test milega.'}</p></>}
  <div className="ch-list" data-testid="choice-chapter-list">{rows.map(r=><ChapterRow key={r.c.id} c={r.c} subject={r.subject} showSubject={!!found}/>)}</div>
  <StepBar testId="choice-pick-bar" big={ticked?`${ticked} chapter${ticked===1?'':'s'} chune`:'Chapter chuno'}
   small={!ticked?'Kam se kam ek chapter tick karo':bank.pick?(questions?`${questions} sawaal chune hue hain`:'Ab inke sawaal chuno'):`${ticked} test${ticked===1?'':'s'} · ${sum} sawaal`}
   label={bank.pick?'Sawaal chuno':'Tests dekho'} disabled={!ticked} onGo={()=>go(bank.pick?'questions':'tests')}/>
 </div>;
}
