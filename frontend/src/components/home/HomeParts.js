import React,{useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {Atom,GraduationCap,Landmark,CalendarCheck,BookMarked,ChevronRight,Clock3,Bookmark,BarChart3,Zap,CalendarDays,ArrowRight} from 'lucide-react';
import {api} from '../../lib/api';
import {useAuth} from '../../lib/auth';
import {useExamList} from '../../lib/catalog';
import {SERIES_PATH} from '../LiveSeriesBanner';
import {PLAY_STORE} from '../BottomTabs';
import {JEE_SERIES_DAYS,JEE_SERIES_DATES_SHORT,JEE_SERIES_START_SHORT} from '../../lib/exams';

const dayPart=h=>h<5?'good night':h<12?'good morning':h<17?'good afternoon':h<21?'good evening':'good night';

export const Greeting=()=>{
 const {user}=useAuth();const name=((user?.display_name||'').trim().split(' ')[0]||'learner').toLowerCase();
 return <header className="app-greeting"><h1 data-testid="home-greeting">{dayPart(new Date().getHours())}, {name}.</h1><p data-testid="home-greeting-sub">one focused step today.</p></header>;
};

export const SectionLabel=({title,to,testId})=><div className="section-label"><h2>{title}</h2>{to&&<Link to={to} data-testid={testId}>view all<ChevronRight size={17}/></Link>}</div>;

function useSeriesDone(){
 const {user}=useAuth();const [done,setDone]=useState(null);
 useEffect(()=>{if(!user)return;const c=new AbortController();api(SERIES_PATH+'/streak',{signal:c.signal}).then(d=>setDone(d.completed_count)).catch(()=>{});return()=>c.abort();},[user]);
 return done;
}

const R=40,RING=2*Math.PI*R;
const Ring=({done,total})=><div className="sf-ring" data-testid="series-feature-ring"><svg viewBox="0 0 96 96" aria-hidden="true"><circle cx="48" cy="48" r={R} className="track"/><circle cx="48" cy="48" r={R} className="bar" style={{strokeDasharray:RING,strokeDashoffset:RING*(1-Math.min(1,(done||0)/total))}}/></svg><div><strong>{done??0}</strong><small>of {total}</small></div></div>;

function seriesState(data){
 const t=data?.today_slot,ended=!!data&&data.today>data.last_date;
 const live=!!t?.ready&&['live','start_closed'].includes(t.state);
 const kicker=ended?'SERIES COMPLETE':live?`LIVE NOW · DAY ${t.day}`:t?`DAY ${t.day} · TODAY`:`STARTS ${JEE_SERIES_START_SHORT.toUpperCase()}`;
 if(t?.can_start&&t.set_id&&t.state!=='archive')return {kicker,live,to:'/sets/'+t.set_id,label:'Start today’s mock',Icon:ArrowRight};
 if(!t&&!ended)return {kicker,live,to:SERIES_PATH,label:'Opens '+JEE_SERIES_START_SHORT,Icon:CalendarDays};
 return {kicker,live,to:SERIES_PATH,label:ended?'Open practice archive':'Open series hub',Icon:ArrowRight};
}

export function SeriesFeatureCard({series}){
 const done=useSeriesDone();const s=seriesState(series.data);
 return <section className="feature-dark series-feature" data-testid="series-feature-card">
  <div className="sf-top"><span className="sf-chip"><i/>ALL INDIA SERIES</span><span className="sf-days">{JEE_SERIES_DAYS} DAYS</span></div>
  <div className="sf-main"><div><span className={'sf-kicker'+(s.live?' is-live':'')} data-testid="series-feature-status">{s.kicker}</span><h2 data-testid="series-feature-title">{JEE_SERIES_DAYS} daily full mocks</h2></div><Ring done={done} total={JEE_SERIES_DAYS}/></div>
  <div className="sf-stats" data-testid="series-feature-stats"><div><strong>75</strong><span>questions</span></div><div><strong>180</strong><span>minutes</span></div><div><strong>+4 / −1</strong><span>marking</span></div></div>
  <div className="sf-foot"><span>{JEE_SERIES_DATES_SHORT} · one mock a day</span><span className="sf-ai">100% AI</span></div>
  <Link className="sf-cta" to={s.to} state={s.to.startsWith('/sets/')?{returnTo:SERIES_PATH}:undefined} data-testid="series-feature-cta">{s.label}<s.Icon size={19}/></Link>
  {series.error&&<small className="sf-error" data-testid="series-feature-error">Live status unavailable. Open the series hub to retry.</small>}
 </section>;
}

const BUILT=[
 {slug:'jee-main',title:'JEE MAIN',sub:'pyq papers',to:'/exams/jee-main/pyq',Icon:Atom,chip:'PYQ'},
 {slug:'bitsat',title:'BITSAT',sub:'mock tests',to:'/exams/bitsat/mocks',Icon:GraduationCap},
 {slug:'comedk',title:'COMEDK',sub:'mock tests',to:'/exams/comedk/mocks',Icon:Landmark},
];
const PracticeCard=({c,i})=><Link to={c.to} className="practice-card" style={{animationDelay:i*60+'ms'}} data-testid={'exam-home-exam-card-'+c.slug}><span className="pc-icon"><c.Icon size={26} strokeWidth={1.6}/></span>{c.chip&&<span className="pc-chip">{c.chip}</span>}<span className="pc-title">{c.title}</span><span className="pc-sub">{c.sub}<ChevronRight size={17}/></span></Link>;

export function PracticeGrid({series}){
 const custom=(useExamList()||[]).filter(e=>!e.builtin).map(e=>({slug:e.slug,title:e.name.toUpperCase(),sub:e.shown===false?'hidden · owner view':'tests',to:'/exams/'+e.slug,Icon:BookMarked}));
 const s=seriesState(series.data);
 const india={slug:'all-india',title:'ALL INDIA',sub:s.live?'live today':series.data&&series.data.today>series.data.last_date?'practice archive':!series.data?.today_slot?'opens '+JEE_SERIES_START_SHORT.toLowerCase():'series hub',to:SERIES_PATH,Icon:CalendarCheck,chip:'LIVE'};
 return <div className="practice-grid" data-testid="exam-home-exam-card-grid">{[...BUILT,india,...custom].map((c,i)=><PracticeCard key={c.slug} c={c} i={i}/>)}</div>;
}

export function ForYou(){
 const {user}=useAuth();const [counts,setCounts]=useState(null);
 useEffect(()=>{if(!user)return;const c=new AbortController();api('/my/tests?'+new URLSearchParams({tab:'progress',page:'1'}),{signal:c.signal}).then(d=>setCounts(d.counts)).catch(()=>{});return()=>c.abort();},[user]);
 const items=[['progress','in progress',Clock3,counts?.progress?counts.progress+' OPEN':null],['saved','saved papers',Bookmark,counts?.saved?counts.saved+' SAVED':null],['completed','my results',BarChart3,counts?.completed?counts.completed+' DONE':null]];
 return <div className="for-you" data-testid="home-for-you">
  {items.map(([tab,label,Icon,badge])=><Link key={tab} to={'/profile?tab='+tab} className="fy-item" data-testid={'home-for-you-'+tab}><span className="fy-icon"><Icon size={26} strokeWidth={1.6}/>{badge&&<b data-testid={'home-for-you-badge-'+tab}>{badge}</b>}</span><span>{label}</span></Link>)}
  <a href={PLAY_STORE} target="_blank" rel="noopener noreferrer" className="fy-item" aria-label="Rapid Fire: JEELIVE.AI app on Google Play" data-testid="home-for-you-rapid-fire"><span className="fy-icon"><Zap size={26} strokeWidth={1.6}/><b>DUEL</b></span><span>rapid fire</span></a>
 </div>;
}
