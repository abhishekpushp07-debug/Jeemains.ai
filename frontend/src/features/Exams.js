import React from 'react';
import {Link,Navigate,useSearchParams} from 'react-router-dom';
import {ArrowUpRight,Clock3,FileCheck2} from 'lucide-react';
import {Badge} from '../components/Shared';
import {Button} from '../components/ui/button';
import {examByName} from '../lib/exams';

export const SetCard=({s})=>{
 const active=s.attempt?.status==='active',done=s.attempt?.status==='completed';
 return <article className="card set-card chapter-test-card" data-testid={'exams-set-card-'+s.id}>
  <div className="row-between"><Badge>{s.exam}</Badge><small data-testid={'exam-state-'+s.id}>{active?'In progress':done?'Completed':'Live'}</small></div>
  <h3 data-testid={'exam-title-'+s.id}>{s.title}</h3>
  <div className="set-facts" data-testid={'exam-facts-'+s.id}><span><FileCheck2 size={16}/>{s.count} questions</span><span><Clock3 size={16}/>{s.rules.minutes?s.rules.minutes+' min':'Untimed'}</span></div>
  <div className="chapter-card-marks" data-testid={'exam-marks-'+s.id}><strong>+{s.rules.correct}</strong> correct <span>·</span> <strong>{s.rules.wrong}</strong> wrong <span>·</span> {s.maximum} marks</div>
  <p data-testid={'exam-source-'+s.id}>{s.source}</p>
  <div className="chapter-card-actions"><Button asChild className="btn btn-primary"><Link to={active?'/attempts/'+s.attempt.id:'/sets/'+s.id} data-testid={(active?'exam-resume-':'exam-start-')+s.id}>{active?'Resume test':done?'Attempt again':'View rules & start'}<ArrowUpRight size={17}/></Link></Button>{done&&<Button asChild variant="outline"><Link to={'/results/'+s.attempt.id} data-testid={'exam-results-'+s.id}>View results</Link></Button>}</div>
 </article>;
};

export const SetRow=({s})=>{
 const active=s.attempt?.status==='active',done=s.attempt?.status==='completed';
 return <article className="exam-row" data-testid={'exams-set-card-'+s.id}>
  <div className="exam-row-number" data-testid={'exam-chapter-number-'+s.id}>{s.chapter_number?String(s.chapter_number).padStart(2,'0'):<FileCheck2 size={20}/>}</div>
  <div className="exam-row-main"><div className="exam-row-overline"><span data-testid={'exam-subject-'+s.id}>{s.chapter_subject||s.subjects.join(' · ')}</span><span className={active?'exam-state-active':''} data-testid={'exam-state-'+s.id}>{active?'In progress':done?'Completed':'Available'}</span></div><h3 data-testid={'exam-title-'+s.id}>{s.title}</h3><p data-testid={'exam-facts-'+s.id}>{s.count} questions <span>·</span> {s.rules.minutes?s.rules.minutes+' min':'Untimed'} <span>·</span> +{s.rules.correct} / {s.rules.wrong}</p></div>
  <div className="exam-row-validity" data-testid={'exam-expiry-'+s.id}><span>{s.end_at?'Available until':'Access'}</span><strong>{s.end_at?new Date(s.end_at*1000).toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'}):'Live practice'}</strong></div>
  <div className="exam-row-actions">{done&&<Button asChild variant="ghost"><Link to={'/results/'+s.attempt.id} data-testid={'exam-results-'+s.id}>Results</Link></Button>}<Button asChild className="btn btn-primary"><Link to={active?'/attempts/'+s.attempt.id:'/sets/'+s.id} data-testid={(active?'exam-resume-':'exam-start-')+s.id}>{active?'Resume':done?'Retry test':'Start test'}<ArrowUpRight size={16}/></Link></Button></div>
 </article>;
};

// Preserve old links without maintaining a second, confusing navigation system.
export default function Exams(){const [params]=useSearchParams();const exam=examByName(params.get('exam'));return <Navigate to={exam?'/exams/'+exam.slug:'/home'} replace/>}
