// Student Choice, the first screen: the open ways (choose questions, a random mock, or the chapters' own tests),
// and how the paper's time is reached. Both switches Off: the page says so and points at the chapter-wise tests.
import React from 'react';
import {Link} from 'react-router-dom';
import {ListChecks,Sparkles,ClipboardList,ChevronRight,Clock3} from 'lucide-react';
import {MARKS,SHORT,SUBJECTS,minutesFor,timeLabel} from '../../lib/choice';
import {ChoiceHero,subjectKey} from './ChoiceParts';

function Way({icon:Icon,title,body,note,onClick,to,testId}){
 const inner=<><span className="ch-way-icon"><Icon size={22}/></span><span className="ch-way-body"><strong>{title}</strong><span>{body}</span>{note&&<em data-testid={testId+'-note'}>{note}</em>}</span><ChevronRight size={20} className="ch-way-go" aria-hidden="true"/></>;
 return to?<Link to={to} className="ch-way" data-testid={testId}>{inner}</Link>:<button type="button" className="ch-way" onClick={onClick} data-testid={testId}>{inner}</button>;
}

function TimeCard({bank}){
 const per=bank.minutes_per_question;
 return <section className="ch-card" data-testid="choice-time"><h2 className="ch-h2"><Clock3 size={17}/>Time kaise milta hai</h2>
  {SUBJECTS.map(s=><div key={s} className="ch-time-row" data-testid={'choice-time-'+subjectKey(s)}><i className={'ch-dot is-'+subjectKey(s)}/><b>{SHORT[s]}</b><span>25 sawaal =</span><strong>{timeLabel(Math.ceil(25*per[s]))}</strong></div>)}
  <p className="ch-muted" data-testid="choice-time-note">Har sawaal apne subject ka time laata hai, isliye chhota paper chhota time paata hai. 25 + 25 + 25 sawaal = {timeLabel(minutesFor({Physics:25,Chemistry:25,Mathematics:25},per))}.</p>
 </section>;
}

export function ChoiceStart({bank,ticked,picked,onRandom}){
 const making=bank.pick||bank.random,all=bank.subjects.flatMap(s=>s.chapters);
 const left=Math.max(0,bank.daily_limit-bank.made_today);
 return <>
  <ChoiceHero testId="choice-hero" kicker="JEE MAIN · CHAPTER-WISE SAWAAL">
   <h1 data-testid="choice-title">{making?'Apna paper, apni marzi.':'Apne chapters, apni marzi.'}</h1>
   <p data-testid="choice-intro">{bank.pick?'JEE Main ke chapter-wise sawaalon mein se chapters aur sawaal khud chuno. Result, analysis aur solutions har paper ki tarah milte hain.':'JEE Main ke chapter-wise sawaal, aapke chune chapters ke hisaab se. Result, analysis aur solutions har paper ki tarah milte hain.'}</p>
   <div className="ch-facts" data-testid="choice-facts">{[`${bank.max_questions} sawaal tak`,`+${MARKS.correct} / −${Math.abs(MARKS.wrong)}`,'time subject ke hisaab se',`${all.length} chapters`].map(f=><span key={f}>{f}</span>)}</div>
   <p className="ch-today" data-testid="choice-today">Aaj {bank.made_today} / {bank.daily_limit} paper bane · {left?`${left} aur bana sakte ho`:'kal naya paper bana sakte ho'}</p>
  </ChoiceHero>
  {!all.length?<section className="ch-card ch-empty" data-testid="choice-not-ready"><h2>Chapters abhi nahi mile</h2><p>Student Choice ke sawaal JEE Main ke chapter-wise sawaal hi hain. Abhi koi chapter khula nahi mila. Thodi der mein dobara dekho, ya chapter-wise tests kholo.</p>
   <Link className="ch-btn" to="/exams/jee-main/chapters" data-testid="choice-open-chapters">Chapter-wise tests</Link></section>:<>
   <div className="ch-ways">
    {bank.pick?<Way testId="choice-way-pick" icon={ListChecks} title="Sawaal khud chuno" to="/choice?step=chapters" body="Subject, phir chapters, phir sawaal. Sirf sawaal dikhte hain, options paper mein milte hain." note={picked?`${picked} sawaal chune hue hain · jaari rakho`:undefined}/>
     :<Way testId="choice-way-chapters" icon={ListChecks} title="Chapters chuno" to="/choice?step=chapters" body="Physics, Chemistry aur Maths ke chapters tick karo. Har chune chapter ka poora test milega: ek-ek karke do." note={ticked?`${ticked} chapter${ticked===1?'':'s'} chune hue hain`:undefined}/>}
    {!bank.pick&&ticked>0&&<Way testId="choice-way-tests" icon={ClipboardList} title="Aapke chapter tests" to="/choice?step=tests" body={`Chune hue ${ticked} chapter${ticked===1?'':'s'} ke test: shuru karo, jaari rakho ya result dekho.`}/>}
    {bank.random&&<Way testId="choice-way-random" icon={Sparkles} title="Random mock" onClick={onRandom} body="Bas sawaalon ki ginti batao. Physics, Chemistry aur Maths mile-jule aayenge, JEE Main ki tarah."/>}
   </div>
   {(!bank.pick||!bank.random)&&<section className="ch-card ch-soon" data-testid="choice-soon"><span className="ch-soon-label">Jald aa raha hai</span>
    {!bank.pick&&<p data-testid="choice-soon-pick"><b>Sawaal khud chunna. </b>Chune chapters ke sawaal dekho (bina options), jo chahiye tick karo, aur un sab ka ek hi paper banao: {bank.max_questions} sawaal tak.</p>}
    {!bank.random&&<p data-testid="choice-soon-random"><b>Random mock. </b>Bas ginti batao; Physics, Chemistry aur Maths ke sawaal mile-jule aayenge, JEE Main ki tarah.</p>}
   </section>}
   <TimeCard bank={bank}/>
  </>}
 </>;
}
